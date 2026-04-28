import { useEffect, useState, type FormEvent } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { register } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth.store';
import { toast } from 'sonner';
import type { UserRole } from '@/types/api';

export default function RegisterPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [form, setForm] = useState<{ full_name: string; email: string; password: string; role: UserRole }>({ full_name: '', email: '', password: '', role: 'user' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true });
  }, [isAuthenticated, navigate]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    try {
      await register(form);
      toast.success('Account created. Sign in to continue.');
      navigate('/auth/login', { replace: true });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-hero-gradient px-4 py-8 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <motion.section initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} className="flex items-center">
          <Card className="w-full p-8 lg:p-10">
            <div className="mb-8 space-y-3">
              <Badge tone="neutral">Create workspace access</Badge>
              <h2 className="text-2xl font-semibold text-white">Register a platform account</h2>
              <p className="text-sm text-slate-400">Role-based onboarding keeps your operational scope aligned with the governance controls in the backend.</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Full name</label>
                <Input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} placeholder="Amina Patel" required />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Email</label>
                <Input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} type="email" placeholder="you@company.com" required />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Password</label>
                <Input value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} type="password" placeholder="At least 32 chars in production" required />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Role</label>
                <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })} className="h-11 w-full rounded-2xl border border-white/10 bg-white/5 px-4 text-sm text-slate-100 outline-none">
                  <option value="user">User</option>
                  <option value="auditor">Auditor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating account…' : 'Create account'}
              </Button>
            </form>
            <p className="mt-6 text-sm text-slate-400">
              Already registered? <Link to="/auth/login" className="font-medium text-brand-300 hover:text-brand-200">Sign in</Link>
            </p>
          </Card>
        </motion.section>

        <motion.section initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="glass-panel relative overflow-hidden p-8 lg:p-12">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(6,182,212,0.14),transparent_30%)]" />
          <div className="relative z-10 flex h-full flex-col justify-between gap-8">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Workflow alignment</p>
              <h1 className="mt-4 max-w-xl text-4xl font-semibold tracking-tight text-white lg:text-6xl">Register once. Operate across the full fairness lifecycle.</h1>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {['Upload datasets', 'Analyze bias', 'Train models', 'Resolve reviews'].map((item) => (
                <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
