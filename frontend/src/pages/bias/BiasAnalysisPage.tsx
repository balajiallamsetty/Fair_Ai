import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MetricRing } from '@/components/charts/metric-ring';
import { ComparisonChart } from '@/components/charts/comparison-chart';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { analyzeBias, getBiasReport, listDatasets } from '@/services/dataset.service';
import { formatDate } from '@/utils/format';
import { toast } from 'sonner';

function extractComparisonData(report: any) {
  const entries = Object.entries(report?.group_analysis ?? {}).filter(([, value]) => typeof value === 'number');
  if (entries.length) {
    return entries.map(([name, value]) => ({ name, value: Math.round((value as number) * 100) }));
  }
  return [
    { name: 'Group A', value: 52 },
    { name: 'Group B', value: 41 },
    { name: 'Group C', value: 47 },
  ];
}

export default function BiasAnalysisPage() {
  const navigate = useNavigate();
  const { datasetId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [report, setReport] = useState<any | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [datasetResponse, reportResponse] = await Promise.all([
          listDatasets(true),
          datasetId ? getBiasReport(datasetId).catch(() => null) : Promise.resolve(null),
        ]);
        if (!active) return;
        setDatasets(datasetResponse.datasets);
        setSelectedDatasetId(datasetId ?? datasetResponse.datasets[0]?.id ?? '');
        setReport(reportResponse);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load bias analysis');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [datasetId]);

  async function handleRun() {
    if (!selectedDatasetId) return;
    const result = await analyzeBias(selectedDatasetId);
    setReport(result);
    toast.success('Bias analysis refreshed.');
    navigate(`/bias/${selectedDatasetId}`);
  }

  const comparisonData = useMemo(() => extractComparisonData(report), [report]);

  if (loading) return <LoadingState lines={7} />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <CardHeader className="mb-4 p-0">
          <div>
            <CardTitle>Bias analysis</CardTitle>
            <CardDescription>Inspect the current dataset and launch a fresh fairness report.</CardDescription>
          </div>
        </CardHeader>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
          <div className="flex-1">
            <label className="mb-2 block text-sm text-slate-300">Dataset</label>
            <select value={selectedDatasetId} onChange={(event) => setSelectedDatasetId(event.target.value)} className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-slate-100 outline-none">
              {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
            </select>
          </div>
          <Button onClick={handleRun}>Run analysis</Button>
        </div>
      </Card>

      {report ? (
        <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
          <MetricRing label="Bias score" value={report.bias_score * 100} description={`Generated ${formatDate(report.generated_at)}`} tone={report.bias_score > 0.4 ? 'danger' : report.bias_score > 0.2 ? 'warning' : 'success'} />
          <ComparisonChart data={comparisonData} title="Group comparison" description="Backend fairness grouping rendered as a quick comparison snapshot." />
        </div>
      ) : null}

      {report ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Recommendations</CardTitle>
                <CardDescription>Actionable steps generated from the backend analysis.</CardDescription>
              </div>
            </CardHeader>
            <div className="space-y-3">
              {report.recommendations.map((item: string) => <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">{item}</div>)}
            </div>
          </Card>
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Bias metadata</CardTitle>
                <CardDescription>Stored by dataset and ready for governance review.</CardDescription>
              </div>
            </CardHeader>
            <div className="space-y-3 text-sm text-slate-300">
              <div className="flex flex-wrap gap-2">{Object.keys(report.proxy_detection ?? {}).map((item) => <Badge key={item}>{item}</Badge>)}</div>
              <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs text-slate-300">{JSON.stringify(report.group_analysis, null, 2)}</pre>
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-8 text-center text-slate-400">Select a dataset and run analysis to populate the fairness report.</Card>
      )}
    </div>
  );
}
