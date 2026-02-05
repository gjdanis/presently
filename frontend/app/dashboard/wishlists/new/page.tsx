'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { ImageUpload } from '@/components/ImageUpload'
import { api } from '@/lib/api'
import type { Group } from '@/lib/types'

export default function NewWishlistItemPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
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
  const [submitError, setSubmitError] = useState<string | null>(null)

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
      setGroups(data.groups)

      // Pre-select group from query parameter
      const groupId = searchParams.get('group')
      if (groupId && data.groups.some((g: any) => g.id === groupId)) {
        setSelectedGroups([groupId])
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading groups:', error)
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

      // If accessed from a group, redirect back to that group
      const groupId = searchParams.get('group')
      if (groupId) {
        router.push(`/dashboard/groups/${groupId}`)
      } else {
        router.push('/dashboard/wishlists')
      }
    } catch (error: any) {
      if (process.env.NODE_ENV === 'development') console.error('Error creating item:', error)
      const message = error?.message || error?.response?.data?.detail || 'Failed to create item'
      setSubmitError(message)
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
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-background py-6 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6 text-foreground">Add Wishlist Item</h1>

        <form onSubmit={handleSubmit} className="space-y-6 bg-card rounded-lg shadow p-6 sm:p-8">
          {submitError && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg text-sm">
              {submitError}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">
              Item Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              placeholder="e.g., Wireless Headphones"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="input"
              placeholder="Any specific details, color preferences, etc."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">
              URL (link to product)
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="input"
              placeholder="https://..."
            />
          </div>

          <ImageUpload
            currentImageUrl={photoUrl}
            onImageChange={setPhotoUrl}
          />

          <div>
            <label className="block text-sm font-medium mb-2 text-foreground">
              Estimated Price
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              className="input"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-3 text-foreground">
              Share with Groups (optional)
            </label>
            {groups.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                You're not a member of any groups yet. This item will be private until you share it.
              </p>
            ) : (
              <>
                <div className="space-y-2">
                  {groups.map((group) => (
                    <label
                      key={group.id}
                      className="flex items-center p-3 border border-border rounded-lg cursor-pointer hover:bg-accent"
                    >
                      <input
                        type="checkbox"
                        checked={selectedGroups.includes(group.id)}
                        onChange={() => toggleGroup(group.id)}
                        className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
                      />
                      <span className="ml-3 text-foreground">{group.name}</span>
                    </label>
                  ))}
                </div>
                {selectedGroups.length === 0 && (
                  <p className="text-muted-foreground text-sm mt-2">
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
              className="flex-1 bg-primary text-primary-foreground font-medium py-2 px-4 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Add Item'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/dashboard/wishlists')}
              className="px-6 py-2 border border-border rounded-lg hover:bg-accent text-foreground"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
