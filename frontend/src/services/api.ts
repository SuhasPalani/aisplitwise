import axios from 'axios';

// Determine the base URL based on environment
const API_BASE_URL = import.meta.env.PROD
  ? 'http://splitwise.local' // Your Ingress host for production (or actual domain)
  : 'http://splitwise.local'; // Use the same for development if you configure /etc/hosts or local DNS

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;