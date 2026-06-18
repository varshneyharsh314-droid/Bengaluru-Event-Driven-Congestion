import React, { useState, useRef, useEffect, useCallback } from 'react';
import { trafficApi, connectVideoWs } from '../services/api';
import { Users, AlertTriangle, ShieldCheck, Siren, Upload, RefreshCw, Film, Video, Image, BarChart3, TrendingUp, Activity } from 'lucide-react';

type AnalysisMode = 'image' | 'video';

interface VideoStreamState {
  isStreaming: boolean;
  currentFrame: string | null;
  headcount: number;
  density: string;
  frameIdx: number;
  totalFrames: number;
  fps: number;
  frameCounts: number[];
  peakCount: number;
  summary: any | null;
}

function SparklineChart({ data, width = 400, height = 80 }: { data: number[], width?: number, height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    const maxVal = Math.max(...data, 1);
    const step = width / (data.length - 1);
    const pad = 4;

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(239, 68, 68, 0.35)');
    gradient.addColorStop(1, 'rgba(239, 68, 68, 0.02)');

    ctx.beginPath();
    ctx.moveTo(0, height);
    data.forEach((val, i) => {
      const x = i * step;
      const y = height - pad - ((val / maxVal) * (height - pad * 2));
      if (i === 0) ctx.lineTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo((data.length - 1) * step, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((val, i) => {
      const x = i * step;
      const y = height - pad - ((val / maxVal) * (height - pad * 2));
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Latest point dot
    if (data.length > 0) {
      const lastX = (data.length - 1) * step;
      const lastY = height - pad - ((data[data.length - 1] / maxVal) * (height - pad * 2));
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }, [data, width, height]);

  return <canvas ref={canvasRef} style={{ width, height }} className="rounded" />;
}

export default function CrowdIntelligence() {
  const [mode, setMode] = useState<AnalysisMode>('image');
  const [eventId, setEventId] = useState('EV-2026-001');
  const [baseCongestion, setBaseCongestion] = useState('Medium');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);
  
  // Image mode state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [annotatedUrl, setAnnotatedUrl] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Video mode state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [videoStream, setVideoStream] = useState<VideoStreamState>({
    isStreaming: false,
    currentFrame: null,
    headcount: 0,
    density: 'Low',
    frameIdx: 0,
    totalFrames: 0,
    fps: 0,
    frameCounts: [],
    peakCount: 0,
    summary: null,
  });

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // === IMAGE MODE HANDLERS ===
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
          if (res.annotated_image_base64) {
            setAnnotatedUrl(`data:image/jpeg;base64,${res.annotated_image_base64}`);
          } else {
            setAnnotatedUrl(previewUrl);
          }
        }
      }, 'image/jpeg');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleImageSubmit = async (e: React.FormEvent) => {
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
      
      const res = await trafficApi.analyzeCrowd(payload);
      setResult(res);
      
      if (res.annotated_image_base64) {
        setAnnotatedUrl(`data:image/jpeg;base64,${res.annotated_image_base64}`);
      } else {
        setAnnotatedUrl(previewUrl);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // === VIDEO MODE HANDLERS ===
  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideoFile(file);
      setVideoPreviewUrl(URL.createObjectURL(file));
      setVideoStream(prev => ({ ...prev, summary: null, currentFrame: null, frameCounts: [], peakCount: 0 }));
    }
  };

  const handleVideoAnalysis = useCallback(async () => {
    if (!videoFile) return;

    setLoading(true);
    setVideoStream({
      isStreaming: true,
      currentFrame: null,
      headcount: 0,
      density: 'Low',
      frameIdx: 0,
      totalFrames: 0,
      fps: 0,
      frameCounts: [],
      peakCount: 0,
      summary: null,
    });

    const socket = connectVideoWs(
      (data) => {
        if (data.event === 'VIDEO_FRAME') {
          setVideoStream(prev => {
            const newCounts = [...prev.frameCounts, data.headcount];
            // Keep last 200 for sparkline performance
            const trimmedCounts = newCounts.length > 200 ? newCounts.slice(-200) : newCounts;
            return {
              ...prev,
              headcount: data.headcount,
              density: data.density,
              frameIdx: data.frame_idx,
              totalFrames: data.total_frames,
              fps: data.fps,
              frameCounts: trimmedCounts,
              peakCount: Math.max(prev.peakCount, data.headcount),
              currentFrame: data.annotated_frame_base64
                ? `data:image/jpeg;base64,${data.annotated_frame_base64}`
                : prev.currentFrame,
            };
          });
        } else if (data.event === 'VIDEO_COMPLETE') {
          setVideoStream(prev => ({
            ...prev,
            isStreaming: false,
            summary: data.summary || null,
          }));
          setLoading(false);
        } else if (data.event === 'ERROR') {
          console.error('Video analysis error:', data.message);
          setVideoStream(prev => ({ ...prev, isStreaming: false }));
          setLoading(false);
        }
      },
      () => {
        setVideoStream(prev => ({ ...prev, isStreaming: false }));
        setLoading(false);
      },
      () => {
        setVideoStream(prev => ({ ...prev, isStreaming: false }));
        setLoading(false);
      }
    );

    wsRef.current = socket;

    // Wait for connection, then send video binary
    socket.onopen = async () => {
      const buffer = await videoFile.arrayBuffer();
      socket.send(buffer);
    };
  }, [videoFile]);

  const progressPct = videoStream.totalFrames > 0
    ? Math.round((videoStream.frameIdx / videoStream.totalFrames) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">CCTV CROWD INTELLIGENCE</h1>
        <p className="text-sm text-slate-400">Process live camera frames or video files using YOLOv8 with SAHI slicing grid calibration for real-time headcount analysis.</p>
      </div>

      {/* Mode Tabs */}
      <div className="flex space-x-2 select-none">
        <button
          onClick={() => setMode('image')}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
            mode === 'image'
              ? 'bg-police-gold text-[#0B132B] border-police-gold shadow-md shadow-police-gold/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Image className="w-4 h-4" />
          <span>Image Analysis</span>
        </button>
        <button
          onClick={() => setMode('video')}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
            mode === 'video'
              ? 'bg-police-gold text-[#0B132B] border-police-gold shadow-md shadow-police-gold/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Video className="w-4 h-4" />
          <span>Video Analysis</span>
        </button>
      </div>

      {/* Preset Camera feeds — Image mode only */}
      {mode === 'image' && (
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
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Left Side: Operational Setup Panel */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3">Operational Setup</h3>
          
          <form onSubmit={mode === 'image' ? handleImageSubmit : (e) => { e.preventDefault(); handleVideoAnalysis(); }} className="space-y-4">
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

            {/* File Upload Area */}
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">
                {mode === 'image' ? 'Upload Camera Frame' : 'Upload CCTV Video'}
              </label>
              <div 
                onClick={() => mode === 'image' ? fileInputRef.current?.click() : videoInputRef.current?.click()}
                className="border-2 border-dashed border-slate-800 hover:border-police-gold/50 rounded-xl p-8 text-center cursor-pointer bg-slate-900/20 hover:bg-slate-900/40 transition-all duration-200"
              >
                {mode === 'image' ? (
                  <>
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
                  </>
                ) : (
                  <>
                    <input 
                      type="file" 
                      ref={videoInputRef}
                      onChange={handleVideoChange}
                      accept="video/*"
                      className="hidden" 
                    />
                    <Video className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                    <p className="text-xs text-slate-300 font-semibold mb-1">Click to select CCTV video</p>
                    <p className="text-[10px] text-slate-500">Supports MP4, AVI, MOV up to 100MB</p>
                  </>
                )}
              </div>
            </div>

            {/* Selected file info */}
            {mode === 'image' && selectedFile && (
              <div className="text-xs text-slate-400 truncate font-semibold bg-slate-800/40 p-2.5 rounded border border-slate-700/30 flex items-center justify-between">
                <span>Selected: {selectedFile.name}</span>
                <span className="text-[10px] bg-police-gold/15 text-police-gold px-1.5 py-0.5 rounded border border-police-gold/20">Ready</span>
              </div>
            )}
            {mode === 'video' && videoFile && (
              <div className="text-xs text-slate-400 truncate font-semibold bg-slate-800/40 p-2.5 rounded border border-slate-700/30 flex items-center justify-between">
                <span>Video: {videoFile.name} ({(videoFile.size / (1024 * 1024)).toFixed(1)} MB)</span>
                <span className="text-[10px] bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">Ready</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (mode === 'image' ? !selectedFile : !videoFile)}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? (
                <RefreshCw className="w-4.5 h-4.5 animate-spin" />
              ) : (
                <span>{mode === 'image' ? 'Start SAHI Calibration' : 'Start Video Headcount'}</span>
              )}
            </button>
          </form>
        </div>

        {/* Right Side: Visual Feed & Analytics */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* === VIDEO MODE CONTENT === */}
          {mode === 'video' && (
            <>
              {/* Live Frame Viewer */}
              <div className="glass-panel p-6 rounded-xl border border-slate-800 relative overflow-hidden bg-[#0a0f1d]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <Activity className="w-4 h-4 text-police-red" />
                    <span>Live CCTV Analysis Feed</span>
                  </h3>
                  {videoStream.isStreaming && (
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                      <span className="text-[10px] text-red-400 font-bold uppercase tracking-wider">Processing</span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col justify-center items-center h-[300px] rounded-lg bg-[#050B14] border border-slate-800/50 overflow-hidden">
                  {videoStream.currentFrame ? (
                    <img 
                      src={videoStream.currentFrame} 
                      alt="Annotated video frame" 
                      className="max-h-full max-w-full object-contain"
                    />
                  ) : videoPreviewUrl && !videoStream.isStreaming ? (
                    <video 
                      src={videoPreviewUrl}
                      className="max-h-full max-w-full object-contain opacity-50"
                      muted
                    />
                  ) : (
                    <div className="text-center text-slate-500">
                      <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p className="text-xs font-semibold">Video Feed Inactive</p>
                      <p className="text-[10px] mt-1">Upload a video to start real-time headcount analysis.</p>
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                {(videoStream.isStreaming || videoStream.summary) && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">
                        Frame {videoStream.frameIdx} / {videoStream.totalFrames}
                      </span>
                      <span className="text-[10px] font-bold text-police-gold">{progressPct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-police-gold to-amber-400 rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${progressPct}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Real-Time Stats Row */}
              {(videoStream.isStreaming || videoStream.frameCounts.length > 0) && (
                <div className="grid grid-cols-3 gap-4">
                  {/* Live Headcount */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Live Headcount</span>
                    <span className={`text-4xl font-black transition-all duration-200 ${
                      videoStream.headcount > 30 ? 'text-police-red' : videoStream.headcount > 10 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {videoStream.headcount}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">persons detected</span>
                  </div>

                  {/* Peak Count */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Peak Count</span>
                    <span className="text-4xl font-black text-police-red">
                      {videoStream.peakCount}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">max in single frame</span>
                  </div>

                  {/* Density Grade */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Density Grade</span>
                    <span className={`text-3xl font-black ${
                      videoStream.density === 'Extreme' || videoStream.density === 'High' ? 'text-police-red' : 
                      videoStream.density === 'Medium' ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {videoStream.density}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">crowd classification</span>
                  </div>
                </div>
              )}

              {/* Sparkline Chart */}
              {videoStream.frameCounts.length > 5 && (
                <div className="glass-panel p-5 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-police-red" />
                      <span>Headcount Timeline</span>
                    </h3>
                    <span className="text-[10px] text-slate-500 font-semibold">
                      {videoStream.frameCounts.length} data points
                    </span>
                  </div>
                  <SparklineChart data={videoStream.frameCounts} width={600} height={90} />
                </div>
              )}

              {/* Video Summary */}
              {videoStream.summary && (
                <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-emerald-400 border-b border-slate-800 pb-3 flex items-center space-x-2">
                    <BarChart3 className="w-4 h-4" />
                    <span>Video Analysis Complete</span>
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Average Headcount</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.average_headcount} people</span>
                      </div>
                      <Users className="w-6 h-6 text-police-gold opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Peak Headcount</span>
                        <span className="text-2xl font-black text-police-red">{videoStream.summary.peak_headcount} people</span>
                      </div>
                      <AlertTriangle className="w-6 h-6 text-police-red opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Frames Processed</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.total_frames_processed}</span>
                      </div>
                      <Film className="w-6 h-6 text-slate-400 opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Crowd Density</span>
                        <span className={`text-2xl font-black ${
                          videoStream.summary.crowd_density === 'Extreme' || videoStream.summary.crowd_density === 'High' ? 'text-police-red' : 'text-amber-400'
                        }`}>{videoStream.summary.crowd_density}</span>
                      </div>
                      <ShieldCheck className="w-6 h-6 text-emerald-400 opacity-55" />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* === IMAGE MODE CONTENT === */}
          {mode === 'image' && (
            <>
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}
