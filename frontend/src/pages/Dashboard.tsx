import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { trafficApi } from '../services/api';
import { LayoutDashboard, ShieldAlert, Users, Clock, Siren, ChevronRight } from 'lucide-react';

export default function Dashboard() {
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        // Load active database incidents first
        const activeDbEvents = await trafficApi.getActiveIncidents();
        
        // Load timeline backup logs
        const fallbackEvents = await trafficApi.getTimeline();
        
        // Merge: place database active events at the top, and append fallback events
        const merged = [...activeDbEvents, ...fallbackEvents];
        setTimelineEvents(merged.slice(0, 15));
      } catch (e) {
        console.error("Failed to load dashboard logs, using fallback:", e);
        try {
          const fallbackEvents = await trafficApi.getTimeline();
          setTimelineEvents(fallbackEvents.slice(0, 15));
        } catch (err) {
          console.error("Timeline query fallback failed:", err);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, []);

  const totalIncidents = timelineEvents.length;
  const highSeverityCount = timelineEvents.filter(e => e.congestion_level === 'High').length;
  const averageDelay = totalIncidents > 0 
    ? Math.round(timelineEvents.reduce((acc, curr) => acc + curr.delay_min, 0) / totalIncidents) 
    : 0;
  const policeDeployed = timelineEvents.reduce((acc, curr) => acc + curr.police_deployed, 0);

  const stats = [
    { name: 'Total Incidents Logged', value: totalIncidents, desc: 'Current active junctions monitor', icon: LayoutDashboard, border: 'border-l-blue-500' },
    { name: 'Critical Gridlocks', value: highSeverityCount, desc: 'High-severity zones active', icon: ShieldAlert, border: 'border-l-red-500', color: 'text-police-red' },
    { name: 'Average Delay Time', value: `${averageDelay} mins`, desc: 'Average queue wait duration', icon: Clock, border: 'border-l-amber-500' },
    { name: 'Police Mobilized', value: `${policeDeployed} officers`, desc: 'Active dispatch forces count', icon: Siren, border: 'border-l-emerald-500' }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-black tracking-tight">OPERATIONAL OVERVIEW</h1>
        <p className="text-sm text-slate-400">Command Control status panel for city junctions.</p>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className={`glass-panel border-l-4 ${stat.border} p-6 rounded-xl flex items-center justify-between`}>
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">{stat.name}</p>
                <h3 className={`text-3xl font-extrabold tracking-tight ${stat.color || 'text-slate-100'}`}>{stat.value}</h3>
                <p className="text-[11px] text-slate-400 mt-2">{stat.desc}</p>
              </div>
              <div className="p-3 bg-slate-800/50 rounded-lg text-slate-400 border border-slate-700/30">
                <Icon className="w-5 h-5 text-slate-300" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Layout panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left main: Active logs */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h3 className="font-extrabold text-lg text-slate-100 uppercase tracking-tight">Active Incident Feeds</h3>
            <span className="px-2.5 py-1 bg-police-gold/10 border border-police-gold/30 rounded text-[10px] text-police-gold font-bold uppercase">LIVE FEED</span>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center"><Clock className="w-8 h-8 animate-spin text-police-gold" /></div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800/80 text-[10px] uppercase text-slate-400 font-extrabold tracking-wider">
                    <th className="pb-3">Incident ID</th>
                    <th className="pb-3">Junction</th>
                    <th className="pb-3">Severity</th>
                    <th className="pb-3">Expected Delay</th>
                    <th className="pb-3">Dispatch</th>
                    <th className="pb-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-sm">
                  {timelineEvents.map((ev) => (
                    <tr key={ev.event_id} className="hover:bg-slate-800/20 transition-colors duration-150">
                      <td className="py-3.5 font-mono text-xs font-bold text-slate-400">{ev.event_id}</td>
                      <td className="py-3.5 text-slate-100 font-semibold">{ev.junction}</td>
                      <td className="py-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          ev.congestion_level === 'High' 
                            ? 'bg-red-500/10 border-red-500/30 text-police-red' 
                            : ev.congestion_level === 'Medium' 
                            ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' 
                            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        }`}>
                          {ev.congestion_level}
                        </span>
                      </td>
                      <td className="py-3.5 text-slate-200">{ev.delay_min} mins</td>
                      <td className="py-3.5 text-slate-300 font-medium">{ev.police_deployed} Officers</td>
                      <td className="py-3.5">
                        <Link 
                          to="/alerts" 
                          className="text-xs text-police-gold hover:underline font-bold flex items-center space-x-1"
                        >
                          <span>Dispatch</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right column: Action Guides */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-lg text-slate-100 uppercase tracking-tight border-b border-slate-800 pb-4">Tactical Response Protocol</h3>
          <div className="space-y-4">
            <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
              <h4 className="font-bold text-xs text-police-gold uppercase tracking-wider mb-1">Level 3 Gridlock Protocol</h4>
              <p className="text-xs text-slate-400">For "High" severity events, deploy a minimum of 8 personnel and set up cordons upstream. Adjust signals immediately.</p>
            </div>
            <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
              <h4 className="font-bold text-xs text-police-red uppercase tracking-wider mb-1">Emergency Corridor Command</h4>
              <p className="text-xs text-slate-400">Prioritize corridors holding ambulances. Reroute surrounding flow to auxiliary collector loops.</p>
            </div>
            <div className="p-4 bg-slate-800/30 border border-slate-700/30 rounded-lg">
              <h4 className="font-bold text-xs text-emerald-400 uppercase tracking-wider mb-1">Closed-Loop retrain guidelines</h4>
              <p className="text-xs text-slate-400">Execute ML retraining at the Retraining Center weekly, ensuring model accuracy stays above 90%.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
