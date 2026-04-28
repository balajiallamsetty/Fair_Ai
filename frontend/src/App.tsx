import { useEffect } from 'react';
import { Toaster } from 'sonner';
import { AppRouter } from '@/router';
import { useUIStore } from '@/store/ui.store';

export default function App() {
  const theme = useUIStore((state) => state.theme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    root.dataset.theme = theme;
  }, [theme]);

  return (
    <>
      <AppRouter />
      <Toaster position="top-right" richColors closeButton theme={theme} />
    </>
  );
}
