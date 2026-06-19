import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  ShieldAlert, LayoutDashboard, Map, Users, Wrench, RefreshCw, 
  HelpCircle, LogOut, Radio, Clock, Siren, Lock, Mail, ChevronRight, Bell, CheckCircle
} from 'lucide-react';
import { authApi, getWsUrl } from './services/api';

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
import CitizenDashboard from './pages/CitizenDashboard';

function Layout({ children, onLogout, user }: { children: React.ReactNode, onLogout: () => void, user: any }) {
  const location = useLocation();
  const [activeAlert, setActiveAlert] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (user?.role === 'citizen') return;
    const wsUrl = getWsUrl('/traffic/ws/alerts');
    const socket = new WebSocket(wsUrl);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "CRITICAL_TRAFFIC_ALERT") {
          setActiveAlert(payload.data.alert_message);
        } else if (payload.event === "DISPATCH_UPDATE") {
          setActiveAlert(payload.data.alert_message);
        }
      } catch (e) {
        console.error("WS parse error:", e);
      }
    };
    return () => socket.close();
  }, [user]);

  const menuItems = user?.role === 'citizen'
    ? [
        { name: 'Citizen Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'System Info', path: '/about', icon: HelpCircle },
      ]
    : [
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

  const isCitizen = user?.role === 'citizen';

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div>
        {/* Logo / Brand */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-police-navy to-police-dark">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="p-2.5 bg-police-gold/10 border border-police-gold/30 rounded-lg text-police-gold shadow-lg shadow-police-gold/10 flex-shrink-0">
              <Siren className="w-6 h-6 siren-glow" />
            </div>
            <div className="min-w-0">
              <h1 className="font-extrabold text-base tracking-tight text-slate-100 leading-none truncate">
                {isCitizen ? "CITIZEN PORTAL" : "AI COMMAND CENTER"}
              </h1>
              <span className="text-[10px] text-police-gold font-semibold uppercase tracking-wider">BTP OPERATIONS</span>
            </div>
          </div>
          {/* Collapse toggle (desktop only) */}
          <button
            onClick={() => setSidebarCollapsed(true)}
            className="hidden lg:block p-1.5 hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 rounded transition-colors"
            title="Collapse Sidebar"
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-police-gold text-[#0B132B] font-bold shadow-md shadow-police-gold/25'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-100'
                }`}
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-[#0B132B]' : 'text-slate-400 group-hover:text-slate-100'}`} />
                  <span className="truncate">{item.name}</span>
                </div>
                <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 transition-transform duration-200 ${isActive ? 'rotate-90 text-[#0B132B]' : 'opacity-0 group-hover:opacity-100 text-slate-500'}`} />
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer User Profile */}
      <div className="mt-auto p-4 border-t border-slate-800 bg-slate-900/30 flex items-center justify-between">
        <div className="flex items-center space-x-3 min-w-0 flex-1">
          <div className="w-9 h-9 rounded-full bg-police-blue/40 border border-police-blue flex items-center justify-center font-bold text-police-gold shadow-md flex-shrink-0 text-xs">
            {user?.officer_badge?.slice(-4) || 'OPS'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-slate-100 truncate">{user?.email}</p>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={onLogout}
          title="Log Out Session"
          className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-police-red transition-colors duration-200 flex-shrink-0"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#050B14] overflow-hidden text-slate-100 font-sans">
      {/* ── MOBILE OVERLAY ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── SIDEBAR (mobile: slide-in overlay, lg: fixed) ── */}
      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-50
          w-72 bg-[#0B132B] border-r border-slate-800
          flex flex-col
          transform transition-all duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          ${sidebarCollapsed ? 'lg:-translate-x-full lg:w-0 lg:opacity-0 lg:pointer-events-none border-r-0' : 'lg:translate-x-0 lg:w-72 lg:opacity-100'}
          lg:flex-shrink-0
        `}
      >
        <SidebarContent />
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="flex-1 flex flex-col overflow-hidden relative min-w-0">
        {/* Top Header */}
        <header className="h-16 sm:h-20 bg-[#0B132B]/85 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-4 sm:px-6 lg:px-8 z-10 select-none gap-3">
          {/* Universal Hamburger Toggle */}
          <button
            onClick={() => {
              if (window.innerWidth >= 1024) {
                setSidebarCollapsed(!sidebarCollapsed);
              } else {
                setSidebarOpen(true);
              }
            }}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-slate-100 hover:bg-slate-700 transition-colors flex-shrink-0"
            aria-label="Toggle menu"
            title="Toggle Navigation Sidebar"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="min-w-0 flex-1">
            <h2 className="text-base sm:text-xl font-black tracking-tight text-slate-100 truncate">
              {isCitizen ? "CITIZEN REPORTING PORTAL" : "SMART CITY OPERATIONS TERMINAL"}
            </h2>
            <p className="text-xs text-slate-400 hidden sm:block truncate">
              {isCitizen
                ? "Upload congestion photos, lock exact GPS locations, and request automated dispatch squads."
                : "Operational Dispatch, AI Congestion Analytics & CCTV Vision Calibration"}
            </p>
          </div>


        </header>

        {/* System Broadcast Overlay */}
        {activeAlert && (
          <div className="bg-police-red/15 border-b border-police-red/40 px-4 sm:px-8 py-3 flex items-center justify-between text-slate-100 text-xs sm:text-sm font-semibold select-none glow-red bg-gradient-to-r from-police-red/10 to-transparent gap-3">
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
              <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-police-red animate-bounce flex-shrink-0" />
              <span className="truncate">{activeAlert}</span>
            </div>
            <button
              onClick={() => setActiveAlert(null)}
              className="text-xs px-2 py-1 bg-police-red/30 hover:bg-police-red/50 rounded text-slate-100 font-bold border border-police-red/40 transition-all duration-200 flex-shrink-0"
            >
              OK
            </button>
          </div>
        )}

        {/* Viewport content */}
        <section className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-[#050B14] relative">
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
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    if (isRegistering) {
      try {
        await authApi.register({
          email,
          password,
          role: 'citizen'
        });
        setSuccessMsg("Registration successful! You can now log in to the Citizen Portal.");
        setIsRegistering(false);
        setEmail(email);
        setPassword('');
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Registration failed. Email might already exist.');
      } finally {
        setLoading(false);
      }
    } else {
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
          <p className="text-xs text-police-gold uppercase font-bold tracking-wider">
            {isRegistering ? "Citizen Registration" : "AI Command & Citizen Portal"}
          </p>
        </div>

        {successMsg && (
          <div className="mb-6 p-4 bg-emerald-950/20 border border-emerald-500/30 rounded-lg flex items-center space-x-3 text-emerald-400 text-sm">
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-police-red/10 border border-police-red/30 rounded-lg flex items-center space-x-3 text-police-red text-sm">
            <Lock className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              {isRegistering ? "Email Address" : "Operational / Citizen Email"}
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#0B132B] border border-slate-800 rounded-lg pl-11 pr-4 py-3 text-slate-100 text-sm focus:border-police-gold/50 focus:outline-none focus:ring-1 focus:ring-police-gold/50 transition-colors duration-200"
                placeholder={isRegistering ? "your.email@gmail.com" : "E.g., admin@bengalurutraffic.gov.in"}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Password</label>
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
                <span>{isRegistering ? "CREATE CITIZEN ACCOUNT" : "ACCESS SECURE PORTAL"}</span>
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegistering(!isRegistering);
              setError(null);
              setSuccessMsg(null);
              setEmail(isRegistering ? 'admin@bengalurutraffic.gov.in' : '');
              setPassword('');
            }}
            className="text-xs text-slate-400 hover:text-police-gold underline font-semibold transition-colors duration-200"
          >
            {isRegistering 
              ? "Already have an account? Sign In" 
              : "Need to report an issue? Sign Up as Citizen"}
          </button>
        </div>

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
          {user?.role === 'citizen' ? (
            <>
              <Route path="/" element={<CitizenDashboard />} />
              <Route path="/about" element={<About />} />
              <Route path="*" element={<CitizenDashboard />} />
            </>
          ) : (
            <>
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
            </>
          )}
        </Routes>
      </Layout>
    </Router>
  );
}
