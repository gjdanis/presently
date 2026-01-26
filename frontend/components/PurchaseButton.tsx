'use client'

import { useState } from 'react'
import { api } from '@/lib/api'

type PurchaseButtonProps = {
  itemId: string
  groupId: string
  isPurchased: boolean
  purchasedByMe: boolean
  purchasedByName?: string
  onClaimChange?: (claimed: boolean) => void
}

export function PurchaseButton({
  itemId,
  groupId,
  isPurchased,
  purchasedByMe,
  purchasedByName,
  onClaimChange,
}: PurchaseButtonProps) {
  const [claimed, setClaimed] = useState(purchasedByMe)
  const [isProcessing, setIsProcessing] = useState(false)

  async function handleTogglePurchase() {
    if (isProcessing) return

    const newClaimedState = !claimed
    const previousClaimedState = claimed

    // Optimistic UI update: immediately update the state
    setClaimed(newClaimedState)
    setIsProcessing(true)

    try {
      if (!newClaimedState) {
        // Unclaim the item
        await api.unclaimItem(itemId, groupId)
      } else {
        // Claim the item
        await api.claimItem({ item_id: itemId, group_id: groupId })
      }

      // Success - notify parent
      onClaimChange?.(newClaimedState)
      setIsProcessing(false)
    } catch (error) {
      console.error('Error toggling claim:', error)
      // Revert on failure
      setClaimed(previousClaimedState)
      alert(newClaimedState ? 'Failed to claim item' : 'Failed to unclaim item')
      setIsProcessing(false)
    }
  }

  if (isPurchased && !purchasedByMe) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400 font-medium">
        ✓ Claimed by {purchasedByName || 'someone else'}
      </div>
    )
  }

  return (
    <button
      onClick={handleTogglePurchase}
      disabled={isProcessing}
      className={`w-full px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 disabled:cursor-not-allowed ${
        claimed
          ? 'bg-green-600 hover:bg-green-700 text-white'
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      }`}
    >
      <span className="flex items-center justify-center gap-2">
        {isProcessing && (
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        <span>{claimed ? "✓ I'm getting this" : 'Claim Item'}</span>
      </span>
    </button>
  )
}
