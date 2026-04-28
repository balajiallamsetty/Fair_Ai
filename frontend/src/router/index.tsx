import { Suspense, lazy } from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/app-shell';
import { PageTransition } from '@/components/animations/page-transition';
import { useAuthStore } from '@/store/auth.store';
import { LoadingState } from '@/components/feedback/async-state';

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const DatasetsPage = lazy(() => import('@/pages/datasets/DatasetsPage'));
const DatasetDetailPage = lazy(() => import('@/pages/datasets/DatasetDetailPage'));
const BiasAnalysisPage = lazy(() => import('@/pages/bias/BiasAnalysisPage'));
const ModelsPage = lazy(() => import('@/pages/models/ModelsPage'));
const ModelDetailPage = lazy(() => import('@/pages/models/ModelDetailPage'));
const MonitoringPage = lazy(() => import('@/pages/monitoring/MonitoringPage'));
const GovernancePage = lazy(() => import('@/pages/governance/GovernancePage'));
const NotFoundPage = lazy(() => import('@/pages/errors/NotFoundPage'));

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }
  return <Outlet />;
}

function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}

function AppLayout() {
  return (
    <AppShell>
      <PageTransition>
        <Outlet />
      </PageTransition>
    </AppShell>
  );
}

function RootRedirect() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return <Navigate to={isAuthenticated ? '/dashboard' : '/auth/login'} replace />;
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="min-h-screen bg-slate-950 p-6"><LoadingState lines={6} /></div>}>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route element={<PublicOnlyRoute />}>
            <Route path="/auth/login" element={<LoginPage />} />
            <Route path="/auth/register" element={<RegisterPage />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/datasets" element={<DatasetsPage />} />
              <Route path="/datasets/:datasetId" element={<DatasetDetailPage />} />
              <Route path="/bias" element={<BiasAnalysisPage />} />
              <Route path="/bias/:datasetId" element={<BiasAnalysisPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/models/:modelId" element={<ModelDetailPage />} />
              <Route path="/monitoring" element={<MonitoringPage />} />
              <Route path="/governance" element={<GovernancePage />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
