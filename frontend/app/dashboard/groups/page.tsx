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
      if (process.env.NODE_ENV === 'development') console.error('Error loading groups:', error)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardNav userName={profile?.name || 'User'} />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="flex justify-between items-center mb-6">
              <div className="h-9 w-40 bg-muted rounded animate-pulse" />
              <div className="h-10 w-32 bg-muted rounded-lg animate-pulse" />
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-card rounded-lg shadow p-6 animate-pulse">
                  <div className="h-6 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-4 bg-muted rounded w-1/2 mb-3" />
                  <div className="h-4 bg-muted rounded w-1/3" />
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!isAuthenticated || !profile) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Groups</h1>
            <Link
              href="/dashboard/groups/new"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
            >
              Create Group
            </Link>
          </div>

          {groups.length === 0 ? (
            <div className="bg-card rounded-lg shadow p-8 text-center border border-border">
              <h3 className="text-lg font-semibold mb-2">No groups yet</h3>
              <p className="text-muted-foreground mb-4">
                Create a group to start sharing wishlists with family and friends.
              </p>
              <Link
                href="/dashboard/groups/new"
                className="inline-block px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
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
                  className="bg-card rounded-lg shadow p-6 hover:shadow-lg transition-shadow border border-border"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-semibold">{group.name}</h3>
                    {group.role === 'admin' && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                        Admin
                      </span>
                    )}
                  </div>
                  {group.description && (
                    <p className="text-muted-foreground text-sm mb-4">
                      {group.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {group.member_count} {group.member_count === 1 ? 'member' : 'members'}
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
