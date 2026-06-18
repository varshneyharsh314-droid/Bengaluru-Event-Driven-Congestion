import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  ShieldAlert, LayoutDashboard, Map, Users, Wrench, RefreshCw, 
  HelpCircle, LogOut, Radio, Clock, Siren, Lock, Mail, ChevronRight, Bell
} from 'lucide-react';
import { authApi } from './services/api';

// Pages Import Placeholder
import Dashboard from './pages/Dashboard';
import CongestionHeatmap from './pages/CongestionHeatmap';
import CrowdIntelligence from './pages/CrowdIntelligence';
import ResourceAllocation from './pages/ResourceAllocation';
import DiversionRecommendation from './pages/DiversionRecommendation';
import PoliceAlerts from './pages/PoliceAlerts';
import TimelineReplay from './pages/TimelineReplay';
import FeedbackCenter from './pages/FeedbackCenter';
import About from './pages/About';
import IncidentCenter from './pages/IncidentCenter';

function Layout({ children, onLogout, user }: { children: React.ReactNode, onLogout: () => void, user: any }) {
  const location = useLocation();
  const [activeAlert, setActiveAlert] = useState<string | null>(null);

  useEffect(() => {
    // Setup real-time WebSocket listener
    const wsUrl = `ws://${window.location.hostname}:8000/api/traffic/ws/alerts`;
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "CRITICAL_TRAFFIC_ALERT") {
          setActiveAlert(payload.data.alert_message);
        }
      } catch (e) {
        console.error("WS parse error:", e);
      }
    };

    return () => socket.close();
  }, []);

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Spatial Heatmap', path: '/heatmap', icon: Map },
    { name: 'Crowd Intelligence', path: '/crowd', icon: Users },
    { name: 'Resource Allocator', path: '/resources', icon: Wrench },
    { name: 'Diversion Recommendation', path: '/diversion', icon: RefreshCw },
    { name: 'Police Dispatcher', path: '/alerts', icon: Siren },
    { name: 'Timeline Replay', path: '/timeline', icon: Clock },
    { name: 'Feedback & Retraining', path: '/feedback', icon: Radio },
    { name: 'Incident Center', path: '/incidents', icon: ShieldAlert },
    { name: 'System Info', path: '/about', icon: HelpCircle },
  ];

  return (
    <div className="flex h-screen bg-[#050B14] overflow-hidden text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-80 bg-[#0B132B] border-r border-slate-800 flex flex-col justify-between select-none">
        <div>
          {/* Logo / Brand */}
          <div className="p-6 border-b border-slate-800 flex items-center space-x-3 bg-gradient-to-r from-police-navy to-police-dark">
            <div className="p-2.5 bg-police-gold/10 border border-police-gold/30 rounded-lg text-police-gold shadow-lg shadow-police-gold/10">
              <Siren className="w-6 h-6 siren-glow" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg tracking-tight text-slate-100 leading-none">AI COMMAND CENTER</h1>
              <span className="text-[10px] text-police-gold font-semibold uppercase tracking-wider">BENGALURU TRAFFIC POLICE</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group ${
                    isActive 
                      ? 'bg-police-gold text-[#0B132B] font-bold shadow-md shadow-police-gold/25' 
                      : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-100'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#0B132B]' : 'text-slate-400 group-hover:text-slate-100'}`} />
                    <span>{item.name}</span>
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform duration-200 ${isActive ? 'rotate-90 text-[#0B132B]' : 'opacity-0 group-hover:opacity-100 text-slate-500'}`} />
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer User Profile */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/30 flex items-center justify-between">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-full bg-police-blue/40 border border-police-blue flex items-center justify-center font-bold text-police-gold shadow-md">
              {user?.officer_badge?.slice(-4) || 'OPS'}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-slate-100 truncate">{user?.email}</p>
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">{user?.role}</p>
            </div>
          </div>
          <button 
            onClick={onLogout}
            title="Log Out Session"
            className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-police-red transition-colors duration-200"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Top Header */}
        <header className="h-20 bg-[#0B132B]/85 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 z-10 select-none">
          <div>
            <h2 className="text-xl font-black tracking-tight text-slate-100">SMART CITY OPERATIONS TERMINAL</h2>
            <p className="text-xs text-slate-400">Operational Dispatch, AI Congestion Analytics & CCTV Vision Calibration</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="px-3.5 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-xs font-semibold flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>GATEWAY ONLINE</span>
            </div>
          </div>
        </header>

        {/* System Broadcast Overlay */}
        {activeAlert && (
          <div className="bg-police-red/15 border-b border-police-red/40 px-8 py-3.5 flex items-center justify-between text-slate-100 text-sm font-semibold select-none glow-red bg-gradient-to-r from-police-red/10 to-transparent">
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5 text-police-red animate-bounce" />
              <span>{activeAlert}</span>
            </div>
            <button 
              onClick={() => setActiveAlert(null)}
              className="text-xs px-2.5 py-1 bg-police-red/30 hover:bg-police-red/50 rounded text-slate-100 font-bold border border-police-red/40 transition-all duration-200"
            >
              Acknowledge
            </button>
          </div>
        )}

        {/* Viewport content */}
        <section className="flex-1 overflow-y-auto p-8 bg-[#050B14] relative">
          {children}
        </section>
      </main>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (user: any) => void }) {
  const [email, setEmail] = useState('admin@bengalurutraffic.gov.in');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    try {
      await authApi.login(formData);
      const user = await authApi.getMe();
      onLogin(user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication credentials rejected.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050B14] flex items-center justify-center p-6 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-police-navy/40 via-police-dark to-[#050B14]">
      <div className="max-w-md w-full glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-2xl glow-blue">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-police-gold/10 border border-police-gold/30 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg text-police-gold shadow-police-gold/10">
            <Siren className="w-9 h-9 siren-glow" />
          </div>
          <h2 className="text-2xl font-black tracking-tight text-slate-100">BENGALURU TRAFFIC</h2>
          <p className="text-xs text-police-gold uppercase font-bold tracking-wider">AI Command Center Portal</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-police-red/10 border border-police-red/30 rounded-lg flex items-center space-x-3 text-police-red text-sm">
            <Lock className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Operational Email</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg pl-11 pr-4 py-3 text-slate-100 text-sm focus:border-police-gold/50 focus:outline-none focus:ring-1 focus:ring-police-gold/50 transition-colors duration-200"
                placeholder="E.g., admin@bengalurutraffic.gov.in"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Control Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg pl-11 pr-4 py-3 text-slate-100 text-sm focus:border-police-gold/50 focus:outline-none focus:ring-1 focus:ring-police-gold/50 transition-colors duration-200"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold rounded-lg text-sm transition-all duration-200 shadow-lg shadow-police-gold/10 flex items-center justify-center space-x-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <span>ACCESS SECURE TERMINAL</span>
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center pt-6 border-t border-slate-800/40">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Authorized Operational Command Personnel Only</p>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [initFinished, setInitFinished] = useState(false);

  useEffect(() => {
    // Check if token exists to resume session
    const resumeSession = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const fetchedUser = await authApi.getMe();
          setUser(fetchedUser);
        } catch (e) {
          authApi.logout();
        }
      }
      setInitFinished(true);
    };
    resumeSession();
  }, []);

  const handleLogout = () => {
    authApi.logout();
    setUser(null);
  };

  if (!initFinished) {
    return (
      <div className="min-h-screen bg-[#050B14] flex items-center justify-center">
        <RefreshCw className="w-10 h-10 text-police-gold animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <Router>
      <Layout onLogout={handleLogout} user={user}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/heatmap" element={<CongestionHeatmap />} />
          <Route path="/crowd" element={<CrowdIntelligence />} />
          <Route path="/resources" element={<ResourceAllocation />} />
          <Route path="/diversion" element={<DiversionRecommendation />} />
          <Route path="/alerts" element={<PoliceAlerts />} />
          <Route path="/timeline" element={<TimelineReplay />} />
          <Route path="/feedback" element={<FeedbackCenter />} />
          <Route path="/incidents" element={<IncidentCenter />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Layout>
    </Router>
  );
}
