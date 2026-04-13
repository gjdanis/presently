'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

type FeedbackDialogProps = {
  isOpen: boolean
  onClose: () => void
}

type State = 'idle' | 'submitting' | 'success' | 'error'

export function FeedbackDialog({ isOpen, onClose }: FeedbackDialogProps) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [state, setState] = useState<State>('idle')
  const [issueUrl, setIssueUrl] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const bodyRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (isOpen) {
      setState('idle')
      setTitle('')
      setBody('')
      setIssueUrl(null)
      setErrorMsg(null)
      setTimeout(() => bodyRef.current?.focus(), 50)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!body.trim()) return
    setState('submitting')
    setErrorMsg(null)
    try {
      const result = await api.submitFeedback(title || undefined, body.trim())
      setIssueUrl(result.issue_url)
      setState('success')
    } catch (err: any) {
      setErrorMsg(err?.message || 'Something went wrong. Please try again.')
      setState('error')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose} />
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-card rounded-lg shadow-xl max-w-lg w-full border border-border">
          {/* Header */}
          <div className="bg-card border-b border-border px-6 py-4 flex justify-between items-center rounded-t-lg">
            <h2 className="text-xl font-semibold text-foreground">Give Feedback</h2>
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
            {state === 'success' ? (
              <div className="text-center py-4">
                <div className="text-4xl mb-3">🎉</div>
                <p className="text-foreground font-medium mb-2">Thanks for the feedback!</p>
                {issueUrl && (
                  <a
                    href={issueUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary text-sm hover:underline"
                  >
                    View issue →
                  </a>
                )}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Subject <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. It would be great if..."
                    className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Feedback <span className="text-destructive">*</span>
                  </label>
                  <textarea
                    ref={bodyRef}
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    required
                    rows={5}
                    placeholder="What's working well? What could be better? Any features you'd love to see?"
                    className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm resize-none"
                  />
                </div>
                {state === 'error' && errorMsg && (
                  <p className="text-destructive text-sm">{errorMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={state === 'submitting' || !body.trim()}
                  className="w-full px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {state === 'submitting' ? 'Sending...' : 'Send Feedback'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
