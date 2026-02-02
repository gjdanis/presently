'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { ActiveInvitation } from '@/lib/types'

type AddMemberFormProps = {
  groupId: string
}

export function AddMemberForm({ groupId }: AddMemberFormProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')
  const [activeInvitations, setActiveInvitations] = useState<ActiveInvitation[]>([])
  const [isLoadingInvitations, setIsLoadingInvitations] = useState(true)
  const [copiedToken, setCopiedToken] = useState<string | null>(null)

  useEffect(() => {
    loadActiveInvitations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId])

  async function loadActiveInvitations() {
    try {
      setIsLoadingInvitations(true)
      const invitations = await api.getActiveInvitations(groupId)
      setActiveInvitations(invitations)
    } catch (err: any) {
      console.error('Error loading invitations:', err)
    } finally {
      setIsLoadingInvitations(false)
    }
  }

  async function handleGenerateLink() {
    setError('')
    setInviteUrl('')
    setIsGenerating(true)

    try {
      const data = await api.createInvitation(groupId)

      // Extract token from backend URL and construct proper frontend URL
      const token = data.invite_url.split('/').pop()
      const frontendUrl = `${window.location.origin}/invite/${token}`

      setInviteUrl(frontendUrl)
      setIsGenerating(false)

      // Reload active invitations to show the new one
      await loadActiveInvitations()
    } catch (err: any) {
      console.error('Error generating invitation:', err)
      setError(err.message || 'Failed to generate invitation link')
      setIsGenerating(false)
    }
  }

  function copyToClipboard(url: string, token: string) {
    navigator.clipboard.writeText(url)
    setCopiedToken(token)
    // Clear the copied state after 2 seconds
    setTimeout(() => {
      setCopiedToken(null)
    }, 2000)
  }

  async function handleRevoke(token: string) {
    if (!confirm('Are you sure you want to revoke this invitation link?')) {
      return
    }

    try {
      await api.revokeInvitation(token)
      await loadActiveInvitations()

      // If the revoked link was the one we just generated, clear it
      if (inviteUrl.includes(token)) {
        setInviteUrl('')
      }
    } catch (err: any) {
      console.error('Error revoking invitation:', err)
      setError(err.message || 'Failed to revoke invitation')
    }
  }

  return (
    <div className="space-y-6">
      {/* Generate New Link Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Invite People to Group</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Generate a shareable link that anyone can use to join this group.
        </p>

        <button
          onClick={handleGenerateLink}
          disabled={isGenerating}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? 'Generating...' : 'Generate Invitation Link'}
        </button>

        {error && (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}

        {inviteUrl && (
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
              Share this link:
            </p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={inviteUrl}
                className="flex-1 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded font-mono"
              />
              <button
                type="button"
                onClick={() => copyToClipboard(inviteUrl, 'new')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium transition-all"
              >
                {copiedToken === 'new' ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Active Invitations List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Active Invitation Links</h3>

        {isLoadingInvitations ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : activeInvitations.length === 0 ? (
          <p className="text-sm text-gray-500">No active invitations</p>
        ) : (
          <div className="space-y-3">
            {activeInvitations.map((invitation) => (
              <div
                key={invitation.token}
                className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      Created by {invitation.created_by}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(invitation.created_at).toLocaleDateString()} • {invitation.current_uses} {invitation.current_uses === 1 ? 'person' : 'people'} joined
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => copyToClipboard(invitation.invite_url.replace(/^https?:\/\/[^/]+/, window.location.origin), invitation.token)}
                      className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-all"
                    >
                      {copiedToken === invitation.token ? '✓ Copied!' : 'Copy Link'}
                    </button>
                    <button
                      onClick={() => handleRevoke(invitation.token)}
                      className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded font-medium"
                    >
                      Revoke
                    </button>
                  </div>
                </div>

                {invitation.accepted_by.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Accepted by:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {invitation.accepted_by.map((accept, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded"
                        >
                          {accept.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
