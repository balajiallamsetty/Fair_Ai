import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import type { ReactNode } from 'react';

export function DataTable({
  columns,
  rows,
  emptyTitle = 'No data yet',
  emptyDescription = 'Once the backend returns records, they will appear here.',
}: {
  columns: string[];
  rows: Array<Array<ReactNode>>;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              {columns.map((column) => (
                <th key={column} className="px-5 py-4 font-medium uppercase tracking-[0.18em]">{column}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/8 text-slate-200">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-white/5">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-5 py-4 align-top">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
