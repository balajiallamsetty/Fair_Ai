import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Files, ShieldAlert, Workflow } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MetricRing } from '@/components/charts/metric-ring';
import { BiasTrendChart } from '@/components/charts/bias-trend-chart';
import { ComparisonChart } from '@/components/charts/comparison-chart';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { Stagger, StaggerItem } from '@/components/animations/stagger';
import { workflowSteps } from '@/theme/designSystem';
import { listDatasets } from '@/services/dataset.service';
import { listModels } from '@/services/model.service';
import { listAlerts } from '@/services/monitoring.service';
import { formatDate, formatNumber } from '@/utils/format';
import { Badge } from '@/components/ui/badge';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [datasetResponse, modelResponse, alertResponse] = await Promise.all([
          listDatasets(true).catch(() => ({ datasets: [], total: 0 })),
          listModels(true).catch(() => []),
          listAlerts().catch(() => ({ alerts: [], total: 0 })),
        ]);
        if (!active) return;
        setDatasets(datasetResponse.datasets);
        setModels(modelResponse);
        setAlerts(alertResponse.alerts);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : 'Failed to load dashboard');
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const kpis = useMemo(
    () => [
      { label: 'Datasets', value: datasets.length, icon: Files, tone: 'brand' as const },
      { label: 'Models', value: models.length, icon: Workflow, tone: 'success' as const },
      { label: 'Alerts', value: alerts.length, icon: ShieldAlert, tone: 'danger' as const },
    ],
    [datasets.length, models.length, alerts.length],
  );

  const trendData = useMemo(
    () =>
      (datasets.length
        ? datasets.slice(0, 5).map((dataset, index) => ({ label: dataset.name.slice(0, 6) || `D${index + 1}`, score: Number((dataset.bias_report?.bias_score ?? 0.18 + index * 0.05).toFixed(2)) }))
        : [
            { label: 'Week 1', score: 0.22 },
            { label: 'Week 2', score: 0.19 },
            { label: 'Week 3', score: 0.16 },
            { label: 'Week 4', score: 0.12 },
          ]),
    [datasets],
  );

  const comparisonData = useMemo(
    () =>
      datasets.length
        ? datasets.slice(0, 4).map((dataset, index) => ({ name: dataset.name.slice(0, 10) || `Group ${index + 1}`, value: Math.round((dataset.profile?.rows_count ?? 1000) / (index + 2)) }))
        : [
            { name: 'Group A', value: 42 },
            { name: 'Group B', value: 56 },
            { name: 'Group C', value: 48 },
          ],
    [datasets],
  );

  if (loading) {
    return <LoadingState lines={8} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  }

  return (
    <Stagger>
      <div className="grid gap-6 xl:grid-cols-[1.6fr_0.9fr]">
        <StaggerItem>
          <Card className="relative overflow-hidden p-8">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.18),transparent_26%)]" />
            <div className="relative z-10 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-2xl space-y-4">
                <Badge tone="neutral">Workflow ready</Badge>
                <h1 className="text-3xl font-semibold tracking-tight text-white lg:text-5xl">Operational fairness control room.</h1>
                <p className="max-w-xl text-slate-300">
                  Track datasets, models, monitoring signals, and review actions from a single enterprise dashboard aligned to the backend lifecycle.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => navigate('/datasets')}>Upload dataset <ArrowRight className="h-4 w-4" /></Button>
                  <Button variant="secondary" onClick={() => navigate('/models')}>Train model</Button>
                  <Button variant="ghost" onClick={() => navigate('/governance')}>Review queue</Button>
                </div>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Guided workflow</p>
                <div className="mt-4 space-y-3 text-sm text-slate-200">
                  {workflowSteps.map((step, index) => (
                    <div key={step} className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-500/20 text-xs text-brand-200">{index + 1}</span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
            {kpis.map((kpi, index) => (
              <MetricRing
                key={kpi.label}
                label={kpi.label}
                value={Math.min(100, kpi.value * 28 + 15)}
                tone={kpi.tone}
                description={`Live ${kpi.label.toLowerCase()} in your workspace`}
              />
            ))}
          </div>
        </StaggerItem>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <StaggerItem>
          <BiasTrendChart data={trendData} />
        </StaggerItem>
        <StaggerItem>
          <ComparisonChart data={comparisonData} title="Distribution snapshot" />
        </StaggerItem>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <StaggerItem>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Recent datasets</CardTitle>
                <CardDescription>Latest dataset registrations and upload metadata.</CardDescription>
              </div>
            </CardHeader>
            <div className="space-y-3">
              {datasets.length ? datasets.slice(0, 4).map((dataset) => (
                <button key={dataset.id} onClick={() => navigate(`/datasets/${dataset.id}`)} className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left hover:bg-white/10">
                  <div>
                    <p className="font-medium text-white">{dataset.name}</p>
                    <p className="text-sm text-slate-400">Updated {formatDate(dataset.updated_at)}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                </button>
              )) : <p className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">No datasets yet. Upload your first CSV to start the workflow.</p>}
            </div>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Active alerts</CardTitle>
                <CardDescription>Monitoring and governance signals requiring attention.</CardDescription>
              </div>
            </CardHeader>
            <div className="space-y-3">
              {alerts.length ? alerts.slice(0, 4).map((alert) => (
                <div key={alert.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium text-white">{alert.alert_type}</p>
                    <Badge tone={alert.severity === 'critical' ? 'danger' : alert.severity === 'high' ? 'danger' : alert.severity === 'medium' ? 'warning' : 'success'}>{alert.severity}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-400">{alert.message}</p>
                </div>
              )) : <p className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">No alerts currently open. Monitoring is quiet.</p>}
            </div>
          </Card>
        </StaggerItem>
      </div>

      <p className="mt-6 text-xs uppercase tracking-[0.3em] text-slate-500">Records loaded: {formatNumber(datasets.length + models.length + alerts.length)}</p>
    </Stagger>
  );
}
