'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { DashboardNav } from '@/components/DashboardNav'
import { ItemDetailModal } from '@/components/ItemDetailModal'
import { EditItemModal } from '@/components/EditItemModal'
import { HelpDialog } from '@/components/HelpDialog'
import { WishlistItemCard } from '@/components/WishlistItemCard'
import Link from 'next/link'
import { api } from '@/lib/api'
import type { Group, WishlistItem } from '@/lib/types'

export default function DashboardPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const [groups, setGroups] = useState<Group[]>([])
  const [wishlistItems, setWishlistItems] = useState<WishlistItem[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [selectedItem, setSelectedItem] = useState<WishlistItem | null>(null)
  const [editingItem, setEditingItem] = useState<WishlistItem | null>(null)
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData()

      // Check if this is the user's first visit
      const hasSeenHelp = localStorage.getItem('presently_help_seen')
      if (!hasSeenHelp) {
        setShowHelp(true)
        localStorage.setItem('presently_help_seen', 'true')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  async function loadDashboardData() {
    try {
      setLoadingData(true)
      const [groupsData, wishlistData] = await Promise.all([
        api.getGroups(),
        api.getWishlist(),
      ])
      setGroups(groupsData.groups)
      setWishlistItems(wishlistData.items)
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading dashboard data:', error)
    } finally {
      setLoadingData(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || !profile) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          {/* Header with greeting and actions */}
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">
              Dashboard
            </h1>
            <div className="flex gap-3">
              <Link
                href="/dashboard/wishlists/new"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                + Add Item
              </Link>
              <Link
                href="/dashboard/groups/new"
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg font-medium hover:opacity-90 transition-colors"
              >
                + Create Group
              </Link>
            </div>
          </div>

          {/* Groups Section */}
          <div>
            <h2 className="text-2xl font-bold mb-4">Groups</h2>

            {loadingData ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-card rounded-lg shadow p-6 animate-pulse">
                    <div className="h-6 bg-muted rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : groups.length === 0 ? (
              <div className="bg-card rounded-lg shadow p-12 text-center border border-border">
                <div className="text-6xl mb-4">👥</div>
                <h3 className="text-xl font-semibold mb-2">No groups yet</h3>
                <p className="text-muted-foreground mb-6">
                  Create your first group to start sharing wishlists with friends and family!
                </p>
                <Link
                  href="/dashboard/groups/new"
                  className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
                >
                  Create Your First Group
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groups.map((group) => (
                  <Link
                    key={group.id}
                    href={`/dashboard/groups/${group.id}`}
                    className="bg-card rounded-lg shadow p-6 hover:shadow-lg transition-shadow border border-border"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-lg">{group.name}</h3>
                      {group.role === 'admin' && (
                        <span className="px-2 py-1 text-xs bg-primary/10 text-primary rounded-full">
                          Admin
                        </span>
                      )}
                    </div>
                    {group.description && (
                      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                        {group.description}
                      </p>
                    )}
                    <p className="text-sm text-muted-foreground">
                      {group.member_count} {group.member_count === 1 ? 'member' : 'members'}
                    </p>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Wishlist Items */}
          <div>
            <h2 className="text-2xl font-bold mb-4">Wishlist</h2>

            {loadingData ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-card rounded-lg shadow p-6 animate-pulse">
                    <div className="h-40 bg-muted rounded mb-4"></div>
                    <div className="h-6 bg-muted rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : wishlistItems.length === 0 ? (
              <div className="bg-card rounded-lg shadow p-12 text-center">
                <div className="text-6xl mb-4">🎁</div>
                <h3 className="text-xl font-semibold mb-2">No wishlist items yet</h3>
                <p className="text-muted-foreground mb-6">
                  Start adding items to your wishlist so others know what you'd like!
                </p>
                <Link
                  href="/dashboard/wishlists/new"
                  className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
                >
                  Add Your First Item
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {wishlistItems.map((item) => (
                  <WishlistItemCard
                    key={item.id}
                    item={item}
                    onPhotoClick={() => setSelectedItem(item)}
                    onEditClick={() => setEditingItem(item)}
                    editMode={true}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Item Detail Modal */}
      {selectedItem && (
        <ItemDetailModal
          item={selectedItem}
          isOpen={!!selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}

      {/* Edit Item Modal */}
      {editingItem && (
        <EditItemModal
          item={editingItem}
          isOpen={!!editingItem}
          onClose={() => setEditingItem(null)}
          onSaved={loadDashboardData}
        />
      )}

      {/* Help Dialog */}
      <HelpDialog isOpen={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  )
}
