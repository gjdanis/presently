'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ThemeToggle } from './ThemeToggle'
import { HelpDialog } from './HelpDialog'
import { FeedbackDialog } from './FeedbackDialog'
import { EditProfileModal } from './EditProfileModal'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'

export function DashboardNav({ userName }: { userName: string }) {
  const pathname = usePathname()
  const { signOut, profile } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [showEditProfile, setShowEditProfile] = useState(false)
  const bmcUrl = process.env.NEXT_PUBLIC_BMC_URL
  const [currentName, setCurrentName] = useState(userName)

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
            <button
              onClick={() => setShowEditProfile(true)}
              className="text-muted-foreground hover:text-foreground hover:underline"
              title="Edit profile"
            >
              Hello, {currentName}
            </button>
            <button
              onClick={() => setShowHelp(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
              aria-label="Help"
              title="Help"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button
              onClick={() => setShowFeedback(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
              aria-label="Give feedback"
              title="Give feedback"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </button>
            {bmcUrl && (
              <a
                href={bmcUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
                aria-label="Buy me a coffee"
                title="Buy me a coffee"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8zM6 1v3M10 1v3M14 1v3" />
                </svg>
              </a>
            )}
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
            <button
              onClick={() => setShowHelp(true)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent"
              aria-label="Help"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
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
              <button
                onClick={() => { setMenuOpen(false); setShowEditProfile(true); }}
                className="text-left px-4 py-2 text-muted-foreground hover:text-foreground rounded-lg border-t border-border mt-2"
              >
                Hello, {currentName}
              </button>
              <button
                onClick={() => { setMenuOpen(false); setShowFeedback(true); }}
                className="text-left px-4 py-2 text-sm text-muted-foreground hover:text-foreground rounded-lg"
              >
                Give Feedback
              </button>
              {bmcUrl && (
                <a
                  href={bmcUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 text-sm text-muted-foreground hover:text-foreground rounded-lg"
                >
                  Buy me a coffee ☕
                </a>
              )}
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

      <HelpDialog isOpen={showHelp} onClose={() => setShowHelp(false)} />
      <FeedbackDialog isOpen={showFeedback} onClose={() => setShowFeedback(false)} />
      <EditProfileModal
        isOpen={showEditProfile}
        onClose={() => setShowEditProfile(false)}
        currentName={currentName}
        currentEmail={profile?.email || ''}
        onUpdate={(newName) => setCurrentName(newName)}
      />
    </nav>
  )
}
