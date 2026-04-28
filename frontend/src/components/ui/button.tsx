import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils/cn';

const MotionButton = motion.button as unknown as React.FC<any>;

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const base = 'inline-flex items-center justify-center gap-2 rounded-2xl font-medium transition disabled:cursor-not-allowed disabled:opacity-50';

const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-gradient-to-r from-brand-500 to-cyan-500 text-white shadow-glow hover:brightness-110',
  secondary: 'bg-white/10 text-slate-100 border border-white/10 hover:bg-white/15 dark:bg-white/10',
  ghost: 'text-slate-200 hover:bg-white/8',
  danger: 'bg-rose-500/15 text-rose-200 border border-rose-400/20 hover:bg-rose-500/25',
};

const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = 'primary', size = 'md', ...props },
  ref,
) {
  return (
    <MotionButton
      ref={ref}
      whileTap={{ scale: 0.98 }}
      className={cn(base, variants[variant], sizes[size], className)}
      {...(props as ButtonHTMLAttributes<HTMLButtonElement>)}
    />
  );
});
