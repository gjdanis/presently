'use client'

import { useState } from 'react'
import { api } from '@/lib/api'

type QuickInviteProps = {
  groupId: string
}

export function QuickInvite({ groupId }: QuickInviteProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')
  const [copied, setCopied] = useState(false)

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
    } catch (err: any) {
      console.error('Error generating invitation:', err)
      setError(err.message || 'Failed to generate invitation link')
      setIsGenerating(false)
    }
  }

  function copyToClipboard(url: string) {
    navigator.clipboard.writeText(url)
    setCopied(true)
    // Clear the copied state after 2 seconds
    setTimeout(() => {
      setCopied(false)
    }, 2000)
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">Generate Invitation Link</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Create a shareable link that anyone can use to join this group.
        </p>

        <button
          onClick={handleGenerateLink}
          disabled={isGenerating}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? 'Generating...' : 'Generate Link'}
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
                onClick={() => copyToClipboard(inviteUrl)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium transition-all"
              >
                {copied ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
