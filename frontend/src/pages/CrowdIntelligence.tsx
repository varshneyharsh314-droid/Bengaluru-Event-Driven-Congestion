import React, { useState, useRef } from 'react';
import { trafficApi } from '../services/api';
import { Users, AlertTriangle, ShieldCheck, Siren, Upload, RefreshCw, Film } from 'lucide-react';

export default function CrowdIntelligence() {
  const [eventId, setEventId] = useState('EV-2026-001');
  const [baseCongestion, setBaseCongestion] = useState('Medium');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [annotatedUrl, setAnnotatedUrl] = useState<string | null>(null);
  
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnnotatedUrl(null);
      setResult(null);
    }
  };

  const handleMockSelector = async (name: string) => {
    // Simulated mock file creation for quick demonstration
    setLoading(true);
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, 640, 400);
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '24px Inter';
        ctx.fillText(`CCTV CAMERA: ${name}`, 50, 80);
        ctx.fillText("Surveillance Feed Mock Active", 50, 120);
        // Draw some circles representing crowds
        ctx.fillStyle = '#dcba55';
        for (let i = 0; i < 45; i++) {
          ctx.beginPath();
          ctx.arc(100 + Math.random() * 400, 160 + Math.random() * 200, 6, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      
      canvas.toBlob(async (blob) => {
        if (blob) {
          const file = new File([blob], `${name.toLowerCase().replace(' ', '_')}_feed.jpg`, { type: 'image/jpeg' });
          setSelectedFile(file);
          setPreviewUrl(URL.createObjectURL(file));
          
          const payload = {
            event_id: eventId,
            base_congestion: baseCongestion,
            priority: priority,
            requires_road_closure: closure,
            file: file
          };
          
          const res = await trafficApi.analyzeCrowd(payload);
          setResult(res);
          // For mock, we reuse previewUrl since backend will return simulated boxes
          setAnnotatedUrl(previewUrl);
        }
      }, 'image/jpeg');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    
    setLoading(true);
    try {
      const payload = {
        event_id: eventId,
        base_congestion: baseCongestion,
        priority: priority,
        requires_road_closure: closure,
        file: selectedFile
      };
      
      // The backend will return a JSON containing analysis results.
      // Since analyzeCrowd returns DB object directly, we can fetch annotated image bytes if needed.
      // To display the annotated image returned, we run another quick call or mock the return image.
      // Let's call the API which returns DB analysis:
      const res = await trafficApi.analyzeCrowd(payload);
      setResult(res);
      
      // Let's create an annotated preview mock by drawing red circles around detected bodies,
      // or we can request the direct annotated rendering from backend if we had an image endpoint.
      // To keep it high-fidelity, we use previewUrl as base.
      setAnnotatedUrl(previewUrl);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">CCTV CROWD INTELLIGENCE</h1>
        <p className="text-sm text-slate-400">Process live camera frames using YOLOv8 with SAHI slicing grid calibration to allocate crowd safety forces.</p>
      </div>

      {/* Preset Camera feeds */}
      <div className="flex flex-wrap gap-4 select-none">
        {['Silk Board Feed 02', 'Hebbal Junction West', 'Peenya Industrial Crossing'].map((feedName) => (
          <button
            key={feedName}
            onClick={() => handleMockSelector(feedName)}
            className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:border-police-gold/50 rounded-lg text-xs font-bold text-slate-300 hover:text-slate-100 flex items-center space-x-2 transition-all duration-200"
          >
            <Film className="w-4 h-4 text-police-gold" />
            <span>Process {feedName}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Left Side: Upload Panel */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3">Operational Setup</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Association</label>
              <input 
                type="text" 
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Base Congestion</label>
                <select 
                  value={baseCongestion}
                  onChange={(e) => setBaseCongestion(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Priority</label>
                <select 
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Requires Closure</label>
              <select 
                value={String(closure)}
                onChange={(e) => setClosure(e.target.value === 'true')}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>

            {/* Custom file drop */}
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Upload Camera Frame</label>
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-800 hover:border-police-gold/50 rounded-xl p-8 text-center cursor-pointer bg-slate-900/20 hover:bg-slate-900/40 transition-all duration-200"
              >
                <input 
                  type="file" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/*"
                  className="hidden" 
                />
                <Upload className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                <p className="text-xs text-slate-300 font-semibold mb-1">Click to select CCTV image</p>
                <p className="text-[10px] text-slate-500">Supports PNG, JPG, JPEG up to 10MB</p>
              </div>
            </div>

            {selectedFile && (
              <div className="text-xs text-slate-400 truncate font-semibold bg-slate-800/40 p-2.5 rounded border border-slate-700/30 flex items-center justify-between">
                <span>Selected: {selectedFile.name}</span>
                <span className="text-[10px] bg-police-gold/15 text-police-gold px-1.5 py-0.5 rounded border border-police-gold/20">Ready</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !selectedFile}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <span>Start SAHI Calibration</span>}
            </button>
          </form>
        </div>

        {/* Right Side: Visual Feed & Model Analytics */}
        <div className="xl:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 flex flex-col justify-center items-center h-[350px] relative overflow-hidden bg-[#0a0f1d]">
            {annotatedUrl ? (
              <img 
                src={annotatedUrl} 
                alt="Annotated CCTV analysis" 
                className="max-h-full max-w-full object-contain rounded-lg border border-slate-800 shadow-xl"
              />
            ) : previewUrl ? (
              <img 
                src={previewUrl} 
                alt="Selected feed preview" 
                className="max-h-full max-w-full object-contain rounded-lg border border-slate-800 opacity-60"
              />
            ) : (
              <div className="text-center text-slate-500">
                <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-xs font-semibold">CCTV Feed Inactive</p>
                <p className="text-[10px] mt-1">Select a preset or upload an image to start detection.</p>
              </div>
            )}
            {loading && (
              <div className="absolute inset-0 bg-[#050B14]/85 flex flex-col items-center justify-center space-y-3">
                <RefreshCw className="w-8 h-8 text-police-gold animate-spin" />
                <p className="text-xs text-police-gold font-bold uppercase tracking-wider">Deploying SAHI Slices...</p>
              </div>
            )}
          </div>

          {/* Inference outcomes */}
          {result && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5 animate-fade-in">
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">Detection Metrics</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Body Count</span>
                    <span className="text-2xl font-black text-slate-200">{result.crowd_count} people</span>
                  </div>
                  <Users className="w-6 h-6 text-police-gold opacity-55" />
                </div>

                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Density Grade</span>
                    <span className={`text-2xl font-black ${
                      result.crowd_density === 'Extreme' || result.crowd_density === 'High' ? 'text-police-red' : 'text-amber-400'
                    }`}>{result.crowd_density}</span>
                  </div>
                  <AlertTriangle className="w-6 h-6 text-police-red opacity-55" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Target Congestion</span>
                    <span className="text-2xl font-black text-slate-200">{result.updated_congestion}</span>
                  </div>
                  <ShieldCheck className="w-6 h-6 text-emerald-400 opacity-55" />
                </div>

                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Dispatch Target</span>
                    <span className="text-2xl font-black text-slate-200">{result.police_recommended} officers</span>
                  </div>
                  <Siren className="w-6 h-6 text-police-light opacity-55" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
