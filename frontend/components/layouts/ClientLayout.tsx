'use client';

import { ThemeProvider } from '@/lib/context/ThemeContext';
import { AuthProvider } from '@/lib/context/AuthContext';
import { ScreeningProvider } from '@/lib/context/ScreeningContext';
import { DockingProvider } from '@/lib/context/DockingContext';
import { Header } from './Header';

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ScreeningProvider>
          <DockingProvider>
            <Header />
            <main className="min-h-screen">
              {children}
            </main>
          </DockingProvider>
        </ScreeningProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
