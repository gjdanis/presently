'use client'

import { useState, useEffect, useRef, FormEvent } from 'react'
import { api } from '@/lib/api'
import { changePassword } from '@/lib/auth'

interface EditProfileModalProps {
  isOpen: boolean
  onClose: () => void
  currentName: string
  currentEmail: string
  onUpdate: (newName: string) => void
}

export function EditProfileModal({ isOpen, onClose, currentName, currentEmail, onUpdate }: EditProfileModalProps) {
  const [name, setName] = useState(currentName)
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setName(currentName)
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setError('')
      setSuccess('')
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen, currentName])

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Name cannot be empty')
      return
    }

    // Validate password fields only if user is attempting to change password
    // We consider password change if new password or confirm password is filled
    const isChangingPassword = newPassword || confirmPassword
    if (isChangingPassword) {
      if (!oldPassword) {
        setError('Please enter your current password')
        return
      }
      if (!newPassword) {
        setError('Please enter a new password')
        return
      }
      if (newPassword.length < 8) {
        setError('New password must be at least 8 characters')
        return
      }
      if (newPassword !== confirmPassword) {
        setError('New passwords do not match')
        return
      }
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      // Update name
      await api.updateProfile(name.trim())
      onUpdate(name.trim())

      // Change password if requested
      if (isChangingPassword) {
        await changePassword(oldPassword, newPassword)
        setSuccess('Profile and password updated successfully!')
      } else {
        setSuccess('Profile updated successfully!')
      }

      // Close after a brief delay to show success message
      setTimeout(() => onClose(), 1500)
    } catch (err: any) {
      console.error('Error updating profile:', err)
      // Provide more helpful error messages for common Cognito errors
      let errorMessage = err.message || 'Failed to update profile'
      if (errorMessage.includes('Incorrect username or password')) {
        errorMessage = 'Current password is incorrect. Please check and try again.'
      } else if (errorMessage.includes('not authenticated')) {
        errorMessage = 'Session expired. Please log out and log back in.'
      } else if (errorMessage.includes('Attempt limit exceeded')) {
        errorMessage = 'Too many failed attempts. Please wait a few minutes and try again.'
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-card rounded-lg shadow-xl max-w-md w-full border border-border">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Edit Profile</h2>

            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium mb-2">
                  Name
                </label>
                <input
                  ref={inputRef}
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={loading}
                  autoComplete="name"
                />
              </div>

              <div className="mb-4 pt-4 border-t border-border">
                <p className="text-sm font-medium mb-3">Change Password (optional)</p>

                {/* Hidden email field for password managers */}
                <input
                  type="email"
                  value={currentEmail}
                  autoComplete="username"
                  readOnly
                  className="sr-only"
                  tabIndex={-1}
                  aria-hidden="true"
                />

                <div className="mb-3">
                  <label htmlFor="oldPassword" className="block text-sm mb-2">
                    Current Password
                  </label>
                  <input
                    id="oldPassword"
                    type="password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    disabled={loading}
                    placeholder="Enter current password"
                    autoComplete="current-password"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="newPassword" className="block text-sm mb-2">
                    New Password
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    disabled={loading}
                    placeholder="Minimum 8 characters"
                    autoComplete="new-password"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="confirmPassword" className="block text-sm mb-2">
                    Confirm New Password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    disabled={loading}
                    placeholder="Re-enter new password"
                    autoComplete="new-password"
                  />
                </div>
              </div>

              {error && (
                <p className="text-sm text-destructive mb-4">{error}</p>
              )}

              {success && (
                <p className="text-sm text-green-600 dark:text-green-400 mb-4">{success}</p>
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:opacity-90"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                  disabled={loading || !name.trim()}
                >
                  {loading ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
