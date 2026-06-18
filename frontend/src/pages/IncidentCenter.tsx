import React, { useState, useEffect } from 'react';
import { trafficApi } from '../services/api';
import { ShieldAlert, CheckCircle2, Clock, MapPin, MessageSquare, RefreshCw, AlertCircle, Activity, Siren, Phone, Send } from 'lucide-react';

export default function IncidentCenter() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Dispatch Modal States
  const [activeDispatchIncident, setActiveDispatchIncident] = useState<any | null>(null);
  const [nearestStation, setNearestStation] = useState<any | null>(null);
  const [resolvingStation, setResolvingStation] = useState(false);
  const [loadingSend, setLoadingSend] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<any | null>(null);

  const [delay, setDelay] = useState(60);
  const [officers, setOfficers] = useState(8);
  const [barricades, setBarricades] = useState(12);

  useEffect(() => {
    if (activeDispatchIncident) {
      setDelay(activeDispatchIncident.delay_min || 30);
      setOfficers(activeDispatchIncident.police_deployed || 5);
      setBarricades(Math.round((activeDispatchIncident.police_deployed || 5) * 1.5));
      setNearestStation(null);
      setDispatchResult(null);
    }
  }, [activeDispatchIncident]);

  const handleInitiateDispatch = async (incident: any) => {
    setActiveDispatchIncident(incident);
    setResolvingStation(true);
    try {
      const result = await trafficApi.getNearestStation(incident.latitude, incident.longitude);
      setNearestStation(result);
    } catch (e) {
      console.error(e);
    } finally {
      setResolvingStation(false);
    }
  };

  const handleDispatch = async () => {
    if (!nearestStation || !activeDispatchIncident) return;
    setLoadingSend(true);
    try {
      const payload = {
        recipient_phone: nearestStation.phone,
        event_type: activeDispatchIncident.event_type || "unplanned",
        priority: activeDispatchIncident.priority || "High",
        congestion: activeDispatchIncident.congestion_level || "High",
        expected_delay: Number(delay),
        police_needed: Number(officers),
        barricades: Number(barricades),
        location_name: activeDispatchIncident.junction,
        latitude: activeDispatchIncident.latitude,
        longitude: activeDispatchIncident.longitude
      };
      const result = await trafficApi.sendAlert(payload);
      setDispatchResult(result);
    } catch (e) {
      console.error(e);
      alert("Failed to send alert.");
    } finally {
      setLoadingSend(false);
    }
  };

  const fetchActiveIncidents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await trafficApi.getActiveIncidents();
      // Only keep events that are crowd congestion or active database logged events
      setIncidents(data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to retrieve active incidents from backend repository.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveIncidents();
  }, []);

  const handleResolve = async (eventId: string) => {
    setActionLoading(eventId);
    try {
      await trafficApi.resolveIncident(eventId);
      // Refresh list
      const data = await trafficApi.getActiveIncidents();
      setIncidents(data);
    } catch (err) {
      console.error("Resolve error:", err);
      alert("Failed to resolve incident.");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-center select-none">
        <div>
          <h1 className="text-3xl font-black tracking-tight">OPERATIONAL INCIDENT CENTER</h1>
          <p className="text-sm text-slate-400">Review and manually clear active crowd congestion anomalies and ML-logged traffic incidents.</p>
        </div>
        <button
          onClick={fetchActiveIncidents}
          className="p-2.5 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-lg flex items-center space-x-2 transition-all duration-200"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="text-xs font-bold uppercase tracking-wider">Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && incidents.length === 0 ? (
        <div className="py-24 flex justify-center items-center">
          <RefreshCw className="w-10 h-10 text-police-gold animate-spin" />
        </div>
      ) : incidents.length === 0 ? (
        <div className="glass-panel p-16 rounded-xl border border-slate-800 text-center select-none bg-slate-900/10">
          <CheckCircle2 className="w-14 h-14 text-emerald-400 mx-auto mb-4 animate-pulse" />
          <h3 className="text-lg font-black text-slate-200">ALL JUNCTIONS CLEAR</h3>
          <p className="text-sm text-slate-500 mt-1.5 max-w-md mx-auto">No active crowd congestion incidents or database event locks currently logged. Feeds are running under free-flow parameters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {incidents.map((incident) => (
            <div 
              key={incident.event_id} 
              className={`glass-panel border-t-4 ${
                incident.congestion_level === 'High' || incident.congestion_level === 'Extreme'
                  ? 'border-t-red-500 shadow-red-950/5'
                  : incident.congestion_level === 'Medium'
                  ? 'border-t-amber-500 shadow-amber-950/5'
                  : 'border-t-blue-500 shadow-blue-950/5'
              } p-6 rounded-xl flex flex-col justify-between space-y-5 transition-transform duration-200 hover:scale-[1.01]`}
            >
              {/* Card Header */}
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-slate-400 uppercase tracking-wider bg-slate-900/60 px-2 py-0.5 rounded border border-slate-800/80">
                      {incident.event_id}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                      incident.event_cause === 'crowd_congestion'
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : 'bg-slate-800 text-slate-400 border-slate-700/30'
                    }`}>
                      {incident.event_cause.replace('_', ' ')}
                    </span>
                  </div>
                  <h3 className="text-lg font-extrabold text-slate-200 mt-2 flex items-center space-x-1.5">
                    <MapPin className="w-4 h-4 text-police-gold" />
                    <span>{incident.junction}</span>
                  </h3>
                </div>
                <span className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase border select-none ${
                  incident.congestion_level === 'High' || incident.congestion_level === 'Extreme'
                    ? 'bg-red-500/15 border-red-500/20 text-police-red'
                    : incident.congestion_level === 'Medium'
                    ? 'bg-amber-500/15 border-amber-500/20 text-amber-400'
                    : 'bg-emerald-500/15 border-emerald-500/20 text-emerald-400'
                }`}>
                  {incident.congestion_level} severity
                </span>
              </div>

              {/* Description body */}
              {incident.description && (
                <div className="p-3.5 bg-slate-900/50 rounded-lg border border-slate-800/80 flex items-start space-x-3">
                  <MessageSquare className="w-4.5 h-4.5 text-slate-500 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-slate-400 leading-relaxed font-semibold">{incident.description}</p>
                </div>
              )}

              {/* Metrics grid */}
              <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-slate-400">
                <div className="flex items-center space-x-2 bg-slate-900/30 p-2.5 rounded border border-slate-800/40">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <span>Delay: {incident.delay_min} mins</span>
                </div>
                <div className="flex items-center space-x-2 bg-slate-900/30 p-2.5 rounded border border-slate-800/40">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span>Deployment: {incident.police_deployed} Officers</span>
                </div>
              </div>

              {/* Action Button */}
              <div className="border-t border-slate-800/60 pt-4 flex justify-between items-center text-[10px] text-slate-500 font-bold uppercase">
                <span>Reported: {incident.timestamp ? new Date(incident.timestamp).toLocaleString() : 'N/A'}</span>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleInitiateDispatch(incident)}
                    disabled={actionLoading !== null}
                    className="px-4.5 py-2 bg-police-gold hover:bg-police-gold/90 disabled:opacity-40 text-[#0B132B] font-bold rounded-lg transition-colors flex items-center space-x-1.5"
                  >
                    <Siren className="w-3.5 h-3.5" />
                    <span>Dispatch Alert</span>
                  </button>

                  <button
                    onClick={() => handleResolve(incident.event_id)}
                    disabled={actionLoading !== null}
                    className="px-4.5 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-slate-900 font-black rounded-lg transition-colors flex items-center space-x-1.5"
                  >
                    {actionLoading === incident.event_id ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Mark Resolved</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dispatch Modal Overlay */}
      {activeDispatchIncident && (
        <div className="fixed inset-0 z-50 bg-[#050B14]/80 backdrop-blur-sm flex items-center justify-center p-4 select-none">
          <div className="glass-panel w-full max-w-xl border border-slate-800 rounded-xl p-6 space-y-6 shadow-2xl relative bg-[#0B132B] animate-fade-in">
            {/* Close button */}
            <button
              onClick={() => setActiveDispatchIncident(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 font-bold text-lg"
            >
              ✕
            </button>

            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Siren className="w-4.5 h-4.5 text-police-gold" />
              <span>SMS Proximity Dispatcher</span>
            </h3>

            <div className="space-y-4">
              {resolvingStation ? (
                <div className="py-8 text-center text-slate-400 flex flex-col items-center">
                  <RefreshCw className="w-7 h-7 text-police-gold animate-spin mb-2" />
                  <span className="text-xs font-bold uppercase tracking-wider">Locating nearest police forces...</span>
                </div>
              ) : nearestStation ? (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-[#050B14] p-3 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Station Resolved</span>
                        <span className="text-xs font-extrabold text-slate-200 truncate">{nearestStation.station_name}</span>
                      </div>
                      <MapPin className="w-4.5 h-4.5 text-police-gold opacity-55" />
                    </div>

                    <div className="bg-[#050B14] p-3 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Geodesic Proximity</span>
                        <span className="text-xs font-extrabold text-slate-200">{nearestStation.distance_km.toFixed(2)} km (ETA {nearestStation.eta_minutes} mins)</span>
                      </div>
                      <Phone className="w-4.5 h-4.5 text-police-light opacity-55" />
                    </div>
                  </div>

                  {/* Form parameters */}
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[9px] font-bold text-slate-400 uppercase mb-1.5">Expected Delay</label>
                      <input 
                        type="number" 
                        value={delay} 
                        onChange={(e) => setDelay(Number(e.target.value))}
                        className="w-full bg-[#050B14] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] font-bold text-slate-400 uppercase mb-1.5">Officers Needed</label>
                      <input 
                        type="number" 
                        value={officers} 
                        onChange={(e) => setOfficers(Number(e.target.value))}
                        className="w-full bg-[#050B14] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] font-bold text-slate-400 uppercase mb-1.5">Barricades Needed</label>
                      <input 
                        type="number" 
                        value={barricades} 
                        onChange={(e) => setBarricades(Number(e.target.value))}
                        className="w-full bg-[#050B14] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex justify-between items-center bg-[#050B14] p-4 rounded border border-slate-800">
                    <div>
                      <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Contact Number</span>
                      <span className="text-xs font-extrabold text-slate-200">{nearestStation.phone}</span>
                    </div>
                    <button
                      onClick={handleDispatch}
                      disabled={loadingSend}
                      className="px-5 py-2.5 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center space-x-1.5 shadow-lg shadow-police-gold/15"
                    >
                      {loadingSend ? <RefreshCw className="w-4 h-4 animate-spin" /> : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Transmit SMS Alert</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Twilio Log output */}
                  {dispatchResult && (
                    <div className="space-y-2 animate-fade-in border-t border-slate-800/80 pt-4">
                      <div className="flex items-center justify-between">
                        <span className="text-[9px] font-bold text-slate-400 uppercase">Gateway logs</span>
                        <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[8px] text-emerald-400 font-bold uppercase">SMS Transmitted</span>
                      </div>
                      <div className="bg-slate-950 p-3.5 rounded font-mono text-[9px] text-slate-300 border border-slate-900 leading-relaxed max-h-[140px] overflow-y-auto">
                        <p className="text-slate-500">// Message ID: {dispatchResult.id}</p>
                        <p className="text-slate-500">// Timestamp: {dispatchResult.timestamp}</p>
                        <p className="text-slate-200 mt-2">{dispatchResult.payload}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center text-red-400 font-bold text-xs">
                  ⚠️ Failed to resolve nearest station coordinates.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
