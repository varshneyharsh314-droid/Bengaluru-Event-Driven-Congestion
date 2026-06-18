import React, { useState } from 'react';
import { ShieldCheck, Siren, Sliders, Settings2, Tv } from 'lucide-react';

export default function ResourceAllocation() {
  const [congestion, setCongestion] = useState('High');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);

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

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">RESOURCE ALLOCATION OPTIMIZER</h1>
        <p className="text-sm text-slate-400">Determine appropriate officer units and blockades based on tactical constraints.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Parameters Form */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Settings2 className="w-4.5 h-4.5 text-police-gold" />
            <span>Optimization Parameters</span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Congestion Level</label>
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

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Requires Cordon / Closure</label>
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
        </div>

        {/* Right Side: Deployment Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-blue">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Officer Personnel</span>
                <span className="text-2xl font-black text-slate-100">{police} Officers</span>
                <p className="text-[9px] text-slate-500 mt-2">Active field dispatch units</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-police-light border border-slate-700/30">
                <Siren className="w-6 h-6" />
              </div>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-gold">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Barricades</span>
                <span className="text-2xl font-black text-slate-100">{barricades} Units</span>
                <p className="text-[9px] text-slate-500 mt-2">Cordon bypass blockades</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-police-gold border border-slate-700/30">
                <ShieldCheck className="w-6 h-6" />
              </div>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex items-center justify-between shadow-lg glow-blue">
              <div>
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">VMS Boards</span>
                <span className="text-2xl font-black text-slate-100">{vms} Boards</span>
                <p className="text-[9px] text-slate-500 mt-2">Variable sign boards</p>
              </div>
              <div className="p-3 bg-slate-800/40 rounded-xl text-emerald-400 border border-slate-700/30">
                <Tv className="w-6 h-6" />
              </div>
            </div>
          </div>

          {/* Allocation Details */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-slate-400" />
              <span>Cordon Deployment Plan</span>
            </h3>
            <p className="text-xs text-slate-400">
              The allocation parameters recommend mobilizing {police} officers to the respective junction points. 
              {closure && " Since a cordon/road closure is requested, the barricades should be positioned 100 meters upstream from the main gridlock nodes."}
              {" VMS (Variable Message Sign) boards should be placed at adjacent intersections to warn oncoming commuters and direct traffic along recommended routes."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
