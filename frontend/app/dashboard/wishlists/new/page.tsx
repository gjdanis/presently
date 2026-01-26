'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { ImageUpload } from '@/components/ImageUpload'
import { api } from '@/lib/api'

type Group = {
  id: string
  name: string
}

export default function NewWishlistItemPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()
  const [loading, setLoading] = useState(false)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroups, setSelectedGroups] = useState<string[]>([])

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url: '',
    price: '',
  })
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadGroups()
    }
  }, [isAuthenticated])

  async function loadGroups() {
    try {
      const data = await api.getGroups()
      setGroups(data.groups.map((g: any) => ({ id: g.id, name: g.name })))
    } catch (error) {
      console.error('Error loading groups:', error)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    setLoading(true)

    try {
      await api.createItem({
        name: formData.name,
        description: formData.description || undefined,
        url: formData.url || undefined,
        price: formData.price ? parseFloat(formData.price) : undefined,
        photo_url: photoUrl || undefined,
        rank: 0,
        group_ids: selectedGroups,
      })

      router.push('/dashboard/wishlists')
    } catch (error: any) {
      console.error('Error creating item:', error)
      const message = error?.response?.data?.error || 'Failed to create item'
      alert(message)
      setLoading(false)
    }
  }

  function toggleGroup(groupId: string) {
    setSelectedGroups((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    )
  }

  if (isLoading) {
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-6 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-gray-900 dark:text-gray-100">Add Wishlist Item</h1>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6 sm:p-8">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">
              Item Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Wireless Headphones"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Any specific details, color preferences, etc."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">
              URL (link to product)
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://..."
            />
          </div>

          <ImageUpload
            currentImageUrl={photoUrl}
            onImageChange={setPhotoUrl}
          />

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">
              Estimated Price
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-3 text-gray-900 dark:text-gray-100">
              Share with Groups (optional)
            </label>
            {groups.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                You're not a member of any groups yet. This item will be private until you share it.
              </p>
            ) : (
              <>
                <div className="space-y-2">
                  {groups.map((group) => (
                    <label
                      key={group.id}
                      className="flex items-center p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <input
                        type="checkbox"
                        checked={selectedGroups.includes(group.id)}
                        onChange={() => toggleGroup(group.id)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="ml-3 text-gray-900 dark:text-gray-100">{group.name}</span>
                    </label>
                  ))}
                </div>
                {selectedGroups.length === 0 && (
                  <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">
                    No groups selected - this item will be private until you share it with a group
                  </p>
                )}
              </>
            )}
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Add Item'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/dashboard/wishlists')}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
