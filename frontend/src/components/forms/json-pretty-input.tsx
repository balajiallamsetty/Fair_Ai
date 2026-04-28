import { Textarea } from '@/components/ui/textarea';

export function JsonPrettyInput({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder?: string }) {
  return <Textarea value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder ?? '{"feature": "value"}'} className="font-mono text-xs leading-6" />;
}
