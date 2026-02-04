'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ThemeToggle } from './ThemeToggle'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'

export function DashboardNav({ userName }: { userName: string }) {
  const pathname = usePathname()
  const { signOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleSignOut = () => {
    signOut()
    window.location.href = '/'
  }

  const linkClass = (path: string) =>
    pathname.startsWith(path) ? 'text-primary font-medium' : 'text-muted-foreground hover:text-foreground'

  return (
    <nav className="sticky top-0 z-50 bg-card shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="text-xl font-bold text-card-foreground hover:text-primary">
              Presently
            </Link>
            {/* Desktop nav */}
            <div className="hidden md:flex gap-4">
              <Link href="/dashboard/groups" className={linkClass('/dashboard/groups')}>
                Groups
              </Link>
              <Link href="/dashboard/wishlists" className={linkClass('/dashboard/wishlists')}>
                Wishlist
              </Link>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-4">
            <span className="text-muted-foreground">Hello, {userName}</span>
            <ThemeToggle />
            <button
              onClick={handleSignOut}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Sign Out
            </button>
          </div>
          {/* Mobile hamburger */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={menuOpen}
            >
              {menuOpen ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l18 18" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
        {/* Mobile dropdown */}
        {menuOpen && (
          <div className="md:hidden py-4 border-t border-border">
            <div className="flex flex-col gap-2">
              <Link
                href="/dashboard/groups"
                onClick={() => setMenuOpen(false)}
                className={`block px-4 py-2 rounded-lg ${linkClass('/dashboard/groups')}`}
              >
                Groups
              </Link>
              <Link
                href="/dashboard/wishlists"
                onClick={() => setMenuOpen(false)}
                className={`block px-4 py-2 rounded-lg ${linkClass('/dashboard/wishlists')}`}
              >
                Wishlist
              </Link>
              <div className="px-4 py-2 text-muted-foreground border-t border-border mt-2 pt-2">
                Hello, {userName}
              </div>
              <button
                onClick={() => { setMenuOpen(false); handleSignOut(); }}
                className="text-left px-4 py-2 text-sm text-muted-foreground hover:text-foreground rounded-lg"
              >
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
