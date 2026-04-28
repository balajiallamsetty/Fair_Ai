import { Bell, Menu, MoonStar, SunMedium, ChevronLeft, LogOut } from 'lucide-react';
import { motion } from 'framer-motion';
import { NavLink, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { primaryNav } from '@/constants/navigation';
import { useAuthStore } from '@/store/auth.store';
import { useUIStore } from '@/store/ui.store';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { workflowSteps } from '@/theme/designSystem';

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const { theme, toggleTheme, sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div className={cn('min-h-screen text-slate-100 transition-colors', theme === 'dark' ? 'bg-slate-950' : 'bg-slate-100 text-slate-900')}>
      <div className="absolute inset-0 -z-10 bg-hero-gradient" />
      <div className="flex min-h-screen">
        <motion.aside
          animate={{ width: sidebarOpen ? 288 : 88 }}
          transition={{ type: 'spring', stiffness: 220, damping: 28 }}
          className="fixed left-0 top-0 z-20 hidden h-screen border-r border-white/10 bg-slate-950/70 backdrop-blur-xl lg:flex lg:flex-col"
        >
          <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-5">
            <div className={cn('overflow-hidden transition-all', sidebarOpen ? 'opacity-100' : 'opacity-0')}>
              <p className="text-xs uppercase tracking-[0.3em] text-brand-200">Fair-AI Guardian</p>
              <h1 className="mt-1 text-lg font-semibold text-white">Enterprise Control Plane</h1>
            </div>
            <button onClick={toggleSidebar} className="rounded-xl border border-white/10 p-2 text-slate-300 hover:bg-white/5">
              <ChevronLeft className={cn('h-4 w-4 transition-transform', !sidebarOpen && 'rotate-180')} />
            </button>
          </div>
          <nav className="flex flex-1 flex-col gap-2 px-3 py-4">
            {primaryNav.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition',
                    isActive ? 'bg-white/10 text-white shadow-glow' : 'text-slate-300 hover:bg-white/5 hover:text-white',
                  )
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span className={cn('truncate transition-all', sidebarOpen ? 'opacity-100' : 'w-0 opacity-0')}>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-white/10 p-4">
            <div className={cn('rounded-2xl border border-white/10 bg-white/5 p-4', !sidebarOpen && 'p-3')}>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Workflow</p>
              <div className={cn('mt-3 space-y-2 text-xs text-slate-300', !sidebarOpen && 'hidden')}>
                {workflowSteps.map((step, index) => (
                  <div key={step} className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500/20 text-[10px] text-brand-200">{index + 1}</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.aside>

        <div className="flex min-h-screen flex-1 flex-col lg:pl-72">
          <header className="sticky top-0 z-10 border-b border-white/10 bg-slate-950/50 px-4 py-4 backdrop-blur-xl lg:px-8">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <button onClick={toggleSidebar} className="rounded-2xl border border-white/10 p-2 text-slate-300 lg:hidden">
                  <Menu className="h-4 w-4" />
                </button>
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Fair-AI Guardian Platform</p>
                  <h2 className="text-lg font-semibold text-white">Secure fairness operations</h2>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" onClick={toggleTheme}>
                  {theme === 'dark' ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
                  <span className="hidden sm:inline">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
                </Button>
                <Button variant="ghost" size="sm">
                  <Bell className="h-4 w-4" />
                </Button>
                {user ? <div className="hidden rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 md:block">{user.full_name}</div> : null}
                <Button variant="secondary" size="sm" onClick={() => { logout(); navigate('/auth/login'); }}>
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </header>
          <main className="flex-1 px-4 py-6 lg:px-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
