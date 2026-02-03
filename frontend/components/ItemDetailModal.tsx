'use client'

import { useState, useEffect } from 'react'

type ItemDetailModalProps = {
  item: {
    name: string
    description?: string
    price?: number
    url?: string
    photoUrl?: string
    photo_url?: string
  }
  isOpen: boolean
  onClose: () => void
}

export function ItemDetailModal({ item, isOpen, onClose }: ItemDetailModalProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  // Reset loading state when modal opens or item changes
  useEffect(() => {
    if (isOpen) {
      setImageLoaded(false)
      setImageError(false)
    }
  }, [isOpen, item])

  if (!isOpen) return null

  const photoUrl = item.photoUrl || item.photo_url

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-between items-center rounded-t-lg">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {item.name}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {photoUrl && (
              <div className="mb-4 relative">
                {!imageLoaded && !imageError && (
                  <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse flex items-center justify-center">
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                {!imageError && (
                  <img
                    src={photoUrl}
                    alt={item.name}
                    className={`w-full max-h-96 object-contain rounded-lg transition-opacity duration-200 ${
                      imageLoaded ? 'opacity-100' : 'opacity-0 absolute inset-0'
                    }`}
                    onLoad={() => setImageLoaded(true)}
                    onError={() => setImageError(true)}
                  />
                )}
                {imageError && (
                  <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                    <p className="text-gray-500 dark:text-gray-400">Failed to load image</p>
                  </div>
                )}
              </div>
            )}

            {item.description && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Description</h3>
                <p className="text-gray-600 dark:text-gray-400">{item.description}</p>
              </div>
            )}

            {item.price && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Price</h3>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  ${Number(item.price).toFixed(2)}
                </p>
              </div>
            )}

            {item.url && (
              <div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                >
                  View Product
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
