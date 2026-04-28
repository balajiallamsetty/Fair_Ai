import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function NotFoundPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-slate-950 px-4">
      <Card className="max-w-md text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">404</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Page not found</h1>
        <p className="mt-3 text-sm text-slate-400">The route you requested is not available in the Fair-AI Guardian frontend.</p>
        <Button className="mt-6" onClick={() => window.location.assign('/dashboard')}>
          Go to dashboard
        </Button>
      </Card>
    </div>
  );
}
