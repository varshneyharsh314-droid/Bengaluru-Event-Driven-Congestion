import React, { useState, useRef, useEffect, useCallback } from 'react';
import { trafficApi, connectVideoWs } from '../services/api';
import { Users, AlertTriangle, ShieldCheck, Siren, Upload, RefreshCw, Film, Video, Image, BarChart3, TrendingUp, Activity, Construction } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

const createMarkerIcon = (color: string) => {
  return new L.DivIcon({
    html: `<div class="w-6 h-6 bg-${color}-500 border border-slate-900 rounded-full flex items-center justify-center shadow-lg">
             <div class="w-2.5 h-2.5 bg-slate-100 rounded-full"></div>
           </div>`,
    className: 'route-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const goldIcon = createMarkerIcon('amber');
const redIcon = createMarkerIcon('red');
const cyanIcon = createMarkerIcon('cyan');
const blueIcon = createMarkerIcon('blue');

const fetchOSRMRoute = async (coordinates: [number, number][]) => {
  if (coordinates.length < 2) return coordinates;
  try {
    const coordsString = coordinates.map(([lat, lon]) => `${lon},${lat}`).join(';');
    const response = await fetch(`https://router.project-osrm.org/route/v1/driving/${coordsString}?overview=full&geometries=geojson`);
    const data = await response.json();
    if (data.routes && data.routes[0]) {
      return data.routes[0].geometry.coordinates.map(([lon, lat]: [number, number]) => [lat, lon]);
    }
  } catch (error) {
    console.error("OSRM Routing Error:", error);
  }
  return coordinates;
};

type AnalysisMode = 'image' | 'video' | 'simulation';

interface VideoStreamState {
  isStreaming: boolean;
  currentFrame: string | null;
  headcount: number;
  density: string;
  frameIdx: number;
  totalFrames: number;
  fps: number;
  frameCounts: number[];
  peakCount: number;
  summary: any | null;
  barricadesRecommended: number;
  policeRecommended: number;
  updatedCongestion: string;
}

function SparklineChart({ data, width = 400, height = 80 }: { data: number[], width?: number, height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    const maxVal = Math.max(...data, 1);
    const step = width / (data.length - 1);
    const pad = 4;

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(239, 68, 68, 0.35)');
    gradient.addColorStop(1, 'rgba(239, 68, 68, 0.02)');

    ctx.beginPath();
    ctx.moveTo(0, height);
    data.forEach((val, i) => {
      const x = i * step;
      const y = height - pad - ((val / maxVal) * (height - pad * 2));
      if (i === 0) ctx.lineTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo((data.length - 1) * step, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((val, i) => {
      const x = i * step;
      const y = height - pad - ((val / maxVal) * (height - pad * 2));
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Latest point dot
    if (data.length > 0) {
      const lastX = (data.length - 1) * step;
      const lastY = height - pad - ((data[data.length - 1] / maxVal) * (height - pad * 2));
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }, [data, width, height]);

  return <canvas ref={canvasRef} style={{ width, height }} className="rounded" />;
}

export default function CrowdIntelligence() {
  const [mode, setMode] = useState<AnalysisMode>('image');
  const [eventId, setEventId] = useState('EV-2026-001');
  const [baseCongestion, setBaseCongestion] = useState('Medium');
  const [priority, setPriority] = useState('High');
  const [closure, setClosure] = useState(true);

  const [edgeGeometries, setEdgeGeometries] = useState<Record<string, [number, number][]>>({});

  // Simulation mode state
  interface SimCamera {
    id: number;
    fromJunction: string;
    toJunction: string;
    headcount: number;
    videoFile: File | null;
    videoPreviewUrl: string | null;
    isStreaming: boolean;
    currentFrame: string | null;
    frameIdx: number;
    totalFrames: number;
    ws: WebSocket | null;
  }

  const [junctionList, setJunctionList] = useState<any[]>([
    { name: 'SilkBoardJunc', lat: 12.9176, lon: 77.6246 },
    { name: 'HSRLayout14thMain', lat: 12.9172, lon: 77.6366 },
    { name: 'AgaraJunction', lat: 12.9261, lon: 77.6508 },
    { name: 'IbblurJunction', lat: 12.9234, lon: 77.6712 },
    { name: 'BellandurJunction', lat: 12.9366, lon: 77.6830 },
    { name: 'MadiwalaCheckpost', lat: 12.9225, lon: 77.6189 },
    { name: 'KoramangalaWaterTank', lat: 12.9348, lon: 77.6210 },
    { name: 'BTMLayout16thMain', lat: 12.9142, lon: 77.6080 },
    { name: 'HSRLayout27thMain', lat: 12.9110, lon: 77.6475 },
  ]);
  const [edgesList, setEdgesList] = useState<any[]>([
    { source: 'SilkBoardJunc', target: 'HSRLayout14thMain', weight: 4.0, length: 1.5, base_weight: 4.0 },
    { source: 'HSRLayout14thMain', target: 'SilkBoardJunc', weight: 4.0, length: 1.5, base_weight: 4.0 },
    { source: 'HSRLayout14thMain', target: 'AgaraJunction', weight: 3.5, length: 1.3, base_weight: 3.5 },
    { source: 'AgaraJunction', target: 'HSRLayout14thMain', weight: 3.5, length: 1.3, base_weight: 3.5 },
    { source: 'AgaraJunction', target: 'IbblurJunction', weight: 5.0, length: 2.1, base_weight: 5.0 },
    { source: 'IbblurJunction', target: 'AgaraJunction', weight: 5.0, length: 2.1, base_weight: 5.0 },
    { source: 'SilkBoardJunc', target: 'MadiwalaCheckpost', weight: 3.0, length: 1.1, base_weight: 3.0 },
    { source: 'MadiwalaCheckpost', target: 'SilkBoardJunc', weight: 3.0, length: 1.1, base_weight: 3.0 },
    { source: 'MadiwalaCheckpost', target: 'KoramangalaWaterTank', weight: 4.5, length: 1.8, base_weight: 4.5 },
    { source: 'KoramangalaWaterTank', target: 'MadiwalaCheckpost', weight: 4.5, length: 1.8, base_weight: 4.5 },
    { source: 'KoramangalaWaterTank', target: 'AgaraJunction', weight: 6.0, length: 2.4, base_weight: 6.0 },
    { source: 'AgaraJunction', target: 'KoramangalaWaterTank', weight: 6.0, length: 2.4, base_weight: 6.0 },
    { source: 'SilkBoardJunc', target: 'BTMLayout16thMain', weight: 3.5, length: 1.4, base_weight: 3.5 },
    { source: 'BTMLayout16thMain', target: 'SilkBoardJunc', weight: 3.5, length: 1.4, base_weight: 3.5 },
    { source: 'BTMLayout16thMain', target: 'KoramangalaWaterTank', weight: 5.5, length: 2.0, base_weight: 5.5 },
    { source: 'KoramangalaWaterTank', target: 'BTMLayout16thMain', weight: 5.5, length: 2.0, base_weight: 5.5 },
    { source: 'IbblurJunction', target: 'BellandurJunction', weight: 4.0, length: 1.6, base_weight: 4.0 },
    { source: 'BellandurJunction', target: 'IbblurJunction', weight: 4.0, length: 1.6, base_weight: 4.0 },
    { source: 'AgaraJunction', target: 'HSRLayout27thMain', weight: 3.0, length: 1.2, base_weight: 3.0 },
    { source: 'HSRLayout27thMain', target: 'AgaraJunction', weight: 3.0, length: 1.2, base_weight: 3.0 },
    { source: 'HSRLayout27thMain', target: 'IbblurJunction', weight: 3.0, length: 1.1, base_weight: 3.0 },
    { source: 'IbblurJunction', target: 'HSRLayout27thMain', weight: 3.0, length: 1.1, base_weight: 3.0 },
  ]);
  const [simSource, setSimSource] = useState('SilkBoardJunc');
  const [simTarget, setSimTarget] = useState('AgaraJunction');
  const [simAlgorithm, setSimAlgorithm] = useState('astar');
  const [routingResult, setRoutingResult] = useState<any | null>(null);

  const [simCameras, setSimCameras] = useState<SimCamera[]>([
    { id: 1, fromJunction: 'SilkBoardJunc', toJunction: 'HSRLayout14thMain', headcount: 0, videoFile: null, videoPreviewUrl: null, isStreaming: false, currentFrame: null, frameIdx: 0, totalFrames: 0, ws: null },
    { id: 2, fromJunction: 'HSRLayout14thMain', toJunction: 'AgaraJunction', headcount: 0, videoFile: null, videoPreviewUrl: null, isStreaming: false, currentFrame: null, frameIdx: 0, totalFrames: 0, ws: null },
    { id: 3, fromJunction: 'SilkBoardJunc', toJunction: 'MadiwalaCheckpost', headcount: 0, videoFile: null, videoPreviewUrl: null, isStreaming: false, currentFrame: null, frameIdx: 0, totalFrames: 0, ws: null },
    { id: 4, fromJunction: 'MadiwalaCheckpost', toJunction: 'KoramangalaWaterTank', headcount: 0, videoFile: null, videoPreviewUrl: null, isStreaming: false, currentFrame: null, frameIdx: 0, totalFrames: 0, ws: null },
    { id: 5, fromJunction: 'KoramangalaWaterTank', toJunction: 'AgaraJunction', headcount: 0, videoFile: null, videoPreviewUrl: null, isStreaming: false, currentFrame: null, frameIdx: 0, totalFrames: 0, ws: null },
  ]);

  // Load junction/edges catalog when mode is 'simulation'
  useEffect(() => {
    if (mode !== 'simulation') return;
    const loadJunctions = async () => {
      try {
        const res = await trafficApi.getJunctions();
        setJunctionList(res.junctions || []);
        setEdgesList(res.edges || []);
      } catch (err) {
        console.error("Failed to load junctions:", err);
      }
    };
    loadJunctions();
  }, [mode]);

  // Map lat/lon coordinates to 2D canvas coordinates
  const latMin = 12.9100;
  const latMax = 12.9380;
  const lonMin = 77.6000;
  const lonMax = 77.6850;

  const projectCoords = (lat: number, lon: number, width: number, height: number) => {
    const pad = 40;
    const x = pad + ((lon - lonMin) / (lonMax - lonMin)) * (width - pad * 2);
    const y = height - pad - ((lat - latMin) / (latMax - latMin)) * (height - pad * 2);
    return { x, y };
  };

  const getConnectedJunctions = (fromNode: string) => {
    if (!fromNode) return [];
    const connected = edgesList
      .filter(e => e.source === fromNode)
      .map(e => e.target);
    return Array.from(new Set(connected));
  };

  const recalculateRoute = useCallback(async () => {
    if (!simSource || !simTarget) return;
    try {
      const congestion_inputs = simCameras
        .filter(cam => cam.fromJunction && cam.toJunction)
        .map(cam => ({
          source: cam.fromJunction,
          target: cam.toJunction,
          headcount: cam.headcount
        }));

      const res = await trafficApi.getDynamicRoute({
        source: simSource,
        target: simTarget,
        algorithm: simAlgorithm,
        congestion_inputs
      });
      setRoutingResult(res);
    } catch (err) {
      console.error("Failed to recalculate route:", err);
    }
  }, [simSource, simTarget, simAlgorithm, simCameras]);

  // Periodically pull fresh route updates based on simulated edge congestion weights
  useEffect(() => {
    if (mode !== 'simulation') return;
    recalculateRoute();
    const interval = setInterval(() => {
      recalculateRoute();
    }, 1500);
    return () => clearInterval(interval);
  }, [mode, recalculateRoute]);

  useEffect(() => {
    const fetchAllEdgeGeometries = async () => {
      const nodeCoordsLookup: Record<string, [number, number]> = {};
      junctionList.forEach(node => {
        nodeCoordsLookup[node.name] = [node.lat, node.lon];
      });

      const uniqueEdges = edgesList.filter((edge, index, self) =>
        index === self.findIndex((e) => (
          (e.source === edge.source && e.target === edge.target) ||
          (e.source === edge.target && e.target === edge.source)
        ))
      );

      const geometries: Record<string, [number, number][]> = {};

      await Promise.all(uniqueEdges.map(async (edge) => {
        const u = nodeCoordsLookup[edge.source];
        const v = nodeCoordsLookup[edge.target];
        if (!u || !v) return;
        
        const snapped = await fetchOSRMRoute([u, v]);
        const keyForward = `${edge.source}_${edge.target}`;
        const keyBackward = `${edge.target}_${edge.source}`;
        geometries[keyForward] = snapped;
        geometries[keyBackward] = [...snapped].reverse();
      }));

      setEdgeGeometries(geometries);
    };

    if (junctionList.length > 0 && edgesList.length > 0) {
      fetchAllEdgeGeometries();
    }
  }, [junctionList, edgesList]);

  const getOptimalRouteGeometry = (): [number, number][] => {
    const optimalRoute = routingResult?.optimal_route || [];
    if (optimalRoute.length < 2) return [];

    const coords: [number, number][] = [];
    for (let i = 0; i < optimalRoute.length - 1; i++) {
      const key = `${optimalRoute[i]}_${optimalRoute[i+1]}`;
      const edgeGeo = edgeGeometries[key];
      if (edgeGeo) {
        if (coords.length > 0 && edgeGeo.length > 0) {
          coords.push(...edgeGeo.slice(1));
        } else {
          coords.push(...edgeGeo);
        }
      } else {
        const nodeCoordsLookup: Record<string, [number, number]> = {};
        junctionList.forEach(node => {
          nodeCoordsLookup[node.name] = [node.lat, node.lon];
        });
        const u = nodeCoordsLookup[optimalRoute[i]];
        const v = nodeCoordsLookup[optimalRoute[i+1]];
        if (u && v) {
          coords.push(u, v);
        }
      }
    }
    return coords;
  };

  const startCameraWs = async (cameraId: number, file: File) => {
    const existingCam = simCameras.find(c => c.id === cameraId);
    if (existingCam?.ws) {
      existingCam.ws.close();
    }

    setSimCameras(prev => prev.map(c => {
      if (c.id === cameraId) {
        return {
          ...c,
          videoFile: file,
          videoPreviewUrl: URL.createObjectURL(file),
          isStreaming: true,
          currentFrame: null,
          frameIdx: 0,
          totalFrames: 0,
        };
      }
      return c;
    }));

    const socket = connectVideoWs(
      (data) => {
        if (data.event === 'VIDEO_FRAME') {
          setSimCameras(prev => prev.map(cam => {
            if (cam.id === cameraId) {
              return {
                ...cam,
                headcount: data.headcount,
                frameIdx: data.frame_idx,
                totalFrames: data.total_frames,
                currentFrame: data.annotated_frame_base64
                  ? `data:image/jpeg;base64,${data.annotated_frame_base64}`
                  : cam.currentFrame
              };
            }
            return cam;
          }));
        } else if (data.event === 'VIDEO_COMPLETE') {
          setSimCameras(prev => prev.map(cam => {
            if (cam.id === cameraId) {
              return { ...cam, isStreaming: false, ws: null };
            }
            return cam;
          }));
        } else if (data.event === 'ERROR') {
          console.error(`Camera ${cameraId} WS Error:`, data.message);
          setSimCameras(prev => prev.map(cam => {
            if (cam.id === cameraId) {
              return { ...cam, isStreaming: false, ws: null };
            }
            return cam;
          }));
        }
      },
      () => {
        setSimCameras(prev => prev.map(cam => {
          if (cam.id === cameraId) {
            return { ...cam, isStreaming: false, ws: null };
          }
          return cam;
        }));
      },
      () => {
        setSimCameras(prev => prev.map(cam => {
          if (cam.id === cameraId) {
            return { ...cam, isStreaming: false, ws: null };
          }
          return cam;
        }));
      },
      simCameras.find(c => c.id === cameraId)?.fromJunction
    );

    setSimCameras(prev => prev.map(c => {
      if (c.id === cameraId) {
        return { ...c, ws: socket };
      }
      return c;
    }));

    const sendFile = async () => {
      if (socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({ type: 'start', fileName: file.name, fileSize: file.size }));
      const chunkSize = 500 * 1024;
      let offset = 0;
      while (offset < file.size) {
        if (socket.readyState !== WebSocket.OPEN) break;
        const slice = file.slice(offset, offset + chunkSize);
        const buffer = await slice.arrayBuffer();
        socket.send(buffer);
        offset += chunkSize;
        await new Promise(resolve => setTimeout(resolve, 15));
      }
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'end' }));
      }
    };

    if (socket.readyState === WebSocket.OPEN) {
      sendFile();
    } else {
      socket.onopen = sendFile;
    }
  };

  const stopCameraWs = (cameraId: number) => {
    const cam = simCameras.find(c => c.id === cameraId);
    if (cam?.ws) {
      cam.ws.close();
    }
    setSimCameras(prev => prev.map(c => {
      if (c.id === cameraId) {
        return { ...c, isStreaming: false, ws: null };
      }
      return c;
    }));
  };

  const updateCameraHeadcount = (cameraId: number, headcount: number) => {
    setSimCameras(prev => prev.map(c => {
      if (c.id === cameraId) {
        return { ...c, headcount };
      }
      return c;
    }));
  };

  const handleCameraVideoUpload = (cameraId: number, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      startCameraWs(cameraId, e.target.files[0]);
    }
  };

  // Canvas is replaced by Leaflet MapContainer

  // Image mode state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [annotatedUrl, setAnnotatedUrl] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Video mode state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [videoStream, setVideoStream] = useState<VideoStreamState>({
    isStreaming: false,
    currentFrame: null,
    headcount: 0,
    density: 'Low',
    frameIdx: 0,
    totalFrames: 0,
    fps: 0,
    frameCounts: [],
    peakCount: 0,
    summary: null,
    barricadesRecommended: 0,
    policeRecommended: 0,
    updatedCongestion: 'Low',
  });

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // === IMAGE MODE HANDLERS ===
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnnotatedUrl(null);
      setResult(null);
    }
  };

  const handleMockSelector = async (name: string) => {
    setLoading(true);
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, 640, 400);
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '24px Inter';
        ctx.fillText(`CCTV CAMERA: ${name}`, 50, 80);
        ctx.fillText("Surveillance Feed Mock Active", 50, 120);
        ctx.fillStyle = '#dcba55';
        for (let i = 0; i < 45; i++) {
          ctx.beginPath();
          ctx.arc(100 + Math.random() * 400, 160 + Math.random() * 200, 6, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      
      canvas.toBlob(async (blob) => {
        if (blob) {
          const file = new File([blob], `${name.toLowerCase().replace(' ', '_')}_feed.jpg`, { type: 'image/jpeg' });
          setSelectedFile(file);
          setPreviewUrl(URL.createObjectURL(file));
          
          const payload = {
            event_id: eventId,
            base_congestion: baseCongestion,
            priority: priority,
            requires_road_closure: closure,
            file: file
          };
          
          const res = await trafficApi.analyzeCrowd(payload);
          setResult(res);
          if (res.annotated_image_base64) {
            setAnnotatedUrl(`data:image/jpeg;base64,${res.annotated_image_base64}`);
          } else {
            setAnnotatedUrl(previewUrl);
          }
        }
      }, 'image/jpeg');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleImageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    
    setLoading(true);
    try {
      const payload = {
        event_id: eventId,
        base_congestion: baseCongestion,
        priority: priority,
        requires_road_closure: closure,
        file: selectedFile
      };
      
      const res = await trafficApi.analyzeCrowd(payload);
      setResult(res);
      
      if (res.annotated_image_base64) {
        setAnnotatedUrl(`data:image/jpeg;base64,${res.annotated_image_base64}`);
      } else {
        setAnnotatedUrl(previewUrl);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // === VIDEO MODE HANDLERS ===
  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideoFile(file);
      setVideoPreviewUrl(URL.createObjectURL(file));
      setVideoStream(prev => ({ ...prev, summary: null, currentFrame: null, frameCounts: [], peakCount: 0 }));
    }
  };

  const handleVideoAnalysis = useCallback(async () => {
    if (!videoFile) return;

    setLoading(true);
    setVideoStream({
      isStreaming: true,
      currentFrame: null,
      headcount: 0,
      density: 'Low',
      frameIdx: 0,
      totalFrames: 0,
      fps: 0,
      frameCounts: [],
      peakCount: 0,
      summary: null,
      barricadesRecommended: 0,
      policeRecommended: 0,
      updatedCongestion: 'Low',
    });

    const socket = connectVideoWs(
      (data) => {
        if (data.event === 'VIDEO_FRAME') {
          setVideoStream(prev => {
            const newCounts = [...prev.frameCounts, data.headcount];
            // Keep last 200 for sparkline performance
            const trimmedCounts = newCounts.length > 200 ? newCounts.slice(-200) : newCounts;
            return {
              ...prev,
              headcount: data.headcount,
              density: data.density,
              frameIdx: data.frame_idx,
              totalFrames: data.total_frames,
              fps: data.fps,
              frameCounts: trimmedCounts,
              peakCount: Math.max(prev.peakCount, data.headcount),
              currentFrame: data.annotated_frame_base64
                ? `data:image/jpeg;base64,${data.annotated_frame_base64}`
                : prev.currentFrame,
              barricadesRecommended: data.barricades_recommended || 0,
              policeRecommended: data.police_recommended || 0,
              updatedCongestion: data.updated_congestion || 'Low',
            };
          });
        } else if (data.event === 'VIDEO_COMPLETE') {
          setVideoStream(prev => ({
            ...prev,
            isStreaming: false,
            summary: data.summary || null,
          }));
          setLoading(false);
        } else if (data.event === 'ERROR') {
          console.error('Video analysis error:', data.message);
          setVideoStream(prev => ({ ...prev, isStreaming: false }));
          setLoading(false);
        }
      },
      () => {
        setVideoStream(prev => ({ ...prev, isStreaming: false }));
        setLoading(false);
      },
      () => {
        setVideoStream(prev => ({ ...prev, isStreaming: false }));
        setLoading(false);
      }
    );

    wsRef.current = socket;

    // Wait for connection, then send video binary
    const sendVideoFile = async () => {
      if (socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({ type: 'start', fileName: videoFile.name, fileSize: videoFile.size }));
      const chunkSize = 500 * 1024;
      let offset = 0;
      while (offset < videoFile.size) {
        if (socket.readyState !== WebSocket.OPEN) break;
        const slice = videoFile.slice(offset, offset + chunkSize);
        const buffer = await slice.arrayBuffer();
        socket.send(buffer);
        offset += chunkSize;
        await new Promise(resolve => setTimeout(resolve, 15));
      }
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'end' }));
      }
    };

    if (socket.readyState === WebSocket.OPEN) {
      sendVideoFile();
    } else {
      socket.onopen = sendVideoFile;
    }
  }, [videoFile]);

  const progressPct = videoStream.totalFrames > 0
    ? Math.round((videoStream.frameIdx / videoStream.totalFrames) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black tracking-tight">CCTV TRAFFIC & CROWD INTELLIGENCE</h1>
        <p className="text-sm text-slate-400">Process live camera frames or video files using YOLOv8 with SAHI slicing grid calibration for real-time traffic and crowd analysis.</p>
      </div>

      {/* Mode Tabs */}
      <div className="flex space-x-2 select-none">
        <button
          onClick={() => setMode('image')}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
            mode === 'image'
              ? 'bg-police-gold text-[#0B132B] border-police-gold shadow-md shadow-police-gold/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Image className="w-4 h-4" />
          <span>Image Analysis</span>
        </button>
        <button
          onClick={() => setMode('video')}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
            mode === 'video'
              ? 'bg-police-gold text-[#0B132B] border-police-gold shadow-md shadow-police-gold/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Video className="w-4 h-4" />
          <span>Video Analysis</span>
        </button>
        <button
          onClick={() => setMode('simulation')}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
            mode === 'simulation'
              ? 'bg-police-gold text-[#0B132B] border-police-gold shadow-md shadow-police-gold/20'
              : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Dynamic Routing Simulator</span>
        </button>
      </div>

      {/* Preset Camera feeds — Image mode only */}
      {mode === 'image' && (
        <div className="flex flex-wrap gap-4 select-none">
          {['Silk Board Feed 02', 'Hebbal Junction West', 'Peenya Industrial Crossing'].map((feedName) => (
            <button
              key={feedName}
              onClick={() => handleMockSelector(feedName)}
              className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:border-police-gold/50 rounded-lg text-xs font-bold text-slate-300 hover:text-slate-100 flex items-center space-x-2 transition-all duration-200"
            >
              <Film className="w-4 h-4 text-police-gold" />
              <span>Process {feedName}</span>
            </button>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Left Side: Operational Panel */}
        {mode === 'simulation' ? (
          /* Simulation Control Panel */
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Activity className="w-4 h-4 text-police-gold" />
              <span>Simulation Router</span>
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Start Junction</label>
                <select 
                  value={simSource}
                  onChange={(e) => setSimSource(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  {junctionList.map(j => (
                    <option key={j.name} value={j.name}>{j.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Destination Junction</label>
                <select 
                  value={simTarget}
                  onChange={(e) => setSimTarget(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  {junctionList.map(j => (
                    <option key={j.name} value={j.name}>{j.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Routing Algorithm</label>
                <select 
                  value={simAlgorithm}
                  onChange={(e) => setSimAlgorithm(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="astar">A* Search Algorithm</option>
                  <option value="dijkstra">Dijkstra's Shortest Path</option>
                </select>
              </div>

              {routingResult && (
                <div className="border-t border-slate-800 pt-4 space-y-4">
                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-400 uppercase text-[10px] font-bold">Base Time:</span>
                    <span className="text-emerald-400 font-bold">{routingResult.baseline_travel_time?.toFixed(1)} mins</span>
                  </div>

                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-400 uppercase text-[10px] font-bold">Simulated Time:</span>
                    <span className={`font-black text-sm ${
                      routingResult.status === 'gridlock' ? 'text-police-red animate-pulse' :
                      routingResult.status === 'congested' ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {routingResult.estimated_travel_time?.toFixed(1)} mins
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-slate-400 uppercase text-[10px] font-bold">Routing Status:</span>
                    <span className={`text-[10px] uppercase px-2 py-0.5 rounded font-bold border ${
                      routingResult.status === 'gridlock'
                        ? 'bg-red-500/15 text-red-400 border-red-500/20'
                        : routingResult.status === 'congested'
                        ? 'bg-amber-500/15 text-amber-400 border-amber-500/20'
                        : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
                    }`}>
                      {routingResult.status}
                    </span>
                  </div>

                  {routingResult.status === 'gridlock' && (
                    <div className="p-3.5 bg-red-950/40 rounded border border-red-500/35 text-red-300 space-y-2">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        <span className="text-xs font-bold uppercase tracking-wider">Gridlock Warning!</span>
                      </div>
                      <p className="text-[10px] text-red-400 leading-relaxed font-semibold">
                        ⚠️ GRIDLOCK ALERT: No clear alternative route. Both paths heavily congested.
                      </p>
                    </div>
                  )}

                  {/* Calculated path sequence list */}
                  <div className="space-y-2">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase">Computed Path Sequence</span>
                    <div className="bg-[#050B14] p-3 rounded-lg border border-slate-800 max-h-[160px] overflow-y-auto space-y-1.5 scrollbar-thin">
                      {routingResult.optimal_route?.length > 0 ? (
                        routingResult.optimal_route.map((node: string, index: number) => (
                          <div key={node} className="flex items-center space-x-2 text-[10px] font-semibold text-slate-300">
                            <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[8px]">
                              {index + 1}
                            </span>
                            <span className="truncate">{node}</span>
                          </div>
                        ))
                      ) : (
                        <span className="text-[10px] text-red-400 italic">No route reachable</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Left Side: Operational Setup Panel */
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h3 className="font-extrabold text-sm uppercase tracking-wider text-police-gold border-b border-slate-800 pb-3">Operational Setup</h3>
            
            <form onSubmit={mode === 'image' ? handleImageSubmit : (e) => { e.preventDefault(); handleVideoAnalysis(); }} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Event Association</label>
                <input 
                  type="text" 
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Base Congestion</label>
                  <select 
                    value={baseCongestion}
                    onChange={(e) => setBaseCongestion(e.target.value)}
                    className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Priority</label>
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
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Requires Closure</label>
                <select 
                  value={String(closure)}
                  onChange={(e) => setClosure(e.target.value === 'true')}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>

              {/* File Upload Area */}
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2">
                  {mode === 'image' ? 'Upload Camera Frame' : 'Upload CCTV Video'}
                </label>
                <div 
                  onClick={() => mode === 'image' ? fileInputRef.current?.click() : videoInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-800 hover:border-police-gold/50 rounded-xl p-8 text-center cursor-pointer bg-slate-900/20 hover:bg-slate-900/40 transition-all duration-200"
                >
                  {mode === 'image' ? (
                    <>
                      <input 
                        type="file" 
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        accept="image/*"
                        className="hidden" 
                      />
                      <Upload className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                      <p className="text-xs text-slate-300 font-semibold mb-1">Click to select CCTV image</p>
                      <p className="text-[10px] text-slate-500">Supports PNG, JPG, JPEG up to 10MB</p>
                    </>
                  ) : (
                    <>
                      <input 
                        type="file" 
                        ref={videoInputRef}
                        onChange={handleVideoChange}
                        accept="video/*"
                        className="hidden" 
                      />
                      <Video className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                      <p className="text-xs text-slate-300 font-semibold mb-1">Click to select CCTV video</p>
                      <p className="text-[10px] text-slate-500">Supports MP4, AVI, MOV up to 100MB</p>
                    </>
                  )}
                </div>
              </div>

              {/* Selected file info */}
              {mode === 'image' && selectedFile && (
                <div className="text-xs text-slate-400 truncate font-semibold bg-slate-800/40 p-2.5 rounded border border-slate-700/30 flex items-center justify-between">
                  <span>Selected: {selectedFile.name}</span>
                  <span className="text-[10px] bg-police-gold/15 text-police-gold px-1.5 py-0.5 rounded border border-police-gold/20">Ready</span>
                </div>
              )}
              {mode === 'video' && videoFile && (
                <div className="text-xs text-slate-400 truncate font-semibold bg-slate-800/40 p-2.5 rounded border border-slate-700/30 flex items-center justify-between">
                  <span>Video: {videoFile.name} ({(videoFile.size / (1024 * 1024)).toFixed(1)} MB)</span>
                  <span className="text-[10px] bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">Ready</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || (mode === 'image' ? !selectedFile : !videoFile)}
                className="w-full py-3 bg-police-gold hover:bg-police-gold/90 text-[#0B132B] font-bold text-xs uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="w-4.5 h-4.5 animate-spin" />
                ) : (
                  <span>{mode === 'image' ? 'Start SAHI Calibration' : 'Start Video Analysis'}</span>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Right Side: Visual Feed & Analytics */}
        <div className="xl:col-span-2 space-y-6">
          {/* === SIMULATION MODE CONTENT === */}
          {mode === 'simulation' && (
            <>
              {/* Interactive Traffic Map Graph */}
              <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 bg-[#0a0f1d]">
                <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-[#00ffff] animate-pulse" />
                  <span>Real-Time Bengaluru Junctions Map Graph</span>
                </h3>
                <div className="flex flex-col items-center bg-[#050B14] rounded-lg border border-slate-800/60 p-4 w-full">
                  <div className="w-full h-[300px] bg-[#050B14] rounded overflow-hidden border border-slate-800 relative z-0">
                    <MapContainer center={[12.9225, 77.64]} zoom={13} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                      />
                      
                      {/* Render edges state */}
                      {(() => {
                        const nodeCoordsLookup: Record<string, [number, number]> = {};
                        junctionList.forEach(node => {
                          nodeCoordsLookup[node.name] = [node.lat, node.lon];
                        });

                        const edgesToDraw = routingResult?.edges_state || edgesList.map(e => ({
                          source: e.source,
                          target: e.target,
                          congestion_level: 'Low'
                        }));

                        return edgesToDraw.map((edge: any, index: number) => {
                          const u = nodeCoordsLookup[edge.source];
                          const v = nodeCoordsLookup[edge.target];
                          if (!u || !v) return null;

                          let edgeColor = '#10b981'; // Green (Low)
                          if (edge.congestion_level === 'Medium') edgeColor = '#f59e0b'; // Yellow
                          if (edge.congestion_level === 'High') edgeColor = '#ef4444'; // Red
                          if (edge.congestion_level === 'Extreme') edgeColor = '#7f1d1d'; // Dark Red (Gridlock)

                          const key = `${edge.source}_${edge.target}`;
                          const positions = edgeGeometries[key] || [u, v];

                          return (
                            <Polyline
                              key={`edge-${index}`}
                              positions={positions}
                              pathOptions={{ color: edgeColor, weight: 4, opacity: 0.8 }}
                            />
                          );
                        });
                      })()}

                      {/* Render optimal route highlight */}
                      {(() => {
                        const coords = getOptimalRouteGeometry();
                        if (coords.length > 1) {
                          return (
                            <Polyline
                              positions={coords}
                              pathOptions={{ color: '#00ffff', weight: 6, opacity: 0.95 }}
                            />
                          );
                        }
                        return null;
                      })()}

                      {/* Render markers for junctions */}
                      {junctionList.map(node => {
                        const isStart = node.name === simSource;
                        const isEnd = node.name === simTarget;
                        const isOnPath = (routingResult?.optimal_route || []).includes(node.name);

                        let markerIcon = blueIcon;
                        if (isStart) markerIcon = goldIcon;
                        else if (isEnd) markerIcon = redIcon;
                        else if (isOnPath) markerIcon = cyanIcon;

                        return (
                          <Marker key={node.name} position={[node.lat, node.lon]} icon={markerIcon}>
                            <Popup>
                              <div className="p-1 text-slate-900">
                                <h4 className="font-extrabold text-xs">{node.name}</h4>
                              </div>
                            </Popup>
                          </Marker>
                        );
                      })}
                    </MapContainer>
                  </div>
                  
                  {/* Graph Map Legend */}
                  <div className="flex flex-wrap gap-4 justify-center mt-3 text-[10px] font-bold text-slate-400 select-none uppercase">
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#dcba55]"></span>
                      <span>Start Point</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#ef4444]"></span>
                      <span>Destination</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-3.5 h-1 bg-[#00ffff] rounded"></span>
                      <span>Optimal Path</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded bg-[#10b981]"></span>
                      <span>Low Density</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded bg-[#f59e0b]"></span>
                      <span>Medium Density</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded bg-[#ef4444]"></span>
                      <span>High Density</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded bg-[#7f1d1d]"></span>
                      <span>Blocked / Gridlock</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Multi-Camera CCTV Grid */}
              <div className="space-y-4">
                <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                  <Video className="w-4 h-4 text-police-gold" />
                  <span>CCTV Surveillance Camera Feeds</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {simCameras.map((cam) => {
                    const connections = getConnectedJunctions(cam.fromJunction);
                    return (
                      <div key={cam.id} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4 bg-[#0a0f1d] hover:border-slate-700 transition-colors">
                        {/* Camera Header */}
                        <div className="flex justify-between items-center border-b border-slate-800 pb-2.5">
                          <span className="text-xs font-bold text-slate-300 flex items-center space-x-1.5">
                            <span className={`w-2 h-2 rounded-full ${cam.isStreaming ? 'bg-red-500 animate-pulse' : 'bg-slate-500'}`}></span>
                            <span>CCTV Camera {cam.id}</span>
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                            cam.headcount > 60 ? 'bg-red-500/15 text-red-400 border-red-500/20' :
                            cam.headcount > 30 ? 'bg-amber-500/15 text-amber-400 border-amber-500/20' :
                            cam.headcount > 10 ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/15' :
                            'bg-emerald-500/15 text-emerald-400 border-emerald-500/20'
                          }`}>
                            {cam.headcount} objects detected
                          </span>
                        </div>

                        {/* Location Mapping Dropdowns */}
                        <div className="grid grid-cols-2 gap-2 text-[10px] font-bold">
                          <div>
                            <label className="block text-slate-400 mb-1">From Junction</label>
                            <select
                              value={cam.fromJunction}
                              onChange={(e) => {
                                const val = e.target.value;
                                setSimCameras(prev => prev.map(c => c.id === cam.id ? { ...c, fromJunction: val, toJunction: '' } : c));
                              }}
                              className="w-full bg-[#050B14] border border-slate-800 rounded p-1.5 text-slate-300 focus:outline-none"
                            >
                              <option value="">-- Select --</option>
                              {junctionList.map(j => (
                                <option key={j.name} value={j.name}>{j.name.replace('Junc', '').replace('Junction', '')}</option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-slate-400 mb-1">To Junction</label>
                            <select
                              value={cam.toJunction}
                              onChange={(e) => {
                                const val = e.target.value;
                                setSimCameras(prev => prev.map(c => c.id === cam.id ? { ...c, toJunction: val } : c));
                              }}
                              disabled={!cam.fromJunction}
                              className="w-full bg-[#050B14] border border-slate-800 rounded p-1.5 text-slate-300 focus:outline-none disabled:opacity-30"
                            >
                              <option value="">-- Select --</option>
                              {connections.map(targetNode => (
                                <option key={targetNode} value={targetNode}>{targetNode.replace('Junc', '').replace('Junction', '')}</option>
                              ))}
                            </select>
                          </div>
                        </div>

                        {/* Feed Simulation Controls */}
                        <div className="space-y-3">
                          {cam.isStreaming ? (
                            /* Streaming Frame View */
                            <div className="space-y-2">
                              <div className="h-[120px] rounded-lg bg-[#050B14] border border-slate-800/50 flex items-center justify-center overflow-hidden relative">
                                {cam.currentFrame ? (
                                  <>
                                    <img 
                                      src={cam.currentFrame} 
                                      alt={`Camera ${cam.id} visual stream`} 
                                      className="max-h-full max-w-full object-contain"
                                    />
                                    <div className="absolute inset-x-0 h-0.5 bg-police-gold/40 shadow-[0_0_8px_#dcba55] animate-radar-sweep pointer-events-none z-10" />
                                  </>
                                ) : (
                                  <div className="text-center text-slate-600 flex flex-col items-center">
                                    <RefreshCw className="w-5 h-5 animate-spin mb-1 text-police-gold" />
                                    <span className="text-[8px] font-bold">Decoding stream frames...</span>
                                  </div>
                                )}
                              </div>
                              
                              <div className="flex justify-between items-center text-[8px] font-bold text-slate-400">
                                <span>Frame: {cam.frameIdx} / {cam.totalFrames}</span>
                                <button 
                                  onClick={() => stopCameraWs(cam.id)}
                                  className="px-2 py-0.5 border border-red-500/35 text-red-400 rounded hover:bg-red-500/10 transition-colors"
                                >
                                  Stop
                                </button>
                              </div>
                            </div>
                          ) : (
                            /* Manual controls / upload form */
                            <div className="space-y-3">
                              {/* Manual Sliders */}
                              <div className="space-y-1">
                                <div className="flex justify-between text-[8px] text-slate-400 font-bold">
                                  <span>Manual Density Slider</span>
                                  <span>{cam.headcount} objects</span>
                                </div>
                                <input 
                                  type="range"
                                  min="0"
                                  max="100"
                                  value={cam.headcount}
                                  onChange={(e) => updateCameraHeadcount(cam.id, Number(e.target.value))}
                                  className="w-full accent-police-gold h-1 bg-slate-800 rounded-lg cursor-pointer appearance-none"
                                />
                              </div>

                              {/* Upload Video Trigger */}
                              <div>
                                <input 
                                  type="file" 
                                  accept="video/*"
                                  id={`sim-cam-file-${cam.id}`}
                                  onChange={(e) => handleCameraVideoUpload(cam.id, e)}
                                  className="hidden"
                                />
                                <label 
                                  htmlFor={`sim-cam-file-${cam.id}`}
                                  className="w-full py-1.5 bg-slate-900 border border-slate-800 hover:border-police-gold text-slate-300 hover:text-white rounded text-[10px] font-bold flex items-center justify-center space-x-1.5 cursor-pointer transition-all duration-200"
                                >
                                  <Upload className="w-3.5 h-3.5" />
                                  <span>Simulate with Video file</span>
                                </label>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* === VIDEO MODE CONTENT === */}
          {mode === 'video' && (
            <>
              {/* Live Frame Viewer */}
              <div className="glass-panel p-6 rounded-xl border border-slate-800 relative overflow-hidden bg-[#0a0f1d]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <Activity className="w-4 h-4 text-police-red" />
                    <span>Live CCTV Analysis Feed</span>
                  </h3>
                  {videoStream.isStreaming && (
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                      <span className="text-[10px] text-red-400 font-bold uppercase tracking-wider">Processing</span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col justify-center items-center h-[300px] rounded-lg bg-[#050B14] border border-slate-800/50 overflow-hidden relative">
                  {videoStream.currentFrame ? (
                    <>
                      <img 
                        src={videoStream.currentFrame} 
                        alt="Annotated video frame" 
                        className="max-h-full max-w-full object-contain"
                      />
                      {videoStream.isStreaming && (
                        <div className="absolute inset-x-0 h-0.5 bg-police-gold/40 shadow-[0_0_8px_#dcba55] animate-radar-sweep pointer-events-none z-10" />
                      )}
                    </>
                  ) : videoPreviewUrl && !videoStream.isStreaming ? (
                    <video 
                      src={videoPreviewUrl}
                      className="max-h-full max-w-full object-contain opacity-50"
                      muted
                    />
                  ) : (
                    <div className="text-center text-slate-500">
                      <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p className="text-xs font-semibold">Video Feed Inactive</p>
                      <p className="text-[10px] mt-1">Upload a video to start real-time headcount analysis.</p>
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                {(videoStream.isStreaming || videoStream.summary) && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">
                        Frame {videoStream.frameIdx} / {videoStream.totalFrames}
                      </span>
                      <span className="text-[10px] font-bold text-police-gold">{progressPct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-police-gold to-amber-400 rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${progressPct}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Real-Time Stats Row */}
              {(videoStream.isStreaming || videoStream.frameCounts.length > 0) && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                  {/* Live Headcount */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Live Detections Count</span>
                    <span className={`text-4xl font-black transition-all duration-200 ${
                      videoStream.headcount > 30 ? 'text-police-red' : videoStream.headcount > 10 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {videoStream.headcount}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">objects detected</span>
                  </div>

                  {/* Peak Count */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Peak Count</span>
                    <span className="text-4xl font-black text-police-red">
                      {videoStream.peakCount}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">max in single frame</span>
                  </div>

                  {/* Density Grade */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Density Grade</span>
                    <span className={`text-3xl font-black ${
                      videoStream.density === 'Extreme' || videoStream.density === 'High' ? 'text-police-red' : 
                      videoStream.density === 'Medium' ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {videoStream.density}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">crowd classification</span>
                  </div>

                  {/* Target Congestion */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Target Congestion</span>
                    <span className="text-3xl font-black text-slate-200">
                      {videoStream.updatedCongestion}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">calculated traffic risk</span>
                  </div>

                  {/* Dispatch Target */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Dispatch Target</span>
                    <span className="text-3xl font-black text-police-light">
                      {videoStream.policeRecommended} Officers
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">patrol mobilization</span>
                  </div>

                  {/* Barricades Recommended */}
                  <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase mb-2">Barricades Recommended</span>
                    <span className="text-3xl font-black text-police-gold">
                      {videoStream.barricadesRecommended} Units
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">tactical cordon units</span>
                  </div>
                </div>
              )}

              {/* Sparkline Chart */}
              {videoStream.frameCounts.length > 5 && (
                <div className="glass-panel p-5 rounded-xl border border-slate-800">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-police-red" />
                      <span>Headcount Timeline</span>
                    </h3>
                    <span className="text-[10px] text-slate-500 font-semibold">
                      {videoStream.frameCounts.length} data points
                    </span>
                  </div>
                  <SparklineChart data={videoStream.frameCounts} width={600} height={90} />
                </div>
              )}

              {/* Video Summary */}
              {videoStream.summary && (
                <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-emerald-400 border-b border-slate-800 pb-3 flex items-center space-x-2">
                    <BarChart3 className="w-4 h-4" />
                    <span>Video Analysis Complete</span>
                  </h3>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Average Objects Count</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.average_headcount} objects</span>
                      </div>
                      <Users className="w-6 h-6 text-police-gold opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Peak Objects Count</span>
                        <span className="text-2xl font-black text-police-red">{videoStream.summary.peak_headcount} objects</span>
                      </div>
                      <AlertTriangle className="w-6 h-6 text-police-red opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Frames Processed</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.total_frames_processed}</span>
                      </div>
                      <Film className="w-6 h-6 text-slate-400 opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Crowd Density</span>
                        <span className={`text-2xl font-black ${
                          videoStream.summary.crowd_density === 'Extreme' || videoStream.summary.crowd_density === 'High' ? 'text-police-red' : 'text-amber-400'
                        }`}>{videoStream.summary.crowd_density}</span>
                      </div>
                      <ShieldCheck className="w-6 h-6 text-emerald-400 opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Target Congestion</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.updated_congestion || 'Low'}</span>
                      </div>
                      <ShieldCheck className="w-6 h-6 text-[#00ffff] opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Dispatch Target</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.police_recommended || 0} officers</span>
                      </div>
                      <Siren className="w-6 h-6 text-police-light opacity-55" />
                    </div>
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between col-span-2 lg:col-span-1">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Barricades Recommended</span>
                        <span className="text-2xl font-black text-slate-200">{videoStream.summary.barricades_recommended || 0} units</span>
                      </div>
                      <Construction className="w-6 h-6 text-police-gold opacity-55" />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* === IMAGE MODE CONTENT === */}
          {mode === 'image' && (
            <>
              <div className="glass-panel p-6 rounded-xl border border-slate-800 flex flex-col justify-center items-center h-[350px] relative overflow-hidden bg-[#0a0f1d]">
                {annotatedUrl ? (
                  <img 
                    src={annotatedUrl} 
                    alt="Annotated CCTV analysis" 
                    className="max-h-full max-w-full object-contain rounded-lg border border-slate-800 shadow-xl"
                  />
                ) : previewUrl ? (
                  <img 
                    src={previewUrl} 
                    alt="Selected feed preview" 
                    className="max-h-full max-w-full object-contain rounded-lg border border-slate-800 opacity-60"
                  />
                ) : (
                  <div className="text-center text-slate-500">
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-xs font-semibold">CCTV Feed Inactive</p>
                    <p className="text-[10px] mt-1">Select a preset or upload an image to start detection.</p>
                  </div>
                )}
                {loading && (
                  <div className="absolute inset-0 bg-[#050B14]/85 flex flex-col items-center justify-center space-y-3">
                    <RefreshCw className="w-8 h-8 text-police-gold animate-spin" />
                    <p className="text-xs text-police-gold font-bold uppercase tracking-wider">Deploying SAHI Slices...</p>
                  </div>
                )}
              </div>

              {/* Inference outcomes */}
              {result && (
                <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-5 animate-fade-in">
                  <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">Detection Metrics</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Traffic & Crowd Count</span>
                        <span className="text-2xl font-black text-slate-200">{result.crowd_count} objects</span>
                      </div>
                      <Users className="w-6 h-6 text-police-gold opacity-55" />
                    </div>

                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Density Grade</span>
                        <span className={`text-2xl font-black ${
                          result.crowd_density === 'Extreme' || result.crowd_density === 'High' ? 'text-police-red' : 'text-amber-400'
                        }`}>{result.crowd_density}</span>
                      </div>
                      <AlertTriangle className="w-6 h-6 text-police-red opacity-55" />
                    </div>

                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Target Congestion</span>
                        <span className="text-2xl font-black text-slate-200">{result.updated_congestion}</span>
                      </div>
                      <ShieldCheck className="w-6 h-6 text-emerald-400 opacity-55" />
                    </div>

                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Dispatch Target</span>
                        <span className="text-2xl font-black text-slate-200">{result.police_recommended} officers</span>
                      </div>
                      <Siren className="w-6 h-6 text-police-light opacity-55" />
                    </div>

                    <div className="bg-slate-900/40 p-4 rounded border border-slate-800 flex items-center justify-between md:col-span-2 lg:col-span-1">
                      <div>
                        <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Barricades Recommended</span>
                        <span className="text-2xl font-black text-slate-200">{result.barricades_recommended} units</span>
                      </div>
                      <Construction className="w-6 h-6 text-police-gold opacity-55" />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
