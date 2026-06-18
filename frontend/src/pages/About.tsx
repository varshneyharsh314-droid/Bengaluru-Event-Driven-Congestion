import React from 'react';
import { HelpCircle, Terminal, Cpu, Database, Network } from 'lucide-react';

export default function About() {
  const specs = [
    { title: 'API Gateway Engine', desc: 'FastAPI Python framework compiling schemas, security filters and ML inference.', icon: Terminal },
    { title: 'Predictive Intelligence', desc: 'XGBoost Congestion forecasting pipeline and adaptive YOLOv8 + SAHI object detection.', icon: Cpu },
    { title: 'Persistent Storage', desc: 'PostgreSQL relational database logging incident tickets, dispatches, and feedback loop audits.', icon: Database },
    { title: 'Routing Topology', desc: 'NetworkX graph-theory algorithm solving A* Search heuristics and Dijkstra bypass links.', icon: Network }
  ];

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-black tracking-tight">SYSTEM STATUS & SPECS</h1>
        <p className="text-sm text-slate-400">Technical specifications and library parameters of the Smart City Traffic Platform.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {specs.map((spec) => {
          const Icon = spec.icon;
          return (
            <div key={spec.title} className="glass-panel p-6 rounded-xl border border-slate-800 flex items-start space-x-4">
              <div className="p-3 bg-slate-850 rounded-lg border border-slate-800 text-police-gold">
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm text-slate-100 uppercase tracking-wider mb-2">{spec.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{spec.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
        <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center space-x-2">
          <HelpCircle className="w-4 h-4 text-slate-400" />
          <span>Operational Credentials</span>
        </h3>
        <div className="text-xs text-slate-400 space-y-2 leading-relaxed">
          <p><strong>System version:</strong> GRID-Bengaluru Traffic Ops v1.0.0 (Production Core)</p>
          <p><strong>Database Status:</strong> PostgreSQL Pool connected on port 5432</p>
          <p><strong>Worker Queue status:</strong> Celery Task Broker mapped to Redis Cache on port 6379</p>
          <p><strong>Developer:</strong> Bengaluru Traffic Police Intelligence Unit (AI Architects Division)</p>
        </div>
      </div>
    </div>
  );
}
