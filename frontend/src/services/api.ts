import axios from 'axios';

// Create API client with proxy-friendly path
const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically append token to request headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authApi = {
  login: async (formData: FormData) => {
    const response = await axios.post(`${API_URL}/auth/token`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },
  
  register: async (payload: any) => {
    const response = await api.post('/auth/register', payload);
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
  }
};

export const trafficApi = {
  predictCongestion: async (payload: any) => {
    const response = await api.post('/traffic/predict-congestion', payload);
    return response.data;
  },
  
  suggestDiversion: async (junction: string, zone: string) => {
    const formData = new FormData();
    formData.append('junction', junction);
    formData.append('zone', zone);
    const response = await api.post('/traffic/suggest-diversion', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  analyzeCrowd: async (payload: { event_id: string; base_congestion: string; priority: string; requires_road_closure: boolean; file: File }) => {
    const formData = new FormData();
    formData.append('event_id', payload.event_id);
    formData.append('base_congestion', payload.base_congestion);
    formData.append('priority', payload.priority);
    formData.append('requires_road_closure', String(payload.requires_road_closure));
    formData.append('file', payload.file);
    
    const response = await api.post('/traffic/analyze-crowd', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getEmergencyRoute: async (payload: any) => {
    const response = await api.post('/traffic/emergency-route', payload);
    return response.data;
  },
  
  getNearestStation: async (lat: number, lng: number) => {
    const formData = new FormData();
    formData.append('latitude', String(lat));
    formData.append('longitude', String(lng));
    const response = await api.post('/traffic/nearest-police-station', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  sendAlert: async (payload: any) => {
    const response = await api.post('/traffic/send-alert', payload);
    return response.data;
  },
  
  getTimeline: async () => {
    const response = await api.get('/traffic/timeline');
    return response.data;
  },
  
  submitFeedback: async (payload: any) => {
    const response = await api.post('/traffic/feedback', payload);
    return response.data;
  },
  
  executeRetraining: async () => {
    const response = await api.post('/traffic/execute-retraining');
    return response.data;
  }
};

export default api;
