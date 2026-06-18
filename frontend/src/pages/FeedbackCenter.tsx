import React, { useState } from 'react';
import { trafficApi } from '../services/api';
import { Radio, RefreshCw, Send, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function FeedbackCenter() {
  const [eventId, setEventId] = useState('EV-2026-001');
  const [badge, setBadge] = useState('KA-POL-8124');
  const [delay, setDelay] = useState(45);
  const [congestion, setCongestion] = useState('Medium');
  const [outcome, setOutcome] = useState('Cleared with Diversion');
  const [comments, setComments] = useState('');

  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [loadingRetraining, setLoadingRetraining] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [retrainResult, setRetrainResult] = useState<any | null>(null);
  const [retrainError, setRetrainError] = useState<string | null>(null);

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingFeedback(true);
    setFeedbackSuccess(false);
    try {
      const payload = {
        event_id: eventId,
        officer_badge: badge,
        actual_delay_min: Number(delay),
        actual_congestion: congestion,
        event_outcome: outcome,
        comments
      };
      await trafficApi.submitFeedback(payload);
      setFeedbackSuccess(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingFeedback(false);
    }
  };

  const handleRetrain = async () => {
    setLoadingRetraining(true);
    setRetrainResult(null);
    setRetrainError(null);
    try {
      const res = await trafficApi.executeRetraining();
      setRetrainResult(res);
    } catch (err: any) {
      setRetrainError(err.response?.data?.detail || 'Inference calibration failed.');
    } finally {
      setLoadingRetraining(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">TACTICAL FEEDBACK & CALIBRATION CENTER</h1>
        <p className="text-sm text-slate-400">Log actual incident metrics reported by ground units to calibrate and retrain ML pipelines.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Form: Log Ground Truth */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Radio className="w-4.5 h-4.5 text-police-gold" />
            <span>Incident Ticket Feedback</span>
          </h3>

          {feedbackSuccess && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-lg flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
              <span>Tactical feedback log successfully processed in database. Status cleared.</span>
            </div>
          )}

          <form onSubmit={handleSubmitFeedback} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Ticket ID</label>
                <input 
                  type="text" 
                  required
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Officer Badge ID</label>
                <input 
                  type="text" 
                  required
                  value={badge}
                  onChange={(e) => setBadge(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Actual Delay (Mins)</label>
                <input 
                  type="number" 
                  required
                  value={delay}
                  onChange={(e) => setDelay(Number(e.target.value))}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Actual Congestion</label>
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
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Outcome</label>
              <select 
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="Normal Clearance">Normal Clearance</option>
                <option value="Cleared with Diversion">Cleared with Diversion</option>
                <option value="Resolved with Extra Forces">Resolved with Extra Forces</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Operator Notes / Comments</label>
              <textarea 
                rows={3}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none resize-none"
                placeholder="Enter dispatch notes or traffic resolution remarks..."
              />
            </div>

            <button
              type="submit"
              disabled={loadingFeedback}
              className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {loadingFeedback ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Ground Truth Log</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Panel: Model Retraining */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
          <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" style={{ animationDuration: '6s' }} />
            <span>Self-Learning Calibration Pipeline</span>
          </h3>

          <p className="text-xs text-slate-400">
            Once enough feedback records (at least 10) are collected, trigger the XGBoost calibration model. 
            The system fits predictions using closed-loop actual parameters.
          </p>

          <button
            onClick={handleRetrain}
            disabled={loadingRetraining}
            className="w-full py-3.5 bg-slate-900 border border-slate-800 hover:border-police-gold/50 text-slate-200 font-bold text-xs uppercase tracking-wider rounded-lg transition-all flex items-center justify-center space-x-2"
          >
            {loadingRetraining ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <span>Trigger Model Calibration</span>}
          </button>

          {retrainError && (
            <div className="p-4 bg-police-red/10 border border-police-red/30 rounded-lg flex items-center space-x-3 text-police-red text-xs">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{retrainError}</span>
            </div>
          )}

          {retrainResult && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center space-x-2.5 text-emerald-400 text-xs font-bold shadow-lg shadow-emerald-500/5">
                <ShieldCheck className="w-5 h-5" />
                <span>Calibration finished. Model weights updated.</span>
              </div>

              <div className="overflow-hidden border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-900/40 text-[10px] text-slate-400 uppercase font-bold tracking-wider border-b border-slate-800">
                      <th className="p-3">Performance Metric</th>
                      <th className="p-3">Pre-Calibration</th>
                      <th className="p-3">Post-Calibration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    <tr>
                      <td className="p-3 font-semibold">Dataset Size</td>
                      <td className="p-3 font-mono" colSpan={2}>{retrainResult.dataset_size} logs</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-semibold">F1 Accuracy</td>
                      <td className="p-3 font-mono text-police-red">{(retrainResult.old_accuracy * 100).toFixed(0)}%</td>
                      <td className="p-3 font-mono text-emerald-400 font-bold">{(retrainResult.new_accuracy * 100).toFixed(0)}%</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-semibold">Mean Absolute Error (MAE)</td>
                      <td className="p-3 font-mono text-police-red">{retrainResult.old_mae} mins</td>
                      <td className="p-3 font-mono text-emerald-400 font-bold">{retrainResult.new_mae} mins</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
