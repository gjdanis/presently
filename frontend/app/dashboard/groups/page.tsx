'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { api } from '@/lib/api'
import type { Group } from '@/lib/types'

export default function GroupsPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadGroups()
    }
  }, [isAuthenticated])

  const loadGroups = async () => {
    try {
      const data = await api.getGroups()
      setGroups(data.groups)
    } catch (error) {
      console.error('Error loading groups:', error)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
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
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">My Groups</h1>
            <Link
              href="/dashboard/groups/new"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Create Group
            </Link>
          </div>

          {groups.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <h3 className="text-lg font-semibold mb-2">No groups yet</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Create a group to start sharing wishlists with family and friends.
              </p>
              <Link
                href="/dashboard/groups/new"
                className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Create Your First Group
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groups.map((group) => (
                <Link
                  key={group.id}
                  href={`/dashboard/groups/${group.id}`}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-semibold">{group.name}</h3>
                    {group.role === 'admin' && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                        Admin
                      </span>
                    )}
                  </div>
                  {group.description && (
                    <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                      {group.description}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {group.memberCount} {group.memberCount === 1 ? 'member' : 'members'}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
