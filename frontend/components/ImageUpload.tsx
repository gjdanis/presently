'use client'

import { useState, useRef, useEffect } from 'react'
import { api } from '@/lib/api'

type ImageUploadProps = {
  currentImageUrl?: string | null
  onImageChange: (_data: string | null) => void
}

export function ImageUpload({ currentImageUrl, onImageChange }: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(currentImageUrl || null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Update preview when currentImageUrl prop changes
  useEffect(() => {
    setPreview(currentImageUrl || null)
  }, [currentImageUrl])

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image file is too large. Please select an image under 10MB.')
      return
    }

    setError(null)
    setUploading(true)

    try {
      // Resize and compress the image
      const resizedBlob = await resizeImageToBlob(file, 800, 800, 0.85)

      // Try to upload to S3
      try {
        const { upload_url, fields, file_url, preview_url } = await api.getPhotoUploadUrl()

        // Convert blob to file for upload
        const resizedFile = new File([resizedBlob], file.name, { type: 'image/jpeg' })

        // Upload to S3
        await api.uploadPhotoToS3(upload_url, fields, resizedFile)

        // Use preview URL for display, but save S3 URI
        setPreview(preview_url)
        onImageChange(file_url)
      } catch (s3Error) {
        console.warn('S3 upload failed, falling back to base64:', s3Error)

        // Fallback to base64 (for local dev or if S3 not configured)
        const resizedDataUrl = await blobToDataUrl(resizedBlob)
        setPreview(resizedDataUrl)
        onImageChange(resizedDataUrl)
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error processing image:', error)
      setError('Failed to process image')
    } finally {
      setUploading(false)
    }
  }

  function handleRemove() {
    setPreview(null)
    setError(null)
    onImageChange(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-900 dark:text-gray-100">
        Photo (optional)
      </label>
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
      {preview ? (
        <div className="relative inline-block">
          <img
            src={preview}
            alt="Preview"
            className="w-32 h-32 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
          />
          <button
            type="button"
            onClick={handleRemove}
            className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-700"
          >
            ×
          </button>
        </div>
      ) : (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            disabled={uploading}
            className="block w-full text-sm text-gray-500 dark:text-gray-400
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-medium
              file:bg-blue-50 file:text-blue-700
              dark:file:bg-blue-900 dark:file:text-blue-200
              hover:file:bg-blue-100 dark:hover:file:bg-blue-800
              file:cursor-pointer
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          {uploading && (
            <p className="text-sm text-gray-500 mt-1">Processing image...</p>
          )}
        </div>
      )}
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Images will be resized to a maximum of 800x800 pixels
      </p>
    </div>
  )
}

// Helper function to resize image and return Blob
function resizeImageToBlob(
  file: File,
  maxWidth: number,
  maxHeight: number,
  quality: number
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        // Calculate new dimensions
        let width = img.width
        let height = img.height

        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width = width * ratio
          height = height * ratio
        }

        // Create canvas and resize
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Failed to get canvas context'))
          return
        }

        ctx.drawImage(img, 0, 0, width, height)

        // Convert to Blob with compression
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to create blob'))
            }
          },
          'image/jpeg',
          quality
        )
      }

      img.onerror = () => reject(new Error('Failed to load image'))
      img.src = e.target?.result as string
    }

    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

// Helper to convert Blob to data URL (for base64 fallback)
function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to convert blob to data URL'))
    reader.readAsDataURL(blob)
  })
}
