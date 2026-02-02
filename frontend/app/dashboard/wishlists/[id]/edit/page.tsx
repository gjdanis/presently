'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { DashboardNav } from '@/components/DashboardNav'
import { EditItemForm } from '@/components/EditItemForm'
import { api } from '@/lib/api'
import type { WishlistItem } from '@/lib/types'

export default function EditItemPage() {
  const params = useParams()
  const router = useRouter()
  const { isAuthenticated, isLoading, profile } = useAuth()
  const [item, setItem] = useState<WishlistItem | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated && params.id) {
      loadItem()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, params.id])

  async function loadItem() {
    try {
      const data = await api.getItem(params.id as string)

      // Verify item belongs to current user
      if (data.user_id !== profile?.id) {
        router.push('/dashboard/wishlists')
        return
      }

      setItem(data)
    } catch (error) {
      console.error('Error loading item:', error)
      router.push('/dashboard/wishlists')
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

  if (!isAuthenticated || !item) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile?.name || 'User'} />

      <main className="max-w-2xl mx-auto py-6 sm:py-12 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-gray-100">Edit Item</h1>
        <EditItemForm item={item} />
      </main>
    </div>
  )
}
