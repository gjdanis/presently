'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { RemoveMemberButton } from '@/components/RemoveMemberButton'
import { AddMemberForm } from '@/components/AddMemberForm'
import { ConfirmModal } from '@/components/ConfirmModal'
import { api } from '@/lib/api'
import type { GroupDetail } from '@/lib/types'

export default function ManageGroupPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const params = useParams()
  const groupId = params.id as string
  const [groupData, setGroupData] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated && groupId) {
      loadGroup()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, groupId])

  const loadGroup = async () => {
    try {
      const data = await api.getGroup(groupId)

      // Check if user is admin (handle both userId and user_id)
      const currentUserMember = data.members.find((m: any) =>
        m.userId === profile?.id || m.user_id === profile?.id
      )
      if (!currentUserMember || currentUserMember.role !== 'admin') {
        router.push(`/dashboard/groups/${groupId}`)
        return
      }

      setGroupData(data)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading group:', error)
      router.push('/dashboard/groups')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteGroup = async () => {
    setDeleting(true)
    try {
      await api.deleteGroup(groupId)
      setShowDeleteConfirm(false)
      router.push('/dashboard/groups')
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error deleting group:', error)
      setDeleteError('Failed to delete group')
    } finally {
      setDeleting(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardNav userName={profile?.name || 'User'} />
        <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="h-8 w-64 bg-muted rounded animate-pulse mb-6" />
            <div className="bg-card rounded-lg shadow p-6 animate-pulse space-y-4">
              <div className="h-6 bg-muted rounded w-1/3" />
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 bg-muted rounded" />
              ))}
            </div>
            <div className="bg-card rounded-lg shadow p-6 mt-6 animate-pulse">
              <div className="h-6 bg-muted rounded w-1/4 mb-4" />
              <div className="h-10 bg-muted rounded w-32" />
            </div>
          </div>
        </main>
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
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Members ({groupData.members.length})</h2>
            <div className="space-y-3">
              {groupData.members.map((member: any) => {
                const memberId = member.userId || member.user_id
                return (
                  <div
                    key={memberId}
                    className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{member.name}</p>
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
                      {memberId !== profile.id && (
                        <RemoveMemberButton
                          groupId={groupId}
                          userId={memberId}
                          userName={member.name}
                          onSuccess={loadGroup}
                        />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Add Member Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Add Members</h2>
            <AddMemberForm groupId={groupId} />
          </div>

          {/* Danger Zone */}
          <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-6 mt-6">
            <h2 className="text-xl font-semibold mb-2 text-red-900 dark:text-red-200">Danger Zone</h2>
            <p className="text-red-700 dark:text-red-300 mb-4 text-sm">
              Once you delete a group, there is no going back. All wishlist associations will be removed.
            </p>
            {deleteError && (
              <p className="text-red-600 dark:text-red-400 text-sm mb-4">{deleteError}</p>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={deleting}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete Group
            </button>
          </div>
        </div>
      </main>
      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteGroup}
        title="Delete group"
        message={`Are you sure you want to delete "${groupData?.group.name}"? This action cannot be undone.`}
        confirmLabel="Delete Group"
        variant="danger"
        loading={deleting}
      />
    </div>
  )
}
