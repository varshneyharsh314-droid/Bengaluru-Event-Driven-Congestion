import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { trafficApi } from '../services/api';
import { RefreshCw, Play, ShieldAlert, Sparkles, Navigation } from 'lucide-react';

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

const createMarkerIcon = (color: string) => {
  return new L.DivIcon({
    html: `<div class="w-6 h-6 bg-${color}-500 border border-slate-900 rounded-full flex items-center justify-center shadow-lg">
             <div class="w-2.5 h-2.5 bg-slate-100 rounded-full"></div>
           </div>`,
    className: 'route-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const blueIcon = createMarkerIcon('blue');

export default function DiversionRecommendation() {
  const [source, setSource] = useState('SilkBoardJunc');
  const [destination, setDestination] = useState('IbblurJunction');
  const [blockedRoad, setBlockedRoad] = useState<string>('HSRLayout14thMain,AgaraJunction');
  const [multiplier, setMultiplier] = useState(10.0);
  const [algorithm, setAlgorithm] = useState('astar');

  const [routeData, setRouteData] = useState<any | null>(null);
  const [diversionText, setDiversionText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setRouteData(null);
    setDiversionText(null);
    try {
      // Formulate blocked roads array: e.g. [["HSRLayout14thMain", "AgaraJunction"]]
      let blockedList: [string, string][] = [];
      if (blockedRoad) {
        const parts = blockedRoad.split(',');
        if (parts.length === 2) {
          blockedList.push([parts[0].trim(), parts[1].trim()]);
        }
      }

      const payload = {
        source,
        destination,
        blocked_roads: blockedList,
        congestion_multiplier: Number(multiplier),
        algorithm
      };

      const routeResult = await trafficApi.getEmergencyRoute(payload);
      setRouteData(routeResult);

      // Query diversion text for source junction
      const divResult = await trafficApi.suggestDiversion(source, "Central Zone");
      setDiversionText(divResult.suggested_diversion);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Build route lines coordinates
  const normalRouteCoords = routeData?.normal_route?.map((node: string) => junctionCoords[node]).filter(Boolean) || [];
  const emergencyRouteCoords = routeData?.emergency_route?.map((node: string) => junctionCoords[node]).filter(Boolean) || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">EMERGENCY CORRIDOR RECOMMENDATIONS</h1>
        <p className="text-sm text-slate-400">Calculate high-speed corridors for ambulances or emergency personnel around blocked junctions.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        {/* Left Form Panel */}
        <div className="xl:col-span-2 space-y-6">
          <form onSubmit={handleCalculate} className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Sparkles className="w-4.5 h-4.5 text-police-gold" />
              <span>Routing Settings</span>
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Source Junction</label>
                <select 
                  value={source} 
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  {Object.keys(junctionCoords).map(key => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Destination Junction</label>
                <select 
                  value={destination} 
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  {Object.keys(junctionCoords).map(key => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Blocked Road Links (Source,Target)</label>
              <select 
                value={blockedRoad} 
                onChange={(e) => setBlockedRoad(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="">No Blocked Roads</option>
                <option value="HSRLayout14thMain,AgaraJunction">HSRLayout14thMain ➔ AgaraJunction</option>
                <option value="SilkBoardJunc,HSRLayout14thMain">SilkBoardJunc ➔ HSRLayout14thMain</option>
                <option value="AgaraJunction,IbblurJunction">AgaraJunction ➔ IbblurJunction</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Multiplier (Congestion Delay)</label>
                <input 
                  type="number" 
                  step="0.5" min="1"
                  value={multiplier} 
                  onChange={(e) => setMultiplier(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Algorithm</label>
                <select 
                  value={algorithm} 
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="astar">A* Heuristic</option>
                  <option value="dijkstra">Dijkstra Core</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <span>Resolve Shortest Path</span>}
            </button>
          </form>

          {/* Rerouting analysis result */}
          {routeData && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 animate-fade-in">
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">Routing Analysis</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Normal Path time</span>
                  <span className="text-lg font-extrabold text-police-red">{routeData.normal_time_congested.toFixed(1)} mins</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded border border-slate-800">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Emergency corridor time</span>
                  <span className="text-lg font-extrabold text-emerald-400">{routeData.emergency_time_congested.toFixed(1)} mins</span>
                </div>
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 p-3.5 rounded flex items-center justify-between glow-blue">
                <div>
                  <span className="block text-[10px] font-bold text-emerald-400 uppercase">Commuters Time Saved</span>
                  <span className="text-xl font-black text-slate-100">{routeData.time_saved_minutes.toFixed(1)} minutes saved</span>
                </div>
                <Navigation className="w-6 h-6 text-emerald-400 animate-pulse" />
              </div>

              <div className="text-xs text-slate-400 space-y-2">
                <p><strong>Emergency path:</strong> {routeData.emergency_route.join(' ➔ ')}</p>
                {diversionText && (
                  <div className="pt-2 border-t border-slate-800/80">
                    <p className="text-police-gold font-bold">Tactical Diversion:</p>
                    <p className="text-[11px] mt-1">{diversionText}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Map Panel */}
        <div className="xl:col-span-3 h-[600px] glass-panel rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
          <MapContainer center={[12.9234, 77.6412]} zoom={13} scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            {/* Markers for key junctions */}
            {Object.entries(junctionCoords).map(([name, coords]) => (
              <Marker key={name} position={coords} icon={blueIcon}>
                <Popup>
                  <div className="p-1 text-slate-900">
                    <h4 className="font-extrabold text-xs">{name}</h4>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* Draw Path Polylines */}
            {normalRouteCoords.length > 0 && (
              <Polyline 
                positions={normalRouteCoords} 
                pathOptions={{ color: 'red', weight: 4, opacity: 0.65, dashArray: '5, 10' }} 
              />
            )}
            {emergencyRouteCoords.length > 0 && (
              <Polyline 
                positions={emergencyRouteCoords} 
                pathOptions={{ color: '#10b981', weight: 6, opacity: 0.95 }} 
              />
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
