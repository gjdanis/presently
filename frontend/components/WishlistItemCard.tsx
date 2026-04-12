'use client'

import Link from 'next/link'
import { ReactNode } from 'react'
import type { WishlistItem } from '@/lib/types'

type WishlistItemCardProps = {
  item: WishlistItem
  onPhotoClick?: () => void
  onEditClick?: () => void
  onMarkReceived?: () => void
  editMode?: boolean
  highlightPurchased?: boolean
  actionButton?: ReactNode
}

export function WishlistItemCard({
  item,
  onPhotoClick,
  onEditClick,
  onMarkReceived,
  editMode = true,
  highlightPurchased = false,
  actionButton
}: WishlistItemCardProps) {
  const photoUrl = item.photo_url

  const cardContent = (
    <>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-lg text-foreground flex-1">
          {item.name}
        </h3>
        <div className="flex items-center gap-1 ml-2 relative z-10">
          {photoUrl && onPhotoClick && (
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onPhotoClick()
              }}
              className="text-primary hover:opacity-80"
              title="View photo"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
          )}
          {onMarkReceived && (
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onMarkReceived()
              }}
              className="text-muted-foreground hover:text-green-600 transition-colors"
              title="Mark as received"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {item.description && (
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {item.description}
        </p>
      )}

      {item.price && (
        <p className="text-lg font-bold text-primary mb-3">
          ${Number(item.price).toFixed(2)}
        </p>
      )}

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-sm text-primary hover:underline mb-3 inline-flex items-center relative z-10"
        >
          View Product
          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}

      {actionButton && (
        <div className="mt-auto pt-3 relative z-10" onClick={(e) => e.stopPropagation()}>
          {actionButton}
        </div>
      )}

      {item.groups && item.groups.length > 0 && (
        <div className={`flex flex-wrap gap-1 ${actionButton ? 'mt-3' : 'mt-auto'} relative z-10`} onClick={(e) => e.stopPropagation()}>
          {item.groups.map((group) => (
            <Link
              key={group.id}
              href={`/dashboard/groups/${group.id}`}
              className="px-2 py-1 text-xs bg-primary/10 text-primary rounded-full hover:bg-primary/20 transition-colors"
            >
              {group.name}
            </Link>
          ))}
        </div>
      )}
    </>
  )

  // In edit mode, make the whole card clickable to edit
  if (editMode && onEditClick) {
    return (
      <div
        onClick={onEditClick}
        className={`rounded-lg shadow hover:shadow-lg transition-all p-4 flex flex-col h-full cursor-pointer ${
          highlightPurchased
            ? 'border-2 border-primary bg-primary/10'
            : 'border border-border bg-card'
        }`}
      >
        {cardContent}
      </div>
    )
  }

  // In view mode, card is not clickable
  return (
    <div className={`rounded-lg shadow hover:shadow-lg transition-all p-4 flex flex-col h-full ${
      highlightPurchased
        ? 'border-2 border-primary bg-primary/10'
        : 'border border-border bg-card'
    }`}>
      {cardContent}
    </div>
  )
}
