import React, { useState } from 'react';
import { trafficApi } from '../services/api';
import { Siren, Phone, ShieldCheck, Mail, MapPin, Send, RefreshCw } from 'lucide-react';

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

export default function PoliceAlerts() {
  const [junction, setJunction] = useState('SilkBoardJunc');
  const [delay, setDelay] = useState(60);
  const [officers, setOfficers] = useState(8);
  const [barricades, setBarricades] = useState(12);

  const [nearestStation, setNearestStation] = useState<any | null>(null);
  const [dispatchResult, setDispatchResult] = useState<any | null>(null);
  const [loadingStation, setLoadingStation] = useState(false);
  const [loadingSend, setLoadingSend] = useState(false);

  const handleCalculateProximity = async () => {
    setLoadingStation(true);
    setNearestStation(null);
    setDispatchResult(null);
    try {
      const coords = junctionCoords[junction] || [12.9176, 77.6246];
      const result = await trafficApi.getNearestStation(coords[0], coords[1]);
      setNearestStation(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingStation(false);
    }
  };

  const handleDispatch = async () => {
    if (!nearestStation) return;
    
    setLoadingSend(true);
    try {
      const coords = junctionCoords[junction] || [12.9176, 77.6246];
      const payload = {
        recipient_phone: nearestStation.phone,
        event_type: "unplanned",
        priority: "High",
        congestion: "High",
        expected_delay: Number(delay),
        police_needed: Number(officers),
        barricades: Number(barricades),
        location_name: junction,
        latitude: coords[0],
        longitude: coords[1]
      };
      
      const result = await trafficApi.sendAlert(payload);
      setDispatchResult(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSend(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">POLICE DISPATCH & PROXIMITY FINDER</h1>
        <p className="text-sm text-slate-400">Locate the closest active police station and dispatch SMS warning alerts to patrol officers.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Parameters Form */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6 hover-scale-premium animate-slide-up delay-75">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Siren className="w-4.5 h-4.5 text-police-gold" />
            <span>Dispatch Settings</span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Select Incident Junction</label>
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
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Expected Delay (Minutes)</label>
              <input 
                type="number" 
                value={delay} 
                onChange={(e) => setDelay(Number(e.target.value))}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Officers Required</label>
                <input 
                  type="number" 
                  value={officers} 
                  onChange={(e) => setOfficers(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Barricades Needed</label>
                <input 
                  type="number" 
                  value={barricades} 
                  onChange={(e) => setBarricades(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            <button
              onClick={handleCalculateProximity}
              disabled={loadingStation}
              className="w-full py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700/50 hover:border-police-gold/50 text-slate-200 font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loadingStation ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <span>Resolve Nearest Station</span>}
            </button>
          </div>
        </div>

        {/* Right Side: Proximity Find Result and SMS logger */}
        <div className="lg:col-span-2 space-y-6">
          {nearestStation && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5 animate-slide-up shadow-xl hover-scale-premium delay-100">
              <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">Nearest Resolved Station</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Station Name</span>
                    <span className="text-sm font-extrabold text-slate-200">{nearestStation.station_name}</span>
                  </div>
                  <MapPin className="w-5 h-5 text-police-gold opacity-55" />
                </div>

                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Geodesic Proximity</span>
                    <span className="text-sm font-extrabold text-slate-200">{nearestStation.distance_km.toFixed(2)} km (ETA {nearestStation.eta_minutes} mins)</span>
                  </div>
                  <Phone className="w-5 h-5 text-police-light opacity-55" />
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 justify-between sm:items-center bg-slate-900/40 p-4 rounded border border-slate-800">
                <div>
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Contact Details / Dispatch Number</span>
                  <span className="text-sm font-extrabold text-slate-200">{nearestStation.phone}</span>
                </div>
                <button
                  onClick={handleDispatch}
                  disabled={loadingSend}
                  className="px-5 py-2.5 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-1.5 shadow-lg shadow-police-gold/10 w-full sm:w-auto flex-shrink-0"
                >
                  {loadingSend ? <RefreshCw className="w-4 h-4 animate-spin" /> : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Transmit SMS Dispatch</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* SMS Dispatch log */}
          {dispatchResult && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 animate-slide-up shadow-xl hover-scale-premium delay-150">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300">Twilio Gateway Log</h3>
                <span className="px-2.5 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[9px] text-emerald-400 font-bold uppercase">SMS TRANSMITTED</span>
              </div>

              <div className="bg-slate-950 p-4 rounded-lg font-mono text-[11px] text-slate-300 border border-slate-900 space-y-2 max-h-[160px] overflow-y-auto">
                <p className="text-slate-500">// Message ID: {dispatchResult.id}</p>
                <p className="text-slate-500">// Timestamp: {dispatchResult.timestamp}</p>
                <p className="text-slate-500">// Recipient: {dispatchResult.recipient_phone}</p>
                <p className="text-slate-200 mt-2">{dispatchResult.payload}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
