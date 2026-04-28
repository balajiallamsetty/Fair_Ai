import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MetricRing } from '@/components/charts/metric-ring';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { explainModel, getModel } from '@/services/model.service';
import { formatDate } from '@/utils/format';
import { JsonPrettyInput } from '@/components/forms/json-pretty-input';

export default function ModelDetailPage() {
  const { modelId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<any | null>(null);
  const [explanation, setExplanation] = useState<any | null>(null);
  const [baseFeatures, setBaseFeatures] = useState('{\n  "feature": "value"\n}');
  const [candidateChanges, setCandidateChanges] = useState('[\n  {"feature": "alternate_value"}\n]');
  const [explaining, setExplaining] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!modelId) {
        setError('Missing model identifier.');
        setLoading(false);
        return;
      }
      try {
        const response = await getModel(modelId);
        if (!active) return;
        setModel(response);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load model');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [modelId]);

  async function handleExplain() {
    if (!modelId) return;
    setExplaining(true);
    try {
      const result = await explainModel(modelId, {
        base_features: JSON.parse(baseFeatures),
        candidate_changes: JSON.parse(candidateChanges),
      });
      setExplanation(result);
      toast.success('Explainability report generated.');
    } finally {
      setExplaining(false);
    }
  }

  if (loading) return <LoadingState lines={7} />;
  if (error || !model) return <ErrorState message={error ?? 'Model not found'} onRetry={() => window.location.reload()} />;

  const fairnessValues = Object.values(model.fairness_metrics ?? {}).filter((value) => typeof value === 'number') as number[];
  const fairnessScore = fairnessValues.length ? Math.round((fairnessValues.reduce((sum, value) => sum + value, 0) / fairnessValues.length) * 100) : 72;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardHeader className="mb-2 p-0">
              <div>
                <CardTitle>{model.name}</CardTitle>
                <CardDescription>{model.algorithm} model trained on {formatDate(model.created_at)}</CardDescription>
              </div>
            </CardHeader>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="neutral">{model.status}</Badge>
              {model.sensitive_columns.map((item: string) => <Badge key={item}>{item}</Badge>)}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate('/models')}>Back to models</Button>
            <Button onClick={handleExplain} disabled={explaining}>{explaining ? 'Explaining…' : 'Generate explainability'}</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <MetricRing label="Fairness health" value={fairnessScore} tone={fairnessScore > 80 ? 'success' : fairnessScore > 60 ? 'warning' : 'danger'} description="Aggregated from fairness metrics" />
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Training summary</CardTitle>
              <CardDescription>Backend-generated training metadata and metrics.</CardDescription>
            </div>
          </CardHeader>
          <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify({ training_summary: model.training_summary, fairness_metrics: model.fairness_metrics }, null, 2)}</pre>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Explainability controls</CardTitle>
            <CardDescription>Provide counterfactual inputs to generate a fairness-aware explanation.</CardDescription>
          </div>
        </CardHeader>
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-sm text-slate-300">Base features</p>
            <JsonPrettyInput value={baseFeatures} onChange={setBaseFeatures} placeholder='{"age": 32, "income": 70000}' />
          </div>
          <div>
            <p className="mb-2 text-sm text-slate-300">Candidate changes</p>
            <JsonPrettyInput value={candidateChanges} onChange={setCandidateChanges} placeholder='[{"income": 80000}]' />
          </div>
        </div>
      </Card>

      {explanation ? (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Explainability output</CardTitle>
              <CardDescription>Feature importance and counterfactual guidance returned by the backend.</CardDescription>
            </div>
          </CardHeader>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="mb-2 font-medium text-white">Baseline prediction</p>
              <pre className="whitespace-pre-wrap">{JSON.stringify(explanation.baseline_prediction, null, 2)}</pre>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="mb-2 font-medium text-white">Feature importance</p>
              <pre className="whitespace-pre-wrap">{JSON.stringify(explanation.feature_importance, null, 2)}</pre>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="mb-2 font-medium text-white">Counterfactuals</p>
              <pre className="whitespace-pre-wrap">{JSON.stringify(explanation.counterfactuals, null, 2)}</pre>
            </div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
