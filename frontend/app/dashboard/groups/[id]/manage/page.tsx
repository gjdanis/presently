'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { RemoveMemberButton } from '@/components/RemoveMemberButton'
import { AddMemberForm } from '@/components/AddMemberForm'
import { api } from '@/lib/api'
import type { GroupDetail } from '@/lib/types'

export default function ManageGroupPage() {
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

      // Check if user is admin
      const currentUserMember = data.members.find(m => m.userId === profile?.id)
      if (!currentUserMember || currentUserMember.role !== 'admin') {
        router.push(`/dashboard/groups/${groupId}`)
        return
      }

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <Link
              href={`/dashboard/groups/${groupId}`}
              className="text-blue-600 dark:text-blue-400 hover:underline mb-2 inline-block"
            >
              ← Back to Group
            </Link>
            <h1 className="text-3xl font-bold">Manage Group</h1>
            <p className="text-gray-600 dark:text-gray-300 mt-2">
              {groupData.group.name}
            </p>
          </div>

          {/* Group Info Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Group Information</h2>
            <div className="space-y-2">
              <div>
                <label className="text-sm text-gray-500 dark:text-gray-400">Name</label>
                <p className="font-medium">{groupData.group.name}</p>
              </div>
              {groupData.group.description && (
                <div>
                  <label className="text-sm text-gray-500 dark:text-gray-400">Description</label>
                  <p>{groupData.group.description}</p>
                </div>
              )}
            </div>
          </div>

          {/* Members Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Members ({groupData.members.length})</h2>
            <div className="space-y-3">
              {groupData.members.map((member) => (
                <div
                  key={member.userId}
                  className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                >
                  <div>
                    <p className="font-medium">{member.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {member.email}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        member.role === 'admin'
                          ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                      }`}
                    >
                      {member.role}
                    </span>
                    {member.userId !== profile.id && (
                      <RemoveMemberButton
                        groupId={groupId}
                        userId={member.userId}
                        userName={member.name}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add Member Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Add Members</h2>
            <AddMemberForm groupId={groupId} />
          </div>
        </div>
      </main>
    </div>
  )
}
