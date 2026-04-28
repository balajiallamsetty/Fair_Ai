import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function ComparisonChart({ data, title = 'Group Comparison', description = 'Outcome balance across sensitive groups.' }: { data: Array<{ name: string; value: number }>; title?: string; description?: string }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} stroke="#94a3b8" />
            <YAxis tickLine={false} axisLine={false} stroke="#94a3b8" />
            <Tooltip contentStyle={{ borderRadius: 16, background: 'rgba(15,23,42,0.92)', border: '1px solid rgba(255,255,255,0.08)' }} />
            <Bar dataKey="value" radius={[12, 12, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={index % 2 === 0 ? '#4f46e5' : '#06b6d4'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
