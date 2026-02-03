'use client'

import Link from 'next/link'
import { ReactNode } from 'react'
import type { WishlistItem } from '@/lib/types'

type WishlistItemCardProps = {
  item: WishlistItem
  onPhotoClick?: () => void
  onEditClick?: () => void
  editMode?: boolean
  highlightPurchased?: boolean
  actionButton?: ReactNode
}

export function WishlistItemCard({
  item,
  onPhotoClick,
  onEditClick,
  editMode = true,
  highlightPurchased = false,
  actionButton
}: WishlistItemCardProps) {
  const photoUrl = item.photo_url

  const cardContent = (
    <>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 flex-1">
          {item.name}
        </h3>
        {photoUrl && onPhotoClick && (
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onPhotoClick()
            }}
            className="ml-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 relative z-10"
            title="View photo"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
        )}
      </div>

      {item.description && (
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
          {item.description}
        </p>
      )}

      {item.price && (
        <p className="text-lg font-bold text-blue-600 dark:text-blue-400 mb-3">
          ${Number(item.price).toFixed(2)}
        </p>
      )}

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-3 inline-flex items-center relative z-10"
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
              className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
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
            ? 'border-2 border-green-500 dark:border-green-600 bg-green-50 dark:bg-green-900/20'
            : 'border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
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
        ? 'border-2 border-green-500 dark:border-green-600 bg-green-50 dark:bg-green-900/20'
        : 'border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
    }`}>
      {cardContent}
    </div>
  )
}
