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
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [editingItem, setEditingItem] = useState<WishlistItem | null>(null)

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
      console.error('Error loading group:', error)
      router.push('/dashboard/groups')
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <DashboardNav userName={profile.name || 'User'} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <Link
              href="/dashboard/groups"
              className="text-blue-600 dark:text-blue-400 hover:underline mb-2 inline-block"
            >
              ← Back to Groups
            </Link>
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold">{groupData.group.name}</h1>
                {groupData.group.description && (
                  <p className="text-gray-600 dark:text-gray-300 mt-2">
                    {groupData.group.description}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Link
                  href={`/dashboard/wishlists/new?group=${groupId}`}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                >
                  + Item
                </Link>
                {isAdmin && (
                  <>
                    <button
                      onClick={() => setShowInviteModal(true)}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
                    >
                      + Member
                    </button>
                    <Link
                      href={`/dashboard/groups/${groupId}/manage`}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                    >
                      Manage Group
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Members Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
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
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-600'
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
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <p className="text-gray-600 dark:text-gray-300">
                Select a member above to view their wishlist
              </p>
            </div>
          ) : !selectedWishlist ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <p className="text-gray-600 dark:text-gray-300">
                No wishlist items have been shared with this group yet.
              </p>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {selectedWishlist.user_name}'s Wishlist
                  </h3>
                  {/* Only show toggle if viewing someone else's wishlist */}
                  {selectedMemberId !== profile.id && (
                    <label className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300 cursor-pointer">
                      <span>Hide purchased items</span>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={hidePurchased}
                        onClick={() => setHidePurchased(!hidePurchased)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                          hidePurchased ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
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
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No items yet</p>
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
                                  // Optionally refresh the group data
                                  // For now, the PurchaseButton handles its own state
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
