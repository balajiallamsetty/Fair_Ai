import { api } from './http';
import type { MonitoringAlert, PredictionRequest, PredictionResponse } from '@/types/api';

export async function predict(modelId: string, payload: PredictionRequest) {
  const { data } = await api.post<PredictionResponse>(`/monitoring/models/${modelId}/predict`, payload);
  return data;
}

export async function listAlerts(params?: { model_id?: string; status?: string }) {
  const { data } = await api.get<{ alerts: MonitoringAlert[]; total: number }>('/monitoring/alerts', { params });
  return data;
}
