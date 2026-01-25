'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { DashboardNav } from '@/components/DashboardNav'
import Link from 'next/link'

export default function DashboardPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || !profile) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Welcome to Presently!</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              You're all set up. Let's start building your groups and wishlists.
            </p>
            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <Link
                  href="/dashboard/groups"
                  className="p-6 border-2 border-blue-500 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  <h3 className="font-semibold text-lg mb-2">Manage Groups</h3>
                  <p className="text-gray-600 dark:text-gray-300 text-sm">
                    Create and manage your wishlist groups
                  </p>
                </Link>
                <Link
                  href="/dashboard/wishlists"
                  className="p-6 border-2 border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors"
                >
                  <h3 className="font-semibold text-lg mb-2">My Wishlists</h3>
                  <p className="text-gray-600 dark:text-gray-300 text-sm">
                    View and edit your wishlist items
                  </p>
                </Link>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-semibold">Next Steps:</h3>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                  <li>Create or join a group</li>
                  <li>Add items to your wishlist</li>
                  <li>View other members' wishlists</li>
                  <li>Mark items as purchased</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
