'use client'

import { useState } from 'react'
import { api } from '@/lib/api'

type AddMemberFormProps = {
  groupId: string
}

export function AddMemberForm({ groupId }: AddMemberFormProps) {
  const [email, setEmail] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setInviteUrl('')
    setIsAdding(true)

    try {
      const data = await api.inviteMember(groupId, { email })

      setEmail('')
      setIsAdding(false)

      if (data.addedDirectly) {
        setSuccess('User added to group successfully!')
      } else {
        // Extract token from backend URL and construct proper frontend URL
        const token = data.inviteUrl.split('/').pop()
        const frontendUrl = `${window.location.origin}/invite/${token}`

        setSuccess('Invitation created! Share this link with them:')
        setInviteUrl(frontendUrl)
      }
    } catch (err: any) {
      console.error('Error sending invitation:', err)
      setError(err.message || 'Failed to send invitation')
      setIsAdding(false)
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(inviteUrl)
    setSuccess('Link copied to clipboard!')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium mb-2"
        >
          Email Address
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          required
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        />
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
        {success && (
          <p className="mt-2 text-sm text-green-600 dark:text-green-400">{success}</p>
        )}
        {inviteUrl && (
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={inviteUrl}
                className="flex-1 px-2 py-1 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded"
              />
              <button
                type="button"
                onClick={copyToClipboard}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium"
              >
                Copy
              </button>
            </div>
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={isAdding}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isAdding ? 'Sending...' : 'Send Invitation'}
      </button>
    </form>
  )
}
