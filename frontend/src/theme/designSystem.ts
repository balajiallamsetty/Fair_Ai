export const workflowSteps = [
  'Register',
  'Login',
  'Upload Dataset',
  'Analyze Bias',
  'Train Model',
  'Predict',
  'Monitor',
  'Governance Review',
];

export const severityTone: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  high: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  critical: 'text-red-400 bg-red-500/10 border-red-500/20',
};
