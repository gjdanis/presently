'use client'

import Link from 'next/link'
import { ThemeToggle } from './ThemeToggle'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'

export function DashboardNav({ userName }: { userName: string }) {
  const pathname = usePathname()
  const { signOut } = useAuth()

  const handleSignOut = () => {
    signOut()
    window.location.href = '/'
  }

  return (
    <nav className="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="text-xl font-bold hover:text-blue-600">
              Presently
            </Link>
            <div className="flex gap-4">
              <Link
                href="/dashboard/groups"
                className={pathname.startsWith('/dashboard/groups') ? 'text-blue-600 font-medium' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}
              >
                Groups
              </Link>
              <Link
                href="/dashboard/wishlists"
                className={pathname.startsWith('/dashboard/wishlists') ? 'text-blue-600 font-medium' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}
              >
                My Wishlist
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-700 dark:text-gray-300">Hello, {userName}</span>
            <ThemeToggle />
            <button
              onClick={handleSignOut}
              className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
