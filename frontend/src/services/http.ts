import axios, { AxiosError } from 'axios';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/auth.store';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const baseURL = `${apiUrl}/api/v1`;

export const api = axios.create({
  baseURL,
  withCredentials: false,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status;
    const message = error.response?.data?.detail ?? error.message ?? 'Request failed';

    if (status === 401) {
      useAuthStore.getState().logout();
      if (window.location.pathname !== '/auth/login') {
        window.location.assign('/auth/login');
      }
      toast.error('Session expired. Please sign in again.');
    } else if (status === 403) {
      toast.error('Access denied. You do not have permission for that action.');
    } else if (status === 404) {
      toast.error('Requested resource was not found.');
    } else {
      toast.error(message);
    }

    return Promise.reject(error);
  },
);
