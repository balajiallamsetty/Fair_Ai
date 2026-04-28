import { api } from './http';
import type { RegisterPayload, TokenResponse } from '@/types/api';

export async function login(payload: { email: string; password: string }) {
  const { data } = await api.post<TokenResponse>('/governance/auth/login', payload);
  return data;
}

export async function register(payload: RegisterPayload) {
  const { data } = await api.post('/governance/auth/register', payload);
  return data;
}
