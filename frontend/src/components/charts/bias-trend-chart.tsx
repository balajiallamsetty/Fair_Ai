import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { motion } from 'framer-motion';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { ReactNode } from 'react';

export interface BiasTrendPoint {
  label: string;
  score: number;
}

export function BiasTrendChart({ data, title = 'Bias Trend', description = 'Historical fairness drift across uploads and model updates.' }: { data: BiasTrendPoint[]; title?: string; description?: string }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }} className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="biasTrendFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} stroke="#94a3b8" />
            <YAxis tickLine={false} axisLine={false} stroke="#94a3b8" domain={[0, 1]} />
            <Tooltip contentStyle={{ borderRadius: 16, background: 'rgba(15,23,42,0.92)', border: '1px solid rgba(255,255,255,0.08)' }} />
            <Area type="monotone" dataKey="score" stroke="#818cf8" fill="url(#biasTrendFill)" strokeWidth={3} dot={{ r: 3 }} isAnimationActive />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>
    </Card>
  );
}
