'use client'

import { useState, useEffect, useRef } from 'react'
import { ImageUpload } from '@/components/ImageUpload'
import { ConfirmModal } from '@/components/ConfirmModal'
import { api } from '@/lib/api'
import type { WishlistItem, Group } from '@/lib/types'

type EditItemModalProps = {
  item: WishlistItem
  isOpen: boolean
  onClose: () => void
  onSaved?: () => void
}

export function EditItemModal({ item, isOpen, onClose, onSaved }: EditItemModalProps) {
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const [selectedGroups, setSelectedGroups] = useState<string[]>(
    item.groups?.map((g) => g.id) || []
  )
  const [groupsChanged, setGroupsChanged] = useState(false)

  const [formData, setFormData] = useState({
    name: item.name,
    description: item.description || '',
    url: item.url || '',
    price: item.price ? item.price.toString() : '',
  })
  const [photoUrl, setPhotoUrl] = useState<string | null>(item.photo_url || null)
  const [photoUrlChanged, setPhotoUrlChanged] = useState(false)
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(item.photo_url || null)

  useEffect(() => {
    if (isOpen) {
      const initialGroups = item.groups?.map((g) => g.id) || []
      setSaveError(null)
      setDeleteError(null)
      loadGroups()
      closeButtonRef.current?.focus()
      // Reset form when modal opens with new item
      setFormData({
        name: item.name,
        description: item.description || '',
        url: item.url || '',
        price: item.price ? item.price.toString() : '',
      })
      setPhotoUrl(item.photo_url || null)
      setCurrentImageUrl(item.photo_url || null)
      setPhotoUrlChanged(false)
      setSelectedGroups(initialGroups)
      setGroupsChanged(false)
    }
  }, [isOpen, item])

  async function loadGroups() {
    try {
      const data = await api.getGroups()
      setGroups(data.groups)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading groups:', error)
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
        // Only send photo_url if it was actually changed via upload
        ...(photoUrlChanged && { photo_url: photoUrl }),
        // Always send group_ids to ensure they're preserved
        group_ids: selectedGroups,
      })

      // Call onSaved callback to refresh data
      if (onSaved) {
        onSaved()
      }

      onClose()
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error updating item:', error)
      setSaveError('Failed to update item')
    } finally {
      setSaving(false)
    }
  }

  function handlePhotoChange(url: string | null) {
    setPhotoUrl(url)
    setPhotoUrlChanged(true)
    // Don't update currentImageUrl - ImageUpload handles its own preview
  }

  function toggleGroup(groupId: string) {
    setGroupsChanged(true)
    setSelectedGroups((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    )
  }

  async function performDelete() {
    setDeleting(true)
    try {
      await api.deleteItem(item.id)
      if (onSaved) onSaved()
      setShowDeleteConfirm(false)
      onClose()
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error deleting item:', error)
      setDeleteError('Failed to delete item')
    } finally {
      setDeleting(false)
    }
  }

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Edit Item
            </h2>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form Content */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {saveError && (
              <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                {saveError}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">
                Item Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
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
                className="input"
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
                className="input"
              />
            </div>

            <ImageUpload
              currentImageUrl={currentImageUrl}
              onImageChange={handlePhotoChange}
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
                className="input"
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

            {deleteError && (
              <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                {deleteError}
              </div>
            )}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                disabled={deleting || saving}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
              <div className="flex-1"></div>
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving || deleting}
                className="px-6 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={performDelete}
        title="Delete item"
        message="Are you sure you want to delete this item? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        loading={deleting}
      />
    </div>
  )
}
