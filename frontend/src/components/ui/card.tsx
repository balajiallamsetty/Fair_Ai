import { cn } from '@/utils/cn';
import { motion } from 'framer-motion';
import type { HTMLAttributes } from 'react';

const MotionCard = motion.div as unknown as React.FC<any>;

export function Card({ className, ...props }: Omit<HTMLAttributes<HTMLDivElement>, 'onDrag'>) {
  return <MotionCard whileHover={{ y: -2 }} className={cn('rounded-2xl border border-white/10 bg-white/5 p-5 shadow-xl shadow-slate-950/20 backdrop-blur-xl dark:bg-slate-950/40', className)} {...props} />;
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-4 flex items-start justify-between gap-3', className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-base font-semibold text-slate-50', className)} {...props} />;
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm text-slate-400', className)} {...props} />;
}
