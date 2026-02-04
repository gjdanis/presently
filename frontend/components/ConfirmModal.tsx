'use client'

import { useEffect, useRef } from 'react'

type ConfirmModalProps = {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  loading?: boolean
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
}: ConfirmModalProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen) cancelButtonRef.current?.focus()
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const confirmClass =
    variant === 'danger'
      ? 'bg-destructive text-destructive-foreground hover:opacity-90'
      : 'bg-primary text-primary-foreground hover:opacity-90'

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden
      />
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-card rounded-lg shadow-xl max-w-md w-full p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          aria-describedby="confirm-message"
        >
          <h2 id="confirm-title" className="text-lg font-semibold text-card-foreground mb-2">
            {title}
          </h2>
          <p id="confirm-message" className="text-muted-foreground mb-6">
            {message}
          </p>
          <div className="flex justify-end gap-3">
            <button
              ref={cancelButtonRef}
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-input rounded-lg hover:bg-accent text-card-foreground"
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              onClick={() => onConfirm()}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed ${confirmClass}`}
            >
              {loading ? '...' : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
