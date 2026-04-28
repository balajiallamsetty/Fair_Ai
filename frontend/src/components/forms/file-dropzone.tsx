import { useMemo, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { cn } from '@/utils/cn';

export function FileDropzone({ file, onFileChange }: { file: File | null; onFileChange: (file: File | null) => void }) {
  const [isDragging, setIsDragging] = useState(false);

  const fileName = useMemo(() => file?.name ?? 'Drop a CSV here or browse files', [file]);

  return (
    <label
      onDragEnter={() => setIsDragging(true)}
      onDragLeave={() => setIsDragging(false)}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        const dropped = event.dataTransfer.files?.[0];
        if (dropped) onFileChange(dropped);
      }}
      className={cn(
        'flex min-h-40 cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-white/15 bg-white/5 px-6 py-8 text-center transition hover:border-brand-400/40 hover:bg-white/7',
        isDragging && 'border-brand-400/60 bg-brand-500/10',
      )}
    >
      <UploadCloud className="h-8 w-8 text-brand-300" />
      <div>
        <p className="font-medium text-white">Dataset upload</p>
        <p className="mt-1 text-sm text-slate-400">{fileName}</p>
      </div>
      <input type="file" accept=".csv" className="hidden" onChange={(event) => onFileChange(event.target.files?.[0] ?? null)} />
    </label>
  );
}
