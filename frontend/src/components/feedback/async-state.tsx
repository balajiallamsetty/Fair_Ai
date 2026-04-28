import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function LoadingState({ lines = 4 }: { lines?: number }) {
  return (
    <Card className="space-y-4">
      <Skeleton className="h-6 w-40" />
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className="h-4 w-full" />
      ))}
    </Card>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Card className="space-y-4 border-rose-400/20 bg-rose-500/5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-rose-300/70">Request failed</p>
        <h3 className="mt-2 text-lg font-semibold text-white">{message}</h3>
      </div>
      {onRetry ? <Button onClick={onRetry}>Retry</Button> : null}
    </Card>
  );
}
