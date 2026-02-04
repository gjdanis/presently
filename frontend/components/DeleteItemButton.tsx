'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { ConfirmModal } from '@/components/ConfirmModal'

export function DeleteItemButton({
  itemId,
  onDelete
}: {
  itemId: string
  onDelete?: () => void
}) {
  const router = useRouter()
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)

  async function performDelete() {
    setDeleting(true)
    try {
      await api.deleteItem(itemId)
      if (onDelete) onDelete()
      router.refresh()
    } catch (err) {
      if (process.env.NODE_ENV === 'development') console.error('Error deleting item:', err)
      setError('Failed to delete item')
    } finally {
      setDeleting(false)
      setShowConfirm(false)
    }
  }

  return (
    <span className="inline-flex flex-col items-start">
      {error && <span className="text-xs text-red-600 dark:text-red-400 mb-1">{error}</span>}
      <button
        onClick={() => setShowConfirm(true)}
      disabled={deleting}
      className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-2 disabled:opacity-50 disabled:cursor-not-allowed"
      title="Delete item"
    >
      {deleting ? (
        <svg
          className="w-5 h-5 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      )}
    </button>
      <ConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={performDelete}
        title="Delete item"
        message="Are you sure you want to delete this item?"
        confirmLabel="Delete"
        variant="danger"
        loading={deleting}
      />
    </span>
  )
}
