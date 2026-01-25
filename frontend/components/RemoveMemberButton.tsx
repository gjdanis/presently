'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { api } from '@/lib/api'

type RemoveMemberButtonProps = {
  groupId: string
  userId: string
  userName: string
}

export function RemoveMemberButton({
  groupId,
  userId,
  userName,
}: RemoveMemberButtonProps) {
  const router = useRouter()
  const [isRemoving, setIsRemoving] = useState(false)

  async function handleRemove() {
    if (!confirm(`Are you sure you want to remove ${userName} from this group?`)) {
      return
    }

    setIsRemoving(true)

    try {
      await api.removeMember(groupId, userId)
      router.refresh()
    } catch (error) {
      console.error('Error removing member:', error)
      alert('Failed to remove member')
      setIsRemoving(false)
    }
  }

  return (
    <button
      onClick={handleRemove}
      disabled={isRemoving}
      className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isRemoving ? 'Removing...' : 'Remove'}
    </button>
  )
}
