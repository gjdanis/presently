'use client'

import { useAuth } from '@/lib/contexts/AuthContext'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DashboardNav } from '@/components/DashboardNav'
import { PurchaseButton } from '@/components/PurchaseButton'
import { InviteMemberModal } from '@/components/InviteMemberModal'
import { ItemDetailModal } from '@/components/ItemDetailModal'
import { EditItemModal } from '@/components/EditItemModal'
import { WishlistItemCard } from '@/components/WishlistItemCard'
import { api } from '@/lib/api'
import type { GroupDetail, WishlistItem } from '@/lib/types'

export default function GroupDetailPage() {
  const { isAuthenticated, isLoading, profile } = useAuth()
  const router = useRouter()
  const params = useParams()
  const groupId = params.id as string
  const [groupData, setGroupData] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [hidePurchased, setHidePurchased] = useState(false)
  const [selectedItem, setSelectedItem] = useState<WishlistItem | null>(null)
  const [editingItem, setEditingItem] = useState<WishlistItem | null>(null)
  const [undoItem, setUndoItem] = useState<WishlistItem | null>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (isAuthenticated && groupId) {
      loadGroup()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, groupId])

  async function handleMarkReceived(item: any) {
    // Optimistically remove from group wishlist view
    setGroupData((prevData) => {
      if (!prevData) return prevData
      return {
        ...prevData,
        wishlists: prevData.wishlists.map((wishlist) => ({
          ...wishlist,
          items: wishlist.items.filter((i: any) => i.id !== item.id),
        })),
      }
    })
    setUndoItem(item)
    try {
      await api.markReceived(item.id)
    } catch (error) {
      // Revert on failure
      setGroupData((prevData) => {
        if (!prevData) return prevData
        return {
          ...prevData,
          wishlists: prevData.wishlists.map((wishlist) =>
            wishlist.user_id === item.user_id
              ? { ...wishlist, items: [...wishlist.items, item] }
              : wishlist
          ),
        }
      })
      setUndoItem(null)
      if (process.env.NODE_ENV === 'development') console.error('Error marking item received:', error)
    }
  }

  async function handleUndo() {
    if (!undoItem) return
    const item = undoItem
    setUndoItem(null)
    try {
      await api.markReceived(item.id)
      setGroupData((prevData) => {
        if (!prevData) return prevData
        return {
          ...prevData,
          wishlists: prevData.wishlists.map((wishlist) =>
            wishlist.user_id === item.user_id
              ? { ...wishlist, items: [...wishlist.items, item] }
              : wishlist
          ),
        }
      })
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error undoing received:', error)
    }
  }

  const loadGroup = async () => {
    try {
      const data = await api.getGroup(groupId)
      setGroupData(data)

      // Auto-select first member if there are members
      if (data.members && data.members.length > 0 && !selectedMemberId) {
        const firstMemberId = data.members[0].user_id
        setSelectedMemberId(firstMemberId)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error loading group:', error)
      router.push('/dashboard/groups')
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardNav userName={profile?.name || 'User'} />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="h-8 w-48 bg-muted rounded animate-pulse mb-6" />
            <div className="flex gap-4 mb-6">
              <div className="h-10 w-24 bg-muted rounded animate-pulse" />
              <div className="h-10 w-24 bg-muted rounded animate-pulse" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-card rounded-lg shadow p-6 animate-pulse space-y-3">
                <div className="h-5 bg-muted rounded w-1/3" />
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 bg-muted rounded" />
                ))}
              </div>
              <div className="bg-card rounded-lg shadow p-6 animate-pulse space-y-4">
                <div className="h-6 bg-muted rounded w-1/2 mb-4" />
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-muted rounded" />
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!isAuthenticated || !profile || !groupData) {
    return null
  }

  // Find current user's membership
  const currentUserMember = groupData.members.find(m => m.user_id === profile.id)
  const isAdmin = currentUserMember?.role === 'admin'

  // Get selected wishlist or null
  const selectedWishlist = selectedMemberId
    ? groupData.wishlists.find((w: any) => w.user_id === selectedMemberId)
    : null

  return (
    <div className="min-h-screen bg-background">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <Link
              href="/dashboard/groups"
              className="text-primary hover:underline mb-2 inline-block"
            >
              ← Back to Groups
            </Link>
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold">{groupData.group.name}</h1>
                {groupData.group.description && (
                  <p className="text-muted-foreground mt-2">
                    {groupData.group.description}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Link
                  href={`/dashboard/wishlists/new?group=${groupId}`}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 font-medium"
                >
                  + Item
                </Link>
                {isAdmin && (
                  <>
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:opacity-90 font-medium"
                    >
                      + Member
                    </button>
                    <Link
                      href={`/dashboard/groups/${groupId}/manage`}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
                    >
                      Manage Group
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Members Section */}
          <div className="bg-card rounded-lg shadow p-6 mb-6 border border-border">
            <h2 className="text-xl font-semibold mb-4 text-foreground">
              Members
            </h2>
            <div className="flex flex-wrap gap-2">
              {groupData.members.map((member: any) => {
                const memberId = member.user_id
                const isCurrentUser = memberId === profile.id
                const isSelected = memberId === selectedMemberId
                return (
                  <button
                    key={memberId}
                    onClick={() => setSelectedMemberId(isSelected ? null : memberId)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isSelected
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-muted text-foreground hover:bg-accent'
                    }`}
                  >
                    {member.name}
                    {member.role === 'admin' && (
                      <span className="ml-1 text-xs opacity-75">
                        (Admin)
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Wishlists Section */}
          {!selectedMemberId ? (
            <div className="bg-card rounded-lg shadow p-8 text-center border border-border">
              <p className="text-muted-foreground">
                Select a member above to view their wishlist
              </p>
            </div>
          ) : !selectedWishlist ? (
            <div className="bg-card rounded-lg shadow p-8 text-center border border-border">
              <p className="text-muted-foreground">
                No wishlist items have been shared with this group yet.
              </p>
            </div>
          ) : (
            <div className="bg-card rounded-lg shadow border border-border">
              <div className="p-6">
                {undoItem && (
                  <div className="flex items-center justify-between mb-4 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm">
                    <div className="flex items-center gap-3">
                      <span>"{undoItem.name}" marked as received</span>
                      <button onClick={handleUndo} className="font-medium underline hover:opacity-80">
                        Undo
                      </button>
                    </div>
                    <button onClick={() => setUndoItem(null)} className="hover:opacity-60 ml-4" aria-label="Dismiss">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                )}
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-foreground">
                    {selectedWishlist.user_name}'s Wishlist
                  </h3>
                  {/* Only show toggle if viewing someone else's wishlist */}
                  {selectedMemberId !== profile.id && (
                    <label className="flex items-center gap-3 text-sm text-muted-foreground cursor-pointer">
                      <span>Hide purchased items</span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={hidePurchased}
                        onClick={() => setHidePurchased(!hidePurchased)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                          hidePurchased ? 'bg-primary' : 'bg-muted'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            hidePurchased ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </label>
                  )}
                </div>
                {selectedWishlist.items.length === 0 ? (
                  <p className="text-muted-foreground text-sm">No items yet</p>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {selectedWishlist.items
                      .filter((item: any) => {
                        // Only filter if viewing someone else's wishlist and toggle is on
                        if (selectedMemberId === profile.id || !hidePurchased) {
                          return true
                        }
                        const isPurchased = item.is_purchased || false
                        return !isPurchased
                      })
                      .map((item: any) => {
                      const itemOwnerId = item.user_id
                      const isOwnItem = itemOwnerId === profile.id

                      // Purchase status (only visible to non-owners)
                      const isPurchased = item.is_purchased || false
                      const purchasedById = item.purchased_by
                      const purchasedByMe = !isOwnItem && purchasedById === profile.id

                      // Find purchaser's name if item is purchased
                      let purchasedByName: string | undefined
                      if (isPurchased && !isOwnItem && purchasedById) {
                        const purchaser = groupData.members.find((m: any) =>
                          m.user_id === purchasedById
                        )
                        purchasedByName = purchaser?.name
                      }

                      return (
                        <WishlistItemCard
                          key={item.id}
                          item={item}
                          onPhotoClick={() => setSelectedItem(item)}
                          onEditClick={isOwnItem ? () => setEditingItem(item as WishlistItem) : undefined}
                          onMarkReceived={isOwnItem ? () => handleMarkReceived(item) : undefined}
                          editMode={isOwnItem}
                          highlightPurchased={purchasedByMe}
                          actionButton={
                            !isOwnItem ? (
                              <PurchaseButton
                                itemId={item.id}
                                groupId={groupId}
                                isPurchased={isPurchased}
                                purchasedByMe={purchasedByMe}
                                purchasedByName={purchasedByName}
                                onClaimChange={(claimed) => {
                                  // Optimistically update local state instead of reloading
                                  setGroupData(prevData => {
                                    if (!prevData) return prevData

                                    return {
                                      ...prevData,
                                      wishlists: prevData.wishlists.map(wishlist => ({
                                        ...wishlist,
                                        items: wishlist.items.map(wishlistItem =>
                                          wishlistItem.id === item.id
                                            ? {
                                                ...wishlistItem,
                                                is_purchased: claimed,
                                                purchased_by: claimed ? profile.id : undefined,
                                              }
                                            : wishlistItem
                                        ),
                                      })),
                                    }
                                  })
                                }}
                              />
                            ) : undefined
                          }
                        />
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Invite Member Modal */}
      <InviteMemberModal
        groupId={groupId}
        groupName={groupData.group.name}
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
      />

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
          onSaved={loadGroup}
        />
      )}
    </div>
  )
}
