import type { LucideIcon } from 'lucide-react';
import { BarChart3, FileUp, ShieldCheck, Sparkles, Workflow, ShieldAlert, Activity, Users } from 'lucide-react';

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  roles?: Array<'admin' | 'auditor' | 'user'>;
}

export const primaryNav: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: BarChart3 },
  { label: 'Datasets', path: '/datasets', icon: FileUp },
  { label: 'Bias Analysis', path: '/bias', icon: Sparkles },
  { label: 'Models', path: '/models', icon: Workflow },
  { label: 'Monitoring', path: '/monitoring', icon: Activity },
  { label: 'Governance', path: '/governance', icon: ShieldCheck, roles: ['admin', 'auditor'] },
];

export const authNav: NavItem[] = [
  { label: 'Login', path: '/auth/login', icon: Users },
  { label: 'Register', path: '/auth/register', icon: ShieldAlert },
];
