import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/tables/data-table';
import { FileDropzone } from '@/components/forms/file-dropzone';
import { LoadingState, ErrorState } from '@/components/feedback/async-state';
import { listDatasets, uploadDataset } from '@/services/dataset.service';
import { formatDate } from '@/utils/format';
import { analyzeBias } from '@/services/dataset.service';

export default function DatasetsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({ name: '', description: '', target_column: '', sensitive_columns: '', feature_columns: '' });

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const response = await listDatasets(true);
        if (active) setDatasets(response.datasets);
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : 'Failed to load datasets');
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
    if (!file) {
      toast.error('Please select a CSV file.');
      return;
    }
    setSubmitting(true);
    try {
      const created = await uploadDataset({
        file,
        name: form.name,
        description: form.description || undefined,
        target_column: form.target_column,
        sensitive_columns: form.sensitive_columns.split(',').map((item) => item.trim()).filter(Boolean),
        feature_columns: form.feature_columns.split(',').map((item) => item.trim()).filter(Boolean),
      });
      toast.success('Dataset uploaded successfully.');
      navigate(`/datasets/${created.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleQuickBias(datasetId: string) {
    const analysis = await analyzeBias(datasetId);
    toast.success(`Bias analysis completed: ${(analysis.bias_score * 100).toFixed(1)}% score.`);
    navigate(`/bias/${datasetId}`);
  }

  if (loading) {
    return <LoadingState lines={7} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="p-6 lg:p-8">
            <CardHeader>
              <div>
                <CardTitle>Upload a dataset</CardTitle>
                <CardDescription>CSV drag-and-drop ingestion mapped to the backend form endpoint.</CardDescription>
              </div>
            </CardHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <FileDropzone file={file} onFileChange={setFile} />
              <div className="grid gap-4 sm:grid-cols-2">
                <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Dataset name" required />
                <Input value={form.target_column} onChange={(event) => setForm({ ...form, target_column: event.target.value })} placeholder="Target column" required />
              </div>
              <Textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Dataset description" />
              <div className="grid gap-4 sm:grid-cols-2">
                <Input value={form.sensitive_columns} onChange={(event) => setForm({ ...form, sensitive_columns: event.target.value })} placeholder="Sensitive columns, comma separated" required />
                <Input value={form.feature_columns} onChange={(event) => setForm({ ...form, feature_columns: event.target.value })} placeholder="Feature columns, comma separated" />
              </div>
              <Button type="submit" disabled={submitting}>{submitting ? 'Uploading…' : 'Upload dataset'}</Button>
            </form>
          </div>
          <div className="border-t border-white/10 bg-white/5 p-6 lg:border-l lg:border-t-0 lg:p-8">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Workflow guidance</p>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              {[
                'Provide the target column and sensitive attributes.',
                'Upload a CSV with clean header names.',
                'Review the preview before moving to bias analysis.',
                'Use the dataset detail page to launch the next step.',
              ].map((item, index) => (
                <div key={item} className="flex gap-3 rounded-2xl border border-white/10 bg-slate-950/20 p-4">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500/20 text-xs text-brand-200">{index + 1}</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Dataset library</CardTitle>
            <CardDescription>Upload history and quick access to analysis actions.</CardDescription>
          </div>
        </CardHeader>
        <DataTable
          columns={[ 'Name', 'Target', 'Sensitive', 'Updated', 'Action' ]}
          rows={datasets.map((dataset) => [
            <button key={`${dataset.id}-name`} onClick={() => navigate(`/datasets/${dataset.id}`)} className="font-medium text-white hover:text-brand-200">{dataset.name}</button>,
            dataset.target_column,
            <div className="flex flex-wrap gap-2">{dataset.sensitive_columns.map((item: string) => <Badge key={item}>{item}</Badge>)}</div>,
            formatDate(dataset.updated_at),
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => navigate(`/datasets/${dataset.id}`)}>Open</Button>
              <Button size="sm" onClick={() => handleQuickBias(dataset.id)}>Analyze bias</Button>
            </div>,
          ])}
          emptyTitle="No datasets uploaded"
          emptyDescription="Upload a CSV above to populate the library and start the workflow."
        />
      </Card>
    </div>
  );
}
