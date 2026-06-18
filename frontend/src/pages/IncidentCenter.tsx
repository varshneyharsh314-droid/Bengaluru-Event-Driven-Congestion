import React, { useState, useEffect } from 'react';
import { trafficApi } from '../services/api';
import { ShieldAlert, CheckCircle2, Clock, MapPin, MessageSquare, RefreshCw, AlertCircle, Activity } from 'lucide-react';

export default function IncidentCenter() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

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
          ))}
        </div>
      )}
    </div>
  );
}
