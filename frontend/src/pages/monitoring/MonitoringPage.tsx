import { useEffect, useState, type FormEvent } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { DataTable } from '@/components/tables/data-table';
import { JsonPrettyInput } from '@/components/forms/json-pretty-input';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { listModels } from '@/services/model.service';
import { listAlerts, predict } from '@/services/monitoring.service';

export default function MonitoringPage() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [modelId, setModelId] = useState('');
  const [features, setFeatures] = useState('{\n  "feature": "value"\n}');
  const [sensitiveAttributes, setSensitiveAttributes] = useState('{\n  "group": "A"\n}');
  const [prediction, setPrediction] = useState<any | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [modelResponse, alertResponse] = await Promise.all([listModels(true), listAlerts()]);
        if (!active) return;
        setModels(modelResponse);
        setAlerts(alertResponse.alerts);
        setModelId(modelResponse[0]?.id ?? '');
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load monitoring');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  async function handlePredict(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!modelId) {
      toast.error('Select a model first.');
      return;
    }
    setSubmitting(true);
    try {
      const result = await predict(modelId, {
        features: JSON.parse(features),
        sensitive_attributes: JSON.parse(sensitiveAttributes),
      });
      setPrediction(result);
      toast.success('Prediction captured.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingState lines={7} />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <CardHeader className="mb-4 p-0">
          <div>
            <CardTitle>Live prediction and fairness monitoring</CardTitle>
            <CardDescription>Run a model prediction and immediately inspect fairness signals.</CardDescription>
          </div>
        </CardHeader>
        <form onSubmit={handlePredict} className="grid gap-4 lg:grid-cols-2">
          <select value={modelId} onChange={(event) => setModelId(event.target.value)} className="h-11 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-slate-100 outline-none">
            {models.map((model) => <option key={model.id} value={model.id}>{model.name}</option>)}
          </select>
          <JsonPrettyInput value={features} onChange={setFeatures} placeholder='{"feature": "value"}' />
          <JsonPrettyInput value={sensitiveAttributes} onChange={setSensitiveAttributes} placeholder='{"group": "A"}' />
          <div className="lg:col-span-2">
            <Button type="submit" disabled={submitting}>{submitting ? 'Evaluating…' : 'Run prediction'}</Button>
          </div>
        </form>
      </Card>

      {prediction ? (
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <Card className="p-6">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Prediction result</p>
            <div className="mt-4 flex items-end gap-3">
              <div className="text-5xl font-semibold text-white">{prediction.prediction}</div>
              <Badge tone={prediction.requires_review ? 'warning' : 'success'}>{prediction.requires_review ? 'Review required' : 'Automated decision'}</Badge>
            </div>
            <p className="mt-3 text-sm text-slate-400">Probability: {(prediction.probability * 100).toFixed(1)}%</p>
            <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(prediction.fairness_snapshot, null, 2)}</pre>
          </Card>
          <Card className="p-6">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Flags</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {prediction.flags.map((flag: string) => <Badge key={flag} tone="warning">{flag}</Badge>)}
            </div>
            <p className="mt-4 text-sm text-slate-400">Decision log ID: {prediction.decision_log_id}</p>
          </Card>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Alert feed</CardTitle>
            <CardDescription>Monitoring alerts returned from the backend.</CardDescription>
          </div>
        </CardHeader>
        <DataTable
          columns={[ 'Type', 'Severity', 'Status', 'Message' ]}
          rows={alerts.map((alert) => [
            alert.alert_type,
            <Badge key={`${alert.id}-severity`} tone={alert.severity === 'critical' ? 'danger' : alert.severity === 'high' ? 'danger' : alert.severity === 'medium' ? 'warning' : 'success'}>{alert.severity}</Badge>,
            alert.status,
            alert.message,
          ])}
          emptyTitle="No active alerts"
          emptyDescription="The monitoring channel is clear right now."
        />
      </Card>
    </div>
  );
}
