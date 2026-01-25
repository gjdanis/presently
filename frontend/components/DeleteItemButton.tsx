'use client'

import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export function DeleteItemButton({ itemId }: { itemId: string }) {
  const router = useRouter()

  async function handleDelete() {
    if (!confirm('Are you sure you want to delete this item?')) {
      return
    }

    try {
      await api.deleteItem(itemId)
      router.refresh()
    } catch (error) {
      console.error('Error deleting item:', error)
      alert('Failed to delete item')
    }
  }

  return (
    <button
      onClick={handleDelete}
      className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-2"
      title="Delete item"
    >
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
    </button>
  )
}
