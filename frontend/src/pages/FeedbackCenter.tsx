import React, { useState, useEffect } from 'react';
import { trafficApi, authApi } from '../services/api';
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
  
  // MLOps calibration progress state
  const [feedbackCount, setFeedbackCount] = useState<number>(0);

  const fetchFeedbackCount = async () => {
    try {
      const data = await trafficApi.getFeedbackCount();
      setFeedbackCount(data.count || 0);
    } catch (err) {
      console.error("Failed to query feedback record count:", err);
    }
  };

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const u = await authApi.getMe();
        if (u && u.officer_badge) {
          setBadge(u.officer_badge);
        }
      } catch (e) {
        console.error("Failed to retrieve current user badge ID:", e);
      }
    };
    fetchUser();
    fetchFeedbackCount();
  }, []);

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
      // Auto pre-fill new event template
      setEventId(`EV-2026-${Math.floor(100 + Math.random() * 900)}`);
      setComments('');
      await fetchFeedbackCount();
    } catch (err) {
      console.error(err);
      alert("Failed to log feedback ticket.");
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
      await fetchFeedbackCount();
    } catch (err: any) {
      setRetrainError(err.response?.data?.detail || 'Inference calibration failed.');
    } finally {
      setLoadingRetraining(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      <div>
        <h1 className="text-3xl font-black tracking-tight uppercase">TACTICAL FEEDBACK & CALIBRATION CENTER</h1>
        <p className="text-sm text-slate-400">Log actual incident metrics reported by ground units to calibrate and retrain ML pipelines.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Form: Log Ground Truth */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6 flex flex-col justify-between">
          <div className="space-y-5">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Radio className="w-4.5 h-4.5 text-police-gold" />
              <span>Incident Ticket Feedback</span>
            </h3>

            {feedbackSuccess && (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-lg flex items-center space-x-2 animate-fade-in">
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
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Officer Badge ID</label>
                  <input 
                    type="text" 
                    required
                    value={badge}
                    onChange={(e) => setBadge(e.target.value)}
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none transition-colors"
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
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Actual Congestion</label>
                  <select 
                    value={congestion}
                    onChange={(e) => setCongestion(e.target.value)}
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none transition-colors"
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
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none transition-colors"
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
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:border-police-gold/50 focus:outline-none resize-none transition-colors"
                  placeholder="Enter dispatch notes or traffic resolution remarks..."
                />
              </div>

              <button
                type="submit"
                disabled={loadingFeedback}
                className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2 shadow-lg shadow-police-gold/15"
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
        </div>

        {/* Right Panel: Model Retraining */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6 flex flex-col justify-between">
          <div className="space-y-6">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center space-x-2">
              <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" style={{ animationDuration: '6s' }} />
              <span>Self-Learning Calibration Pipeline</span>
            </h3>

            <p className="text-xs text-slate-400 leading-relaxed font-semibold">
              Once enough feedback records (at least 10) are collected, trigger the XGBoost calibration model. 
              The system fits predictions using closed-loop actual parameters.
            </p>

            {/* Database Log Calibration Progress Tracker */}
            <div className="bg-[#050B14] p-4 rounded-lg border border-slate-800/80 space-y-3 shadow-inner">
              <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                <span>Ground Truth Calibration Logs</span>
                <span className={feedbackCount >= 10 ? 'text-emerald-400' : 'text-police-gold animate-pulse'}>
                  {feedbackCount} / 10 Active
                </span>
              </div>
              
              <div className="w-full h-2 bg-slate-950 border border-slate-900 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    feedbackCount >= 10 
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_8px_#10b981]' 
                      : 'bg-gradient-to-r from-police-gold to-amber-500 shadow-[0_0_6px_#dcba55]'
                  }`}
                  style={{ width: `${Math.min(100, (feedbackCount / 10) * 100)}%` }}
                />
              </div>
              
              {feedbackCount < 10 ? (
                <p className="text-[10px] text-amber-500/85 leading-relaxed font-semibold flex items-center gap-1.5 select-none">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>Need {10 - feedbackCount} more ground-truth entries to execute. Clear incidents on the Incident Center page.</span>
                </p>
              ) : (
                <p className="text-[10px] text-emerald-400/85 leading-relaxed font-semibold flex items-center gap-1.5 select-none">
                  <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>Retraining queue satisfied. XGBoost calibration ready.</span>
                </p>
              )}
            </div>

            <button
              onClick={handleRetrain}
              disabled={loadingRetraining}
              className={`w-full py-3.5 text-xs font-bold uppercase tracking-wider rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 border ${
                feedbackCount >= 10
                  ? 'bg-emerald-500 text-slate-950 border-emerald-500 hover:bg-emerald-600 shadow-lg shadow-emerald-500/10'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200 cursor-not-allowed'
              }`}
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
              <div className="space-y-6 animate-fade-in border-t border-slate-800 pt-5">
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center space-x-2.5 text-emerald-400 text-xs font-bold shadow-lg shadow-emerald-500/5">
                  <ShieldCheck className="w-5 h-5" />
                  <span>Calibration finished. Model weights updated.</span>
                </div>

                <div className="space-y-5">
                  {/* Dataset Size Card */}
                  <div className="bg-slate-900/30 p-4 rounded-lg border border-slate-800 flex items-center justify-between">
                    <div>
                      <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Calibration Dataset Size</span>
                      <span className="text-sm font-black text-slate-200">{retrainResult.dataset_size} ground truth logs</span>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                  </div>

                  {/* Accuracy Gauge */}
                  <div className="bg-slate-900/30 p-4 rounded-lg border border-slate-800 space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">F1 Prediction Accuracy</span>
                      <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[9px] text-emerald-400 font-bold uppercase">
                        +{((retrainResult.new_accuracy - retrainResult.old_accuracy) * 100).toFixed(0)}% Boost
                      </span>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Pre */}
                      <div>
                        <div className="flex justify-between text-[9px] text-slate-400 font-bold mb-1">
                          <span>Pre-Calibration accuracy</span>
                          <span>{(retrainResult.old_accuracy * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                          <div 
                            className="h-full bg-red-500/80 rounded-full transition-all duration-500"
                            style={{ width: `${retrainResult.old_accuracy * 100}%` }}
                          />
                        </div>
                      </div>
                      {/* Post */}
                      <div>
                        <div className="flex justify-between text-[9px] text-slate-300 font-bold mb-1">
                          <span>Post-Calibration accuracy</span>
                          <span className="text-emerald-400">{(retrainResult.new_accuracy * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-850 shadow-[0_0_8px_rgba(16,185,129,0.1)]">
                          <div 
                            className="h-full bg-emerald-500 rounded-full animate-pulse transition-all duration-500"
                            style={{ width: `${retrainResult.new_accuracy * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* MAE Gauge */}
                  <div className="bg-slate-900/30 p-4 rounded-lg border border-slate-800 space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Mean Absolute Error (MAE)</span>
                      <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[9px] text-emerald-400 font-bold uppercase">
                        -{(retrainResult.old_mae - retrainResult.new_mae).toFixed(1)} mins delay variance
                      </span>
                    </div>

                    <div className="space-y-3">
                      {/* Pre */}
                      <div>
                        <div className="flex justify-between text-[9px] text-slate-400 font-bold mb-1">
                          <span>Pre-Calibration variance (lower is better)</span>
                          <span>{retrainResult.old_mae} mins</span>
                        </div>
                        <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                          <div 
                            className="h-full bg-red-500/80 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, (retrainResult.old_mae / 30) * 100)}%` }}
                          />
                        </div>
                      </div>
                      {/* Post */}
                      <div>
                        <div className="flex justify-between text-[9px] text-slate-300 font-bold mb-1">
                          <span>Post-Calibration variance (lower is better)</span>
                          <span className="text-emerald-400">{retrainResult.new_mae} mins</span>
                        </div>
                        <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                          <div 
                            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, (retrainResult.new_mae / 30) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
