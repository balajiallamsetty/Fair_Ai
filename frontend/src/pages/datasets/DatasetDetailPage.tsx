import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/tables/data-table';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { analyzeBias, getDataset, getBiasReport } from '@/services/dataset.service';
import { formatDate } from '@/utils/format';

export default function DatasetDetailPage() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataset, setDataset] = useState<any | null>(null);
  const [analysis, setAnalysis] = useState<any | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      if (!datasetId) {
        setError('Missing dataset identifier.');
        setLoading(false);
        return;
      }
      try {
        const [datasetResponse, reportResponse] = await Promise.all([
          getDataset(datasetId),
          getBiasReport(datasetId).catch(() => null),
        ]);
        if (!active) return;
        setDataset(datasetResponse);
        setAnalysis(reportResponse);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load dataset');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [datasetId]);

  async function handleAnalyze() {
    if (!datasetId) return;
    const result = await analyzeBias(datasetId);
    setAnalysis(result);
    toast.success('Bias analysis completed.');
    navigate(`/bias/${datasetId}`);
  }

  if (loading) return <LoadingState lines={7} />;
  if (error || !dataset) return <ErrorState message={error ?? 'Dataset not found'} onRetry={() => window.location.reload()} />;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardHeader className="mb-2 p-0">
              <div>
                <CardTitle>{dataset.name}</CardTitle>
                <CardDescription>{dataset.description || 'No description provided.'}</CardDescription>
              </div>
            </CardHeader>
            <div className="mt-3 flex flex-wrap gap-2">
              {dataset.sensitive_columns.map((item: string) => <Badge key={item}>{item}</Badge>)}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate('/datasets')}>Back to datasets</Button>
            <Button onClick={handleAnalyze}>Analyze bias</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Schema and preview</CardTitle>
              <CardDescription>Ingested schema definition and sample rows from the CSV.</CardDescription>
            </div>
          </CardHeader>
          <div className="space-y-4">
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(dataset.schema_definition, null, 2)}</pre>
            <DataTable
              columns={dataset.sample_preview[0] ? Object.keys(dataset.sample_preview[0]) : ['Preview']}
              rows={dataset.sample_preview.map((row: Record<string, unknown>) => Object.values(row).map((value) => String(value ?? '')))}
              emptyTitle="No sample preview available"
              emptyDescription="The backend did not return preview rows for this dataset."
            />
          </div>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Dataset profile</CardTitle>
              <CardDescription>Uploaded at {formatDate(dataset.created_at)}</CardDescription>
            </div>
          </CardHeader>
          <div className="space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Target column: <span className="font-medium text-white">{dataset.target_column}</span></div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Feature columns: <span className="font-medium text-white">{dataset.feature_columns.join(', ') || 'Auto-detected'}</span></div>
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(dataset.profile, null, 2)}</pre>
          </div>
        </Card>
      </div>

      {analysis ? (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Latest bias snapshot</CardTitle>
              <CardDescription>Stored analysis and recommendations for this dataset.</CardDescription>
            </div>
          </CardHeader>
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Bias score</p>
              <div className="mt-3 text-4xl font-semibold text-white">{Math.round(analysis.bias_score * 100)}%</div>
              <p className="mt-2 text-sm text-slate-400">Generated {formatDate(analysis.generated_at)}</p>
            </div>
            <div className="space-y-3">
              {analysis.recommendations.map((item: string) => (
                <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">{item}</div>
              ))}
            </div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
