import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { trafficApi } from '../services/api';
import { Siren, ShieldAlert, Sparkles, MapPin, CheckCircle, RefreshCw } from 'lucide-react';

// Create a custom SVG marker for Leaflet to prevent broken assets pathing
const createCustomIcon = (color: string) => {
  return new L.DivIcon({
    html: `<div class="relative w-8 h-8">
             <div class="absolute inset-0 bg-${color}-500/30 border-2 border-${color}-500 rounded-full animate-ping"></div>
             <div class="absolute top-1 left-1 w-6 h-6 bg-${color}-500 border border-slate-900 rounded-full flex items-center justify-center shadow-lg">
               <svg class="w-3.5 h-3.5 text-slate-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
               </svg>
             </div>
           </div>`,
    className: 'custom-leaflet-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });
};

const defaultIcon = createCustomIcon('blue');
const highIcon = createCustomIcon('red');

export default function CongestionHeatmap() {
  const [eventType, setEventType] = useState('unplanned');
  const [eventCause, setEventCause] = useState('accident');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);
  const [hour, setHour] = useState(18);
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [duration, setDuration] = useState(2.5);
  const [zone, setZone] = useState('Central Zone 2');
  const [junction, setJunction] = useState('SilkBoardJunc');
  const [description, setDescription] = useState('severe accident and heavy traffic at junction');
  
  const [prediction, setPrediction] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  // Map nodes coordinates
  const junctionCoords: { [key: string]: [number, number] } = {
    'SilkBoardJunc': [12.9176, 77.6246],
    'HSRLayout14thMain': [12.9172, 77.6366],
    'AgaraJunction': [12.9261, 77.6508],
    'IbblurJunction': [12.9234, 77.6712],
    'BellandurJunction': [12.9366, 77.6830],
    'MadiwalaCheckpost': [12.9225, 77.6189],
    'KoramangalaWaterTank': [12.9348, 77.6210],
    'BTMLayout16thMain': [12.9142, 77.6080],
    'HSRLayout27thMain': [12.9110, 77.6475],
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const coord = junctionCoords[junction] || [12.9176, 77.6246];
      const payload = {
        event_type: eventType,
        event_cause: eventCause,
        priority: priority,
        requires_road_closure: closure,
        hour: Number(hour),
        day_of_week: Number(dayOfWeek),
        duration_hours: Number(duration),
        zone: zone,
        junction: junction,
        latitude: coord[0],
        longitude: coord[1],
        description: description
      };
      
      const result = await trafficApi.predictCongestion(payload);
      setPrediction(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const activeCoord = junctionCoords[junction] || [12.9176, 77.6246];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">SPATIAL CONGESTION CALIBRATION</h1>
        <p className="text-sm text-slate-400">Map incidents to evaluate expected severity gridlocks and plan emergency response routes.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        {/* Left Column: Form Inputs & Predictions */}
        <div className="xl:col-span-2 space-y-6">
          <form onSubmit={handlePredict} className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5 hover-scale-premium animate-slide-up delay-75">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Sparkles className="w-4.5 h-4.5 text-police-gold" />
              <span>Inference Parameters</span>
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Type</label>
                <select 
                  value={eventType} 
                  onChange={(e) => setEventType(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="unplanned">Unplanned</option>
                  <option value="planned">Planned</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Cause</label>
                <select 
                  value={eventCause} 
                  onChange={(e) => setEventCause(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="accident">Accident</option>
                  <option value="vehicle_breakdown">Breakdown</option>
                  <option value="water_logging">Waterlogging</option>
                  <option value="construction">Construction</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
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

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Road Closure</label>
                <select 
                  value={String(closure)} 
                  onChange={(e) => setClosure(e.target.value === 'true')}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Hour (0-23)</label>
                <input 
                  type="number" 
                  min="0" max="23"
                  value={hour} 
                  onChange={(e) => setHour(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Duration (Hours)</label>
                <input 
                  type="number" 
                  step="0.5" min="0.5"
                  value={duration} 
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Junction Node</label>
                <select 
                  value={junction} 
                  onChange={(e) => setJunction(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  {Object.keys(junctionCoords).map(key => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Zone</label>
                <select 
                  value={zone} 
                  onChange={(e) => setZone(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="Central Zone 2">Central Zone 2</option>
                  <option value="East Zone 1">East Zone 1</option>
                  <option value="South Zone 1">South Zone 1</option>
                  <option value="North Zone 2">North Zone 2</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Description / NLP Keyword Inputs</label>
              <textarea 
                value={description} 
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. severe water logging and accident near Agara Junction..."
                rows={2}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <span>Execute Congestion Model</span>}
            </button>
          </form>

          {/* Inference results */}
          {prediction && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 animate-slide-up hover-scale-premium delay-150">
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">Prediction Matrix</h3>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Severity Prediction:</span>
                <span className={`px-3 py-1 text-xs font-black uppercase rounded border ${
                  prediction.predicted_congestion === 'High' 
                    ? 'bg-red-500/10 border-red-500/30 text-police-red glow-red' 
                    : prediction.predicted_congestion === 'Medium'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 glow-gold'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 glow-blue'
                }`}>{prediction.predicted_congestion}</span>
              </div>

              <div className="space-y-2">
                <p className="text-[10px] uppercase font-bold text-slate-400">Probability Distributions</p>
                <div className="space-y-1.5">
                  {Object.entries(prediction.probabilities).map(([key, val]: any) => (
                    <div key={key} className="flex items-center space-x-2 text-xs">
                      <span className="w-16 text-slate-300">{key}:</span>
                      <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${key === 'High' ? 'bg-police-red' : key === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                          style={{ width: `${val * 100}%` }}
                        ></div>
                      </div>
                      <span className="w-8 text-right font-mono text-[10px] text-slate-400">{Math.round(val * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t border-slate-800/80 pt-4">
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Delay Minutes</span>
                  <span className="text-sm font-extrabold text-slate-200">{prediction.predicted_delay_min} mins</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">XGBoost Pred Duration</span>
                  <span className="text-sm font-extrabold text-slate-200">{prediction.predicted_duration_minutes ? `${prediction.predicted_duration_minutes.toFixed(1)} mins` : 'N/A'}</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">XGBoost Pred Radius</span>
                  <span className="text-sm font-extrabold text-slate-200">{prediction.predicted_impact_radius_meters ? `${prediction.predicted_impact_radius_meters.toFixed(1)} meters` : 'N/A'}</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Police / Barricades</span>
                  <span className="text-sm font-extrabold text-slate-200">{prediction.resources.police_officers} / {prediction.resources.barricades}</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800 col-span-2">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">VMS Warning Boards Required</span>
                  <span className="text-sm font-extrabold text-police-gold">{prediction.resources.vms_boards !== undefined ? `${prediction.resources.vms_boards} Boards` : '0 Boards'}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Leaflet Map */}
        <div className="xl:col-span-3 h-[350px] sm:h-[500px] lg:h-[600px] glass-panel rounded-xl overflow-hidden border border-slate-800 relative shadow-2xl animate-fade-in delay-200">
          <MapContainer center={[12.9234, 77.6412]} zoom={13} scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            {/* Draw active nodes */}
            {Object.entries(junctionCoords).map(([name, coords]) => {
              const isActive = name === junction;
              return (
                <Marker 
                  key={name} 
                  position={coords} 
                  icon={isActive && prediction?.predicted_congestion === 'High' ? highIcon : defaultIcon}
                >
                  <Popup>
                    <div className="p-1 text-slate-900">
                      <h4 className="font-extrabold text-sm">{name}</h4>
                      <p className="text-xs text-slate-600">Coordinates: {coords[0].toFixed(4)}, {coords[1].toFixed(4)}</p>
                      {isActive && prediction && (
                        <div className="mt-2 pt-2 border-t border-slate-200">
                          <p className="text-xs"><strong>Severity:</strong> {prediction.predicted_congestion}</p>
                          <p className="text-xs"><strong>Predicted Duration:</strong> {prediction.predicted_duration_minutes?.toFixed(1)} mins</p>
                          <p className="text-xs"><strong>Impact Radius:</strong> {prediction.predicted_impact_radius_meters?.toFixed(1)} meters</p>
                        </div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}

            {/* Draw Red Impact Circle representing predicted impact radius */}
            {prediction && prediction.predicted_impact_radius_meters && (
              <Circle
                center={activeCoord}
                radius={prediction.predicted_impact_radius_meters}
                pathOptions={{ 
                  color: '#ef4444', 
                  fillColor: '#ef4444', 
                  fillOpacity: 0.15, 
                  weight: 2 
                }}
              />
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

