'use client';

import { useAuth } from '@/lib/context/AuthContext';
import { useTheme } from '@/lib/context/ThemeContext';
import { Moon, Sun, Beaker, LogOut, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Branding */}
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Beaker className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">EGFR Screening</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden flex-1 items-center justify-center gap-8 md:flex">
            {!user && (
              <Link
                href="/"
                className={`text-sm font-medium transition-colors ${
                  isActive('/') ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Home
              </Link>
            )}
          </nav>

          {/* Auth Actions & Theme Toggle */}
          <div className="flex items-center gap-4">
            {!user ? (
              <div className="hidden items-center gap-4 md:flex mr-2">
                <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                  Log in
                </Link>
                <Link href="/register" className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90">
                  Sign up
                </Link>
              </div>
            ) : (
              <div className="hidden items-center gap-4 md:flex mr-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
                  <User className="h-4 w-4" />
                  <span className="max-w-[100px] truncate">{user.name.split(' ')[0]}</span>
                </div>
                <button onClick={logout} className="text-sm font-medium text-muted-foreground hover:text-destructive transition-colors flex items-center gap-1" title="Log out">
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            )}
            <button
              onClick={toggleTheme}
              className="rounded-lg bg-muted p-2 text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
