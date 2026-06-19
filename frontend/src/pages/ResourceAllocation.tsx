import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { 
  ShieldCheck, Siren, Sliders, Settings2, Tv, MapPin, 
  Trash2, Send, CheckCircle2, AlertTriangle, Construction, Info, RefreshCw
} from 'lucide-react';

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

const graphNeighbors: { [key: string]: string[] } = {
  'SilkBoardJunc': ['HSRLayout14thMain', 'MadiwalaCheckpost', 'BTMLayout16thMain'],
  'HSRLayout14thMain': ['SilkBoardJunc', 'AgaraJunction'],
  'AgaraJunction': ['HSRLayout14thMain', 'IbblurJunction', 'KoramangalaWaterTank', 'HSRLayout27thMain'],
  'IbblurJunction': ['AgaraJunction', 'BellandurJunction', 'HSRLayout27thMain'],
  'BellandurJunction': ['IbblurJunction'],
  'MadiwalaCheckpost': ['SilkBoardJunc', 'KoramangalaWaterTank'],
  'KoramangalaWaterTank': ['MadiwalaCheckpost', 'AgaraJunction', 'BTMLayout16thMain'],
  'BTMLayout16thMain': ['SilkBoardJunc', 'KoramangalaWaterTank'],
  'HSRLayout27thMain': ['AgaraJunction', 'IbblurJunction'],
};

// Custom Leaflet Icons using inline SVGs for compatibility & crisp scaling
const junctionIcon = new L.DivIcon({
  html: `<div class="relative w-8 h-8">
           <div class="absolute inset-0 bg-blue-500/20 border-2 border-blue-500 rounded-full animate-ping"></div>
           <div class="absolute top-1 left-1 w-6 h-6 bg-blue-600 border border-slate-900 rounded-full flex items-center justify-center shadow-lg">
             <svg class="w-3.5 h-3.5 text-slate-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
             </svg>
           </div>
         </div>`,
  className: 'junction-marker-icon',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const neighborIcon = new L.DivIcon({
  html: `<div class="w-5 h-5 bg-slate-800 border-2 border-slate-600 rounded-full flex items-center justify-center shadow-md">
           <div class="w-2 h-2 bg-slate-400 rounded-full"></div>
         </div>`,
  className: 'neighbor-marker-icon',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const autoBarricadeIcon = new L.DivIcon({
  html: `<div class="w-8 h-8 bg-amber-500 border border-slate-900 rounded-lg flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-150">
           <svg class="w-5 h-5 text-slate-950 font-bold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
           </svg>
         </div>`,
  className: 'barricade-marker-icon',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const manualBarricadeIcon = new L.DivIcon({
  html: `<div class="w-8 h-8 bg-orange-600 border border-slate-900 rounded-lg flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-150 animate-bounce">
           <svg class="w-5 h-5 text-slate-100 font-bold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
           </svg>
         </div>`,
  className: 'manual-barricade-marker-icon',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const vmsIcon = new L.DivIcon({
  html: `<div class="w-8 h-8 bg-emerald-500 border border-slate-900 rounded-lg flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-150">
           <svg class="w-5 h-5 text-slate-950 font-bold" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/>
           </svg>
         </div>`,
  className: 'vms-marker-icon',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

// Map recentering controller
function MapRecenter({ coords }: { coords: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(coords, map.getZoom());
  }, [coords, map]);
  return null;
}

// Map click event listner to place manual barricades
function MapClickHandler({ onClick, enabled }: { onClick: (latlng: L.LatLng) => void, enabled: boolean }) {
  useMapEvents({
    click: (e) => {
      if (enabled) {
        onClick(e.latlng);
      }
    },
  });
  return null;
}

export default function ResourceAllocation() {
  const [junction, setJunction] = useState('SilkBoardJunc');
  const [congestion, setCongestion] = useState('High');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);
  
  // Custom manual barricades placed by clicking on the map
  const [manualBarricades, setManualBarricades] = useState<{ id: number; lat: number; lng: number }[]>([]);
  const [placementMode, setPlacementMode] = useState(false);
  const [dispatchStatus, setDispatchStatus] = useState<string | null>(null);

  // Clear manual barricades when junction changes
  useEffect(() => {
    setManualBarricades([]);
    setDispatchStatus(null);
  }, [junction]);

  // Replicate local calculation rules
  const calculateDeployment = () => {
    const cong = congestion.toUpperCase();
    const prio = priority.toUpperCase();
    
    let basePolice = 2;
    if (cong === 'MEDIUM') basePolice = 4;
    else if (cong === 'HIGH') basePolice = 8;
    else if (cong === 'EXTREME') basePolice = 15;

    let police = basePolice;
    if (prio === 'HIGH') police += 2;
    if (closure) police += 4;
    police = Math.min(20, police);

    let baseBarricades = 1;
    if (cong === 'MEDIUM') baseBarricades = 5;
    else if (cong === 'HIGH') baseBarricades = 12;
    else if (cong === 'EXTREME') baseBarricades = 20;

    let barricades = baseBarricades;
    if (closure) barricades += 8;
    barricades = Math.min(30, barricades);

    // VMS Boards calculation matching resource_service.py
    let vms = 1;
    if (cong === 'HIGH' || cong === 'EXTREME') vms += 1;
    if (prio === 'HIGH') vms += 1;
    vms = Math.min(5, vms);

    return { police, barricades, vms };
  };

  const { police, barricades, vms } = calculateDeployment();
  const activeCoord = junctionCoords[junction] || [12.9176, 77.6246];
  const neighbors = graphNeighbors[junction] || [];

  // Calculate automatic cordon barricades and VMS boards coordinates
  // (placed at fraction positions along the segments connecting the selected junction to its neighbors)
  const autoBarricadeCoords = closure ? neighbors.map((neighName) => {
    const coordJunc = activeCoord;
    const coordNeigh = junctionCoords[neighName];
    if (!coordNeigh) return null;
    
    // Barricades placed 15% of the way towards the neighbor
    const lat = coordJunc[0] + 0.15 * (coordNeigh[0] - coordJunc[0]);
    const lng = coordJunc[1] + 0.15 * (coordNeigh[1] - coordJunc[1]);
    return { name: neighName, lat, lng };
  }).filter((item): item is { name: string; lat: number; lng: number } => item !== null) : [];

  const autoVmsCoords = neighbors.slice(0, vms).map((neighName) => {
    const coordJunc = activeCoord;
    const coordNeigh = junctionCoords[neighName];
    if (!coordNeigh) return null;
    
    // VMS boards placed 35% of the way towards the neighbor
    const lat = coordJunc[0] + 0.35 * (coordNeigh[0] - coordJunc[0]);
    const lng = coordJunc[1] + 0.35 * (coordNeigh[1] - coordJunc[1]);
    return { name: neighName, lat, lng };
  }).filter((item): item is { name: string; lat: number; lng: number } => item !== null);

  const handleMapClick = (latlng: L.LatLng) => {
    setManualBarricades(prev => [
      ...prev,
      { id: Date.now(), lat: latlng.lat, lng: latlng.lng }
    ]);
  };

  const handleRemoveManualBarricade = (id: number) => {
    setManualBarricades(prev => prev.filter(b => b.id !== id));
  };

  const handleClearManualBarricades = () => {
    setManualBarricades([]);
  };

  const handleDispatch = () => {
    setDispatchStatus("dispatching");
    setTimeout(() => {
      setDispatchStatus("success");
    }, 1200);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between sm:items-center">
        <div>
          <h1 className="text-3xl font-black tracking-tight">TACTICAL BARRICADES & RESOURCE OPTIMIZER</h1>
          <p className="text-sm text-slate-400">Model road closures, place physical barricades on the graph network, and calculate police dispatch requirements.</p>
        </div>
        <div className="flex items-center space-x-2 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-lg self-start sm:self-auto flex-shrink-0">
          <Construction className="w-4.5 h-4.5 text-amber-500" />
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Cordon Planner V2</span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        {/* Left Side: Parameters and Controls */}
        <div className="xl:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6 hover-scale-premium animate-slide-up delay-75">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2 select-none">
              <Settings2 className="w-4.5 h-4.5 text-police-gold" />
              <span>Optimization Parameters</span>
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Target Junction Node</label>
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Congestion severity</label>
                  <select 
                    value={congestion} 
                    onChange={(e) => setCongestion(e.target.value)}
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Extreme">Extreme</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Priority Level</label>
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
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Requires Cordon / Closure</label>
                <select 
                  value={String(closure)} 
                  onChange={(e) => setClosure(e.target.value === 'true')}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="true">Yes (Deploy Auto-Barricades)</option>
                  <option value="false">No (Free Flow)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Interactive Manual Barricades Placement Panel */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 hover-scale-premium animate-slide-up delay-100">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-slate-400" />
                <span>Manual Barricade Dispatch</span>
              </h3>
              {manualBarricades.length > 0 && (
                <button
                  onClick={handleClearManualBarricades}
                  className="text-[9px] font-bold text-police-red hover:text-red-400 uppercase flex items-center space-x-1"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Clear All ({manualBarricades.length})</span>
                </button>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between bg-slate-900/40 p-3 rounded-lg border border-slate-800">
                <div>
                  <span className="block text-xs font-extrabold text-slate-200">Manual Map Placement</span>
                  <span className="text-[10px] text-slate-500">Toggle mode and click on the map to add blockades</span>
                </div>
                <button
                  onClick={() => setPlacementMode(!placementMode)}
                  className={`px-3 py-1.5 text-[10px] font-black uppercase rounded-lg border transition-all ${
                    placementMode 
                      ? 'bg-orange-600/20 border-orange-500 text-orange-400 shadow-md shadow-orange-500/10'
                      : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600'
                  }`}
                >
                  {placementMode ? 'Placement ON' : 'Placement OFF'}
                </button>
              </div>

              {manualBarricades.length === 0 ? (
                <p className="text-[10px] text-slate-500 italic">No manual blockades placed yet. Enable placement mode and click on the map to drop barricades.</p>
              ) : (
                <div className="max-h-[140px] overflow-y-auto space-y-2 pr-1">
                  {manualBarricades.map((b, idx) => (
                    <div key={b.id} className="flex justify-between items-center bg-slate-900/20 border border-slate-850 p-2 rounded text-[10px] font-mono">
                      <span className="text-slate-300">Blockade #{idx + 1} ({b.lat.toFixed(4)}, {b.lng.toFixed(4)})</span>
                      <button 
                        onClick={() => handleRemoveManualBarricade(b.id)}
                        className="text-slate-500 hover:text-police-red transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Allocation Details & Action Plan */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5 hover-scale-premium animate-slide-up delay-150">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Info className="w-4 h-4 text-slate-400" />
              <span>Cordon Deployment Plan</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed font-medium">
              The optimization parameters recommend mobilizing <strong className="text-slate-200">{police} Officers</strong>.
              {closure ? (
                <span> Since a cordon is active, <strong className="text-amber-400">{autoBarricadeCoords.length} automatic barricades</strong> have been positioned 100 meters upstream on connecting links to block vehicular access to the gridlock node. </span>
              ) : (
                <span> Road closure is not requested; free-flow parameters are active. </span>
              )}
              {manualBarricades.length > 0 && (
                <span>Additionally, <strong className="text-orange-500">{manualBarricades.length} custom manual barricades</strong> have been logged. </span>
              )}
              <strong className="text-emerald-400">{autoVmsCoords.length} VMS boards</strong> should be activated at upstream intersections to notify commuters.
            </p>

            <button
              onClick={handleDispatch}
              disabled={dispatchStatus === 'dispatching'}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2 shadow-lg shadow-police-gold/15"
            >
              {dispatchStatus === 'dispatching' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Dispatch Resources & Blockades</span>
                </>
              )}
            </button>

            {dispatchStatus === 'success' && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center space-x-2.5 text-emerald-400 text-xs font-semibold animate-fade-in">
                <CheckCircle2 className="w-4.5 h-4.5 flex-shrink-0" />
                <span>Deployment success! Patrol stations notified. Barricade crews dispatched.</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Deployment Recommendations & Tactical Map */}
        <div className="lg:col-span-3 space-y-6">
          {/* Resource recommendations metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-blue select-none hover-scale-premium animate-slide-up delay-75">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Officer Personnel</span>
                <span className="text-2xl font-black text-slate-100">{police} Officers</span>
                <p className="text-[9px] text-slate-500 mt-2">Active field dispatch units</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-police-light border border-slate-700/30">
                <Siren className="w-6 h-6 siren-glow" />
              </div>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-gold select-none hover-scale-premium animate-slide-up delay-100">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Barricades Recommended</span>
                <span className="text-2xl font-black text-slate-100">{barricades + manualBarricades.length} Units</span>
                <p className="text-[9px] text-slate-500 mt-2">{barricades} Auto + {manualBarricades.length} Manual</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-police-gold border border-slate-700/30">
                <ShieldCheck className="w-6 h-6" />
              </div>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-blue select-none hover-scale-premium animate-slide-up delay-150">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">VMS Boards Needed</span>
                <span className="text-2xl font-black text-slate-100">{vms} Boards</span>
                <p className="text-[9px] text-slate-500 mt-2">Variable sign boards</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-emerald-400 border border-slate-700/30">
                <Tv className="w-6 h-6" />
              </div>
            </div>
          </div>

          {/* Tactical Map */}
          <div className="h-[350px] sm:h-[500px] glass-panel rounded-xl overflow-hidden border border-slate-800 relative shadow-2xl animate-fade-in delay-200">
            <MapContainer center={[12.9234, 77.6412]} zoom={13.5} scrollWheelZoom={true}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />

              <MapRecenter coords={activeCoord} />
              
              <MapClickHandler onClick={handleMapClick} enabled={placementMode} />

              {/* Draw road links / network connection edges for visual context */}
              {Object.entries(graphNeighbors).map(([node, nodeNeighbors]) => {
                const nodeCoord = junctionCoords[node];
                if (!nodeCoord) return null;
                return nodeNeighbors.map((neighName) => {
                  const neighCoord = junctionCoords[neighName];
                  if (!neighCoord) return null;
                  return (
                    <Polyline 
                      key={`${node}-${neighName}`}
                      positions={[nodeCoord, neighCoord]} 
                      pathOptions={{ color: '#1e293b', weight: 3, opacity: 0.5 }} 
                    />
                  );
                });
              })}

              {/* Render non-active junctions in the background */}
              {Object.entries(junctionCoords).map(([name, coords]) => {
                if (name === junction) return null;
                return (
                  <Marker key={name} position={coords} icon={neighborIcon}>
                    <Popup>
                      <div className="p-1 text-slate-900 font-sans">
                        <h4 className="font-extrabold text-xs">{name}</h4>
                        <p className="text-[10px] text-slate-500">Adjacent Network Node</p>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}

              {/* Draw Safety Cordon circle around active junction */}
              <Circle
                center={activeCoord}
                radius={250} // 250m safety cordon
                pathOptions={{ 
                  color: '#eab308', 
                  fillColor: '#eab308', 
                  fillOpacity: 0.05, 
                  weight: 1.5,
                  dashArray: '4, 6'
                }}
              />

              {/* Render the Active Junction marker */}
              <Marker position={activeCoord} icon={junctionIcon}>
                <Popup>
                  <div className="p-1 text-slate-900 font-sans">
                    <h4 className="font-extrabold text-xs text-blue-600">{junction}</h4>
                    <p className="text-[10px] text-slate-500">Incident Target Junction</p>
                    <p className="text-[10px] text-slate-700 mt-1">Status: <strong>Cordon Active</strong></p>
                  </div>
                </Popup>
              </Marker>

              {/* Render Automatic Cordon Barricades */}
              {autoBarricadeCoords.map((b, idx) => (
                <Marker key={`auto-barr-${idx}`} position={[b.lat, b.lng]} icon={autoBarricadeIcon}>
                  <Popup>
                    <div className="p-1 text-slate-900 font-sans">
                      <h4 className="font-extrabold text-xs text-amber-600 flex items-center space-x-1">
                        <Construction className="w-3.5 h-3.5" />
                        <span>Auto-Barricade #{idx + 1}</span>
                      </h4>
                      <p className="text-[10px] text-slate-600 mt-1">Positioned upstream towards {b.name} to close road link access.</p>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* Render Upstream VMS warning sign boards */}
              {autoVmsCoords.map((v, idx) => (
                <Marker key={`auto-vms-${idx}`} position={[v.lat, v.lng]} icon={vmsIcon}>
                  <Popup>
                    <div className="p-1 text-slate-900 font-sans">
                      <h4 className="font-extrabold text-xs text-emerald-600 flex items-center space-x-1">
                        <Tv className="w-3.5 h-3.5" />
                        <span>VMS Warning Board #{idx + 1}</span>
                      </h4>
                      <p className="text-[10px] text-slate-600 mt-1">Displays rerouting instructions upstream towards {v.name}.</p>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* Render Manual Barricades */}
              {manualBarricades.map((b, idx) => (
                <Marker key={`manual-${b.id}`} position={[b.lat, b.lng]} icon={manualBarricadeIcon}>
                  <Popup>
                    <div className="p-1 text-slate-900 font-sans">
                      <h4 className="font-extrabold text-xs text-orange-600">Manual Barricade #{idx + 1}</h4>
                      <p className="text-[10px] text-slate-500">Coordinates: {b.lat.toFixed(5)}, {b.lng.toFixed(5)}</p>
                      <button
                        onClick={() => handleRemoveManualBarricade(b.id)}
                        className="mt-2 text-[9px] bg-red-100 hover:bg-red-200 text-red-700 font-bold px-2 py-1 rounded"
                      >
                        Remove Blockade
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>

            {/* Map overlay placement indicator */}
            {placementMode && (
              <div className="absolute top-4 right-4 z-[1000] bg-orange-600/90 border border-orange-500 text-slate-100 text-[10px] font-black uppercase px-3 py-1.5 rounded-lg flex items-center space-x-2 animate-pulse shadow-lg">
                <AlertTriangle className="w-4 h-4 text-slate-100" />
                <span>Placement Mode Active: Click map to place blockades</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
