import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Sparkles } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth.store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function LoginPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true });
  }, [isAuthenticated, navigate]);

  const benefits = useMemo(
    () => ['JWT-backed access control', 'Audit-ready workflows', 'Fairness ops in one place'],
    [],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    try {
      const session = await login({ email, password });
      setSession(session.access_token, session.user);
      toast.success('Welcome back.');
      navigate('/dashboard', { replace: true });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-hero-gradient px-4 py-8 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <motion.section
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-panel relative overflow-hidden p-8 lg:p-12"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.16),transparent_28%)]" />
          <div className="relative z-10 flex h-full flex-col justify-between gap-10">
            <div className="max-w-xl space-y-5">
              <Badge tone="neutral">Fair-AI Guardian Platform</Badge>
              <h1 className="text-4xl font-semibold tracking-tight text-white lg:text-6xl">Enterprise fairness controls with the polish of a premium SaaS.</h1>
              <p className="text-lg leading-8 text-slate-300">
                Secure the full lifecycle from dataset upload to governance review with an interface designed for operators, auditors, and ML teams.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {benefits.map((benefit) => (
                <div key={benefit} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200 backdrop-blur-xl">
                  <Sparkles className="mb-3 h-5 w-5 text-brand-300" />
                  {benefit}
                </div>
              ))}
            </div>
          </div>
        </motion.section>

        <motion.section initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="flex items-center">
          <Card className="w-full p-8 lg:p-10">
            <div className="mb-8 space-y-3">
              <div className="inline-flex rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                <ShieldCheck className="mr-2 h-3.5 w-3.5" /> Secure sign in
              </div>
              <h2 className="text-2xl font-semibold text-white">Sign in to continue</h2>
              <p className="text-sm text-slate-400">Use your JWT-backed account to access datasets, models, monitoring, and governance.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Email</label>
                <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="you@company.com" required />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Password</label>
                <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="••••••••" required />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>

            <p className="mt-6 text-sm text-slate-400">
              New here? <Link to="/auth/register" className="font-medium text-brand-300 hover:text-brand-200">Create an account</Link>
            </p>
          </Card>
        </motion.section>
      </div>
    </div>
  );
}
