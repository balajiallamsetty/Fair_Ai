import { motion } from 'framer-motion';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/utils/cn';

export function MetricRing({ label, value, tone = 'brand', description }: { label: string; value: number; tone?: 'brand' | 'success' | 'warning' | 'danger'; description?: string }) {
  const toneClasses = {
    brand: 'from-brand-500 to-cyan-400',
    success: 'from-emerald-500 to-cyan-400',
    warning: 'from-amber-500 to-orange-400',
    danger: 'from-rose-500 to-red-400',
  };

  return (
    <Card className="flex h-full flex-col justify-between">
      <CardHeader>
        <div>
          <CardTitle>{label}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <div className="flex items-center gap-4">
        <div className="relative h-24 w-24 shrink-0 rounded-full bg-slate-900/80 p-1">
          <motion.div
            initial={{ rotate: -90 }}
            animate={{ rotate: -90 }}
            className={cn('absolute inset-0 rounded-full bg-gradient-to-br', toneClasses[tone])}
            style={{
              maskImage: `conic-gradient(white ${value}%, transparent ${value}%)`,
              WebkitMaskImage: `conic-gradient(white ${value}%, transparent ${value}%)`,
            }}
          />
          <div className="absolute inset-2 grid place-items-center rounded-full bg-slate-950">
            <span className="text-xl font-semibold text-white">{Math.round(value)}%</span>
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-slate-400">Current score</p>
          <div className="text-3xl font-semibold text-white">{Math.round(value)}%</div>
        </div>
      </div>
    </Card>
  );
}
