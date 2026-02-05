'use client'

import { useEffect, useRef } from 'react'

type HelpDialogProps = {
  isOpen: boolean
  onClose: () => void
}

export function HelpDialog({ isOpen, onClose }: HelpDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen) closeButtonRef.current?.focus()
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

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-card rounded-lg shadow-xl max-w-2xl w-full border border-border">
          {/* Header */}
          <div className="bg-card border-b border-border px-6 py-4 flex justify-between items-center rounded-t-lg">
            <h2 className="text-2xl font-semibold text-foreground">
              Getting Started with Presently
            </h2>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="text-muted-foreground hover:text-foreground"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <div>
              <h3 className="text-lg font-semibold mb-3 text-foreground">How to Use Presently</h3>
              <ul className="space-y-2.5 text-muted-foreground text-sm">
                <li className="flex items-start gap-2.5">
                  <span className="text-primary mt-0.5">•</span>
                  <span><strong className="text-foreground">Create a group</strong> (e.g., "Family" or "Friends") and invite members via email or link</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-primary mt-0.5">•</span>
                  <span><strong className="text-foreground">Add wishlist items</strong> with details like description, price, links, and photos</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-primary mt-0.5">•</span>
                  <span><strong className="text-foreground">Share with groups</strong> by selecting which groups can see each item</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-primary mt-0.5">•</span>
                  <span><strong className="text-foreground">View group wishlists</strong> by clicking a group and selecting a member</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-primary mt-0.5">•</span>
                  <span><strong className="text-foreground">Claim items</strong> to secretly mark them as purchased - owners won't see who claimed them</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-card border-t border-border px-6 py-4 rounded-b-lg">
            <button
              onClick={onClose}
              className="w-full px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
