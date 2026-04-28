import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/tables/data-table';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { listDatasets } from '@/services/dataset.service';
import { listModels, trainModel } from '@/services/model.service';
import { formatDate } from '@/utils/format';

export default function ModelsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [form, setForm] = useState({ dataset_id: '', name: '', test_size: '0.2', random_state: '42' });

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [datasetResponse, modelResponse] = await Promise.all([listDatasets(true), listModels(true)]);
        if (!active) return;
        setDatasets(datasetResponse.datasets);
        setModels(modelResponse);
        setForm((current) => ({ ...current, dataset_id: datasetResponse.datasets[0]?.id ?? '' }));
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load models');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const created = await trainModel({
        dataset_id: form.dataset_id,
        name: form.name,
        test_size: Number(form.test_size),
        random_state: Number(form.random_state),
      });
      setModels((current) => [created, ...current]);
      toast.success('Model training completed.');
      navigate(`/models/${created.id}`);
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
            <CardTitle>Train a model</CardTitle>
            <CardDescription>Backend-backed logistic regression training aligned with the selected dataset.</CardDescription>
          </div>
        </CardHeader>
        <form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-4">
          <select value={form.dataset_id} onChange={(event) => setForm({ ...form, dataset_id: event.target.value })} className="h-11 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-slate-100 outline-none lg:col-span-1">
            {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
          </select>
          <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Model name" className="lg:col-span-1" required />
          <Input value={form.test_size} onChange={(event) => setForm({ ...form, test_size: event.target.value })} type="number" min="0.1" max="0.5" step="0.05" placeholder="Test size" className="lg:col-span-1" />
          <div className="flex gap-3 lg:col-span-1">
            <Input value={form.random_state} onChange={(event) => setForm({ ...form, random_state: event.target.value })} type="number" placeholder="Random state" />
            <Button type="submit" disabled={submitting}>{submitting ? 'Training…' : 'Train'}</Button>
          </div>
        </form>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Model library</CardTitle>
            <CardDescription>Trained models and fairness metadata from the backend.</CardDescription>
          </div>
        </CardHeader>
        <DataTable
          columns={[ 'Name', 'Algorithm', 'Status', 'Dataset', 'Updated' ]}
          rows={models.map((model) => [
            <button key={`${model.id}-name`} onClick={() => navigate(`/models/${model.id}`)} className="font-medium text-white hover:text-brand-200">{model.name}</button>,
            model.algorithm,
            <Badge tone={model.status === 'ready' ? 'success' : 'warning'}>{model.status}</Badge>,
            datasets.find((dataset) => dataset.id === model.dataset_id)?.name ?? model.dataset_id,
            formatDate(model.updated_at),
          ])}
          emptyTitle="No models trained yet"
          emptyDescription="Train the first model from the form above to populate the library."
        />
      </Card>
    </div>
  );
}
