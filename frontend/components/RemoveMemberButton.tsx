'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { ConfirmModal } from '@/components/ConfirmModal'

type RemoveMemberButtonProps = {
  groupId: string
  userId: string
  userName: string
  onSuccess?: () => void
}

export function RemoveMemberButton({
  groupId,
  userId,
  userName,
  onSuccess,
}: RemoveMemberButtonProps) {
  const [isRemoving, setIsRemoving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)

  async function performRemove() {
    setIsRemoving(true)
    try {
      await api.removeMember(groupId, userId)
      if (onSuccess) onSuccess()
      setShowConfirm(false)
    } catch (err) {
      if (process.env.NODE_ENV === 'development') console.error('Error removing member:', err)
      setError('Failed to remove member')
    } finally {
      setIsRemoving(false)
      setShowConfirm(false)
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
      <button
        onClick={() => setShowConfirm(true)}
        disabled={isRemoving}
        className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Remove
      </button>
      <ConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={performRemove}
        title="Remove member"
        message={`Are you sure you want to remove ${userName} from this group?`}
        confirmLabel="Remove"
        variant="danger"
        loading={isRemoving}
      />
    </span>
  )
}
