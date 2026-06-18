import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { trafficApi } from '../services/api';
import { Play, Pause, Clock, AlertTriangle, RefreshCw } from 'lucide-react';

export default function TimelineReplay() {
  const [selectedHour, setSelectedHour] = useState(16);
  const [isPlaying, setIsPlaying] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const timerRef = useRef<any>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const result = await trafficApi.getTimeline();
        setEvents(result);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  // Handle auto playback loop
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setSelectedHour((prevHour) => {
          if (prevHour >= 20) {
            return 16;
          }
          return prevHour + 1;
        });
      }, 2000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isPlaying]);

  // Filter events active at selectedHour
  const activeEvents = events.filter(e => {
    return selectedHour >= e.start_hour && selectedHour <= e.end_hour;
  });

  const getSeverityColor = (level: string) => {
    if (level === 'High') return '#ef4444';
    if (level === 'Medium') return '#f59e0b';
    return '#10b981';
  };

  const getFormatTime = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour;
    return `${displayHour}:00 ${period}`;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">SPATIO-TEMPORAL TIMELINE REPLAY</h1>
        <p className="text-sm text-slate-400">Replay historic gridlock sequences during peak traffic hours (4 PM - 8 PM).</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        {/* Left Control Panel */}
        <div className="xl:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Clock className="w-4.5 h-4.5 text-police-gold" />
              <span>Time Control Center</span>
            </h3>

            {/* Slider */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Operational Target Time</span>
                <span className="text-lg font-extrabold text-police-gold">{getFormatTime(selectedHour)}</span>
              </div>
              
              <input 
                type="range" 
                min="16" max="20"
                value={selectedHour}
                onChange={(e) => {
                  setSelectedHour(Number(e.target.value));
                  setIsPlaying(false);
                }}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-police-gold"
              />

              <div className="flex justify-between text-[10px] text-slate-500 font-bold uppercase">
                <span>04:00 PM</span>
                <span>05:00 PM</span>
                <span>06:00 PM</span>
                <span>07:00 PM</span>
                <span>08:00 PM</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-4">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`flex-1 py-3 font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2 ${
                  isPlaying ? 'bg-police-red/25 border border-police-red/40 text-slate-200' : 'bg-police-gold text-[#0B132B]'
                }`}
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-4 h-4" />
                    <span>Pause Playback</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Start Auto Replay</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Active Gridlocks Feed */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 max-h-[300px] overflow-y-auto">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">
              Active Gridlocks ({activeEvents.length})
            </h3>
            {loading ? (
              <div className="py-8 flex justify-center"><RefreshCw className="w-6 h-6 animate-spin text-police-gold" /></div>
            ) : activeEvents.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">No active gridlocks recorded for this time segment.</p>
            ) : (
              <div className="space-y-2.5">
                {activeEvents.map(ev => (
                  <div key={ev.event_id} className="p-3 bg-slate-900/40 border border-slate-800 rounded flex items-center justify-between text-xs">
                    <div>
                      <h4 className="font-bold text-slate-200">{ev.junction}</h4>
                      <p className="text-[10px] text-slate-500">Delay: {ev.delay_min} mins | Deployed: {ev.police_deployed} Officers</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold border" style={{
                      borderColor: `${getSeverityColor(ev.congestion_level)}40`,
                      color: getSeverityColor(ev.congestion_level),
                      backgroundColor: `${getSeverityColor(ev.congestion_level)}10`
                    }}>{ev.congestion_level}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Map Panel */}
        <div className="xl:col-span-3 h-[600px] glass-panel rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
          <MapContainer center={[12.9234, 77.6412]} zoom={13} scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {activeEvents.map(ev => (
              <CircleMarker
                key={ev.event_id}
                center={[ev.latitude, ev.longitude]}
                radius={ev.congestion_level === 'High' ? 18 : ev.congestion_level === 'Medium' ? 12 : 8}
                pathOptions={{
                  color: getSeverityColor(ev.congestion_level),
                  fillColor: getSeverityColor(ev.congestion_level),
                  fillOpacity: 0.35,
                  weight: 2
                }}
              >
                <Popup>
                  <div className="p-1 text-slate-900">
                    <h4 className="font-extrabold text-sm">{ev.junction}</h4>
                    <p className="text-xs mt-1"><strong>Severity:</strong> {ev.congestion_level}</p>
                    <p className="text-xs"><strong>Delay:</strong> {ev.delay_min} mins</p>
                    <p className="text-xs"><strong>Force Deployed:</strong> {ev.police_deployed} officers</p>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
