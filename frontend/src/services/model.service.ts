import { api } from './http';
import type { Model, ModelTrainRequest } from '@/types/api';

export async function listModels(mine = false) {
  const { data } = await api.get<Model[]>('/models', { params: { mine } });
  return data;
}

export async function getModel(modelId: string) {
  const { data } = await api.get<Model>(`/models/${modelId}`);
  return data;
}

export async function trainModel(payload: ModelTrainRequest) {
  const { data } = await api.post<Model>('/models/train', payload);
  return data;
}

export async function explainModel(modelId: string, payload: {
  base_features: Record<string, unknown>;
  candidate_changes: Array<Record<string, unknown>>;
}) {
  const { data } = await api.post(`/models/${modelId}/explain`, payload);
  return data as { feature_importance: Array<Record<string, unknown>>; baseline_prediction: Record<string, unknown>; counterfactuals: Array<Record<string, unknown>> };
}
