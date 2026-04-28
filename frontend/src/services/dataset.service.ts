import { api } from './http';
import type { Dataset, DatasetListResponse, BiasAnalysisResponse } from '@/types/api';

export async function listDatasets(mine = false) {
  const { data } = await api.get<DatasetListResponse>('/data/datasets', { params: { mine } });
  return data;
}

export async function getDataset(datasetId: string) {
  const { data } = await api.get<Dataset>(`/data/datasets/${datasetId}`);
  return data;
}

export async function getDatasetProfile(datasetId: string) {
  const { data } = await api.get(`/data/datasets/${datasetId}/profile`);
  return data as { id: string; profile: Record<string, unknown>; created_at: string };
}

export async function uploadDataset(payload: {
  name: string;
  description?: string;
  target_column: string;
  sensitive_columns: string[];
  feature_columns?: string[];
  file: File;
}) {
  const formData = new FormData();
  formData.append('name', payload.name);
  formData.append('target_column', payload.target_column);
  formData.append('sensitive_columns', payload.sensitive_columns.join(','));
  if (payload.description) formData.append('description', payload.description);
  if (payload.feature_columns?.length) formData.append('feature_columns', payload.feature_columns.join(','));
  formData.append('file', payload.file);

  const { data } = await api.post<Dataset>('/data/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function analyzeBias(datasetId: string) {
  const { data } = await api.post<BiasAnalysisResponse>(`/bias/datasets/${datasetId}/analyze`);
  return data;
}

export async function getBiasReport(datasetId: string) {
  const { data } = await api.get(`/bias/datasets/${datasetId}/report`);
  return data as BiasAnalysisResponse;
}
