'use client'

import { useAuth } from '@/lib/contexts/AuthContext'

export function AuthLoadingGate({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-12 w-12 border-2 border-primary border-t-transparent mx-auto mb-4"
            aria-hidden
          />
          <p className="text-muted-foreground text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
