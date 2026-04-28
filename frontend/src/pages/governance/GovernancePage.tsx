import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/tables/data-table';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { getGovernanceReport, listReviewQueue, resolveReview } from '@/services/governance.service';
import { formatDate } from '@/utils/format';

export default function GovernancePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState('pending');
  const [queue, setQueue] = useState<any[]>([]);
  const [report, setReport] = useState<any | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [queueResponse, reportResponse] = await Promise.all([listReviewQueue(status), getGovernanceReport()]);
        if (!active) return;
        setQueue(queueResponse.items);
        setReport(reportResponse);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load governance');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [status]);

  async function handleResolve(reviewId: string, decision: 'approved' | 'rejected') {
    await resolveReview(reviewId, decision);
    toast.success(`Review ${decision}.`);
    const refreshed = await listReviewQueue(status);
    setQueue(refreshed.items);
  }

  if (loading) return <LoadingState lines={7} />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <CardHeader className="mb-4 p-0">
          <div>
            <CardTitle>Governance review</CardTitle>
            <CardDescription>Pending items, audit logs, and report-level risk signals.</CardDescription>
          </div>
        </CardHeader>
        <div className="flex flex-wrap gap-2">
          {['pending', 'approved', 'rejected'].map((item) => (
            <Button key={item} variant={status === item ? 'primary' : 'secondary'} size="sm" onClick={() => setStatus(item)}>
              {item}
            </Button>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Review queue</CardTitle>
            <CardDescription>Human-in-the-loop items that require approval or rejection.</CardDescription>
          </div>
        </CardHeader>
        <DataTable
          columns={[ 'Item', 'Status', 'Created', 'Decision' ]}
          rows={queue.map((item) => [
            <div key={item.id}>
              <p className="font-medium text-white">{item.title ?? item.alert_type ?? item.id}</p>
              <p className="text-xs text-slate-400">{item.entity_type ?? 'review item'}</p>
            </div>,
            <Badge key={`${item.id}-status`} tone={item.status === 'approved' ? 'success' : item.status === 'rejected' ? 'danger' : 'warning'}>{item.status}</Badge>,
            formatDate(item.created_at),
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => handleResolve(item.id, 'approved')}>Approve</Button>
              <Button size="sm" variant="danger" onClick={() => handleResolve(item.id, 'rejected')}>Reject</Button>
            </div>,
          ])}
          emptyTitle="No queue items"
          emptyDescription="There are no items in the current review state."
        />
      </Card>

      {report ? (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Alerts</CardTitle>
                <CardDescription>Governance report summary.</CardDescription>
              </div>
            </CardHeader>
            <p className="text-3xl font-semibold text-white">{report.alerts.length}</p>
          </Card>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Open reviews</CardTitle>
                <CardDescription>Current queue size in the report.</CardDescription>
              </div>
            </CardHeader>
            <p className="text-3xl font-semibold text-white">{report.open_reviews.length}</p>
          </Card>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Audit logs</CardTitle>
                <CardDescription>Recorded governance events.</CardDescription>
              </div>
            </CardHeader>
            <p className="text-3xl font-semibold text-white">{report.audit_logs.length}</p>
          </Card>
        </div>
      ) : null}

      {report ? (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Governance report</CardTitle>
              <CardDescription>Generated {formatDate(report.generated_at)}</CardDescription>
            </div>
          </CardHeader>
          <div className="grid gap-4 lg:grid-cols-3">
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(report.dataset, null, 2)}</pre>
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(report.model, null, 2)}</pre>
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(report.alerts.slice(0, 3), null, 2)}</pre>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
