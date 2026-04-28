import { cn } from '@/utils/cn';
import type { ReactNode } from 'react';

export function Badge({ className, tone = 'neutral', children }: { className?: string; tone?: 'neutral' | 'success' | 'warning' | 'danger'; children: ReactNode }) {
  const tones = {
    neutral: 'border-white/10 bg-white/5 text-slate-300',
    success: 'border-emerald-400/20 bg-emerald-500/10 text-emerald-300',
    warning: 'border-amber-400/20 bg-amber-500/10 text-amber-300',
    danger: 'border-rose-400/20 bg-rose-500/10 text-rose-300',
  };

  return <span className={cn('inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium', tones[tone], className)}>{children}</span>;
}
