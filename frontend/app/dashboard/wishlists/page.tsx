'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { DraggableWishlist } from '@/components/DraggableWishlist'
import { EditItemModal } from '@/components/EditItemModal'
import { api } from '@/lib/api'
import type { WishlistItem } from '@/lib/types'

export default function WishlistsPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const [items, setItems] = useState<WishlistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [editingItem, setEditingItem] = useState<WishlistItem | null>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadWishlist()
    }
  }, [isAuthenticated])

  async function loadWishlist() {
    try {
      const data = await api.getWishlist()
      setItems(data.items)
    } catch (error) {
      console.error('Error loading wishlist:', error)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-300">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile?.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">My Wishlist</h1>
            <Link
              href="/dashboard/wishlists/new"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Add Item
            </Link>
          </div>

          {items.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">No wishlist items yet</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Start adding items you'd like to receive as gifts!
              </p>
              <Link
                href="/dashboard/wishlists/new"
                className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Add Your First Item
              </Link>
            </div>
          ) : (
            <DraggableWishlist
              initialItems={items}
              onReorder={loadWishlist}
              onEditItem={(item) => setEditingItem(item)}
            />
          )}
        </div>
      </main>

      {/* Edit Item Modal */}
      {editingItem && (
        <EditItemModal
          item={editingItem}
          isOpen={!!editingItem}
          onClose={() => setEditingItem(null)}
          onSaved={loadWishlist}
        />
      )}
    </div>
  )
}
