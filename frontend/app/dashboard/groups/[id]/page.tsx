'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { api } from '@/lib/api'
import type { GroupDetail } from '@/lib/types'

export default function GroupDetailPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const params = useParams()
  const groupId = params.id as string
  const [groupData, setGroupData] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated && groupId) {
      loadGroup()
    }
  }, [isAuthenticated, groupId])

  const loadGroup = async () => {
    try {
      const data = await api.getGroup(groupId)
      setGroupData(data)
    } catch (error) {
      console.error('Error loading group:', error)
      router.push('/dashboard/groups')
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

  if (!isAuthenticated || !profile || !groupData) {
    return null
  }

  // Handle both userId (camelCase from type) and user_id (snake_case from API)
  const currentUserMember = groupData.members.find(m =>
    (m as any).userId === profile.id || (m as any).user_id === profile.id
  )
  const isAdmin = currentUserMember?.role === 'admin'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <Link
              href="/dashboard/groups"
              className="text-blue-600 dark:text-blue-400 hover:underline mb-2 inline-block"
            >
              ← Back to Groups
            </Link>
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold">{groupData.group.name}</h1>
                {groupData.group.description && (
                  <p className="text-gray-600 dark:text-gray-300 mt-2">
                    {groupData.group.description}
                  </p>
                )}
              </div>
              {isAdmin && (
                <Link
                  href={`/dashboard/groups/${groupId}/manage`}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Manage Group
                </Link>
              )}
            </div>
          </div>

          {/* Members Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Members</h2>
            <div className="flex flex-wrap gap-2">
              {groupData.members.map((member: any) => {
                const memberId = member.userId || member.user_id
                return (
                  <span
                    key={memberId}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm text-gray-900 dark:text-gray-100"
                  >
                    {member.name}
                    {member.role === 'admin' && (
                      <span className="ml-1 text-xs text-blue-600 dark:text-blue-400">
                        (Admin)
                      </span>
                    )}
                  </span>
                )
              })}
            </div>
          </div>

          {/* Wishlists Section */}
          <div className="space-y-4">
            {groupData.wishlists.length === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
                <p className="text-gray-600 dark:text-gray-300">
                  No wishlist items have been shared with this group yet.
                </p>
              </div>
            ) : (
              groupData.wishlists.map((userWishlist: any) => {
                const userId = userWishlist.userId || userWishlist.user_id
                const userName = userWishlist.userName || userWishlist.user_name
                return (
                  <div key={userId} className="bg-white dark:bg-gray-800 rounded-lg shadow">
                    <div className="p-6">
                      <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">{userName}'s Wishlist</h3>
                      {userWishlist.items.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400 text-sm">No items yet</p>
                      ) : (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                          {userWishlist.items.map((item: any) => {
                            const photoUrl = item.photoUrl || item.photo_url
                            return (
                              <div key={item.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                {photoUrl && (
                                  <img
                                    src={photoUrl}
                                    alt={item.name}
                                    className="w-full h-48 object-cover rounded-lg mb-3"
                                  />
                                )}
                                <h4 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">{item.name}</h4>
                                {item.description && (
                                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                                    {item.description}
                                  </p>
                                )}
                                {item.price && (
                                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                    ${Number(item.price).toFixed(2)}
                                  </p>
                                )}
                                {item.url && (
                                  <a
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                                  >
                                    View Product →
                                  </a>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
