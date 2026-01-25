'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ImageUpload } from '@/components/ImageUpload'
import { api } from '@/lib/api'
import type { WishlistItem, Group } from '@/lib/types'

export function EditItemForm({ item }: { item: WishlistItem }) {
  const router = useRouter()
  const [saving, setSaving] = useState(false)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroups, setSelectedGroups] = useState<string[]>(
    item.groups.map((g) => g.id)
  )

  const [formData, setFormData] = useState({
    name: item.name,
    description: item.description || '',
    url: item.url || '',
    price: item.price ? item.price.toString() : '',
  })
  const [photoUrl, setPhotoUrl] = useState<string | null>(item.photo_url || null)

  useEffect(() => {
    loadGroups()
  }, [])

  async function loadGroups() {
    try {
      const data = await api.getGroups()
      setGroups(data.groups)
    } catch (error) {
      console.error('Error loading groups:', error)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)

    try {
      await api.updateItem(item.id, {
        name: formData.name,
        description: formData.description || null,
        url: formData.url || null,
        price: formData.price ? parseFloat(formData.price) : null,
        photo_url: photoUrl,
        group_ids: selectedGroups,
      })

      router.push('/dashboard/wishlists')
    } catch (error) {
      console.error('Error updating item:', error)
      alert('Failed to update item')
      setSaving(false)
    }
  }

  function toggleGroup(groupId: string) {
    setSelectedGroups((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    )
  }

  return (
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
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-3 text-gray-900 dark:text-gray-100">
          Share with Groups
        </label>
        {groups.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            You're not a member of any groups yet.
          </p>
        ) : (
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
        )}
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={saving}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Changes'}
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
  )
}
