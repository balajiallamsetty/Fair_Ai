import { api } from './http';
import type { GovernanceReport, ReviewItem } from '@/types/api';

export async function getGovernanceReport(params?: { dataset_id?: string; model_id?: string }) {
  const { data } = await api.get<GovernanceReport>('/governance/report', { params });
  return data;
}

export async function listReviewQueue(status_filter = 'pending') {
  const { data } = await api.get<{ items: ReviewItem[]; total: number }>('/governance/review-queue', {
    params: { status_filter },
  });
  return data;
}

export async function resolveReview(reviewId: string, decision: 'approved' | 'rejected') {
  const { data } = await api.post(`/governance/review-queue/${reviewId}/resolve`, null, { params: { decision } });
  return data as Record<string, unknown>;
}
