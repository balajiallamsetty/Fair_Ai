export type UserRole = 'admin' | 'auditor' | 'user';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

export interface AuthPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends AuthPayload {
  full_name: string;
  role?: UserRole;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string | null;
  owner_id: string;
  file_path: string;
  schema_definition: Record<string, string>;
  target_column: string;
  sensitive_columns: string[];
  feature_columns: string[];
  profile: Record<string, unknown>;
  preprocessing: Record<string, unknown>;
  bias_report?: Record<string, unknown> | null;
  sample_preview: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

export interface DatasetListResponse {
  datasets: Dataset[];
  total: number;
}

export interface BiasAnalysisResponse {
  dataset_id: string;
  generated_at: string;
  bias_score: number;
  group_analysis: Record<string, unknown>;
  distribution_comparison: Record<string, unknown>;
  proxy_detection: Record<string, unknown>;
  intersectional_analysis: Record<string, unknown>;
  recommendations: string[];
}

export interface ModelTrainRequest {
  dataset_id: string;
  name: string;
  test_size?: number;
  random_state?: number;
}

export interface Model {
  id: string;
  name: string;
  dataset_id: string;
  owner_id: string;
  algorithm: string;
  target_column: string;
  sensitive_columns: string[];
  feature_columns: string[];
  artifact_path: string;
  preprocessing_artifact_path?: string | null;
  training_summary: Record<string, unknown>;
  fairness_metrics: Record<string, unknown>;
  mitigation_results?: Record<string, unknown> | null;
  explainability?: Record<string, unknown> | null;
  model_card: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PredictionRequest {
  features: Record<string, string | number | boolean>;
  sensitive_attributes?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export interface PredictionResponse {
  model_id: string;
  prediction: number;
  probability: number;
  fairness_snapshot: Record<string, unknown>;
  flags: string[];
  requires_review: boolean;
  decision_log_id: string;
}

export interface MonitoringAlert {
  id: string;
  model_id: string;
  alert_type: string;
  severity: string;
  message: string;
  triggered_by: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  status: string;
  created_at: string;
  [key: string]: unknown;
}

export interface GovernanceReport {
  generated_at: string;
  dataset?: Record<string, unknown> | null;
  model?: Record<string, unknown> | null;
  alerts: Record<string, unknown>[];
  open_reviews: Record<string, unknown>[];
  audit_logs: Record<string, unknown>[];
}
