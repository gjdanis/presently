'use client'

import { useState, useEffect } from 'react'
import { DeleteItemButton } from '@/components/DeleteItemButton'
import { api } from '@/lib/api'
import type { WishlistItem } from '@/lib/types'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function SortableItem({
  item,
  onDelete,
  onEdit
}: {
  item: WishlistItem
  onDelete: (itemId: string) => void
  onEdit: (item: WishlistItem) => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow group"
    >
      <div className="flex items-start gap-3 p-3 sm:p-4">
        <button
          className="mt-1 cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 touch-none flex-shrink-0"
          {...attributes}
          {...listeners}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 8h16M4 16h16"
            />
          </svg>
        </button>

        <div
          onClick={() => onEdit(item)}
          className="flex-1 min-w-0 cursor-pointer"
        >
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1 break-words group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {item.name}
          </h3>

          {item.description && (
            <p className="text-gray-600 dark:text-gray-400 text-sm mb-2 break-words line-clamp-2">
              {item.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm mb-2">
            {item.price && (
              <span className="text-gray-900 dark:text-gray-100 font-medium">
                ${Number(item.price).toFixed(2)}
              </span>
            )}

            {item.url && (
              <span className="text-blue-600 dark:text-blue-400 text-xs">
                View →
              </span>
            )}
          </div>

          {item.groups && item.groups.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {item.groups.map((group) => (
                <span
                  key={group.id}
                  className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full"
                >
                  {group.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex-shrink-0">
          <DeleteItemButton
            itemId={item.id}
            onDelete={() => onDelete(item.id)}
          />
        </div>
      </div>
    </div>
  )
}

export function DraggableWishlist({
  initialItems,
  onReorder,
  onEditItem
}: {
  initialItems: WishlistItem[]
  onReorder?: () => void
  onEditItem?: (item: WishlistItem) => void
}) {
  const [items, setItems] = useState(initialItems)
  const [reorderMessage, setReorderMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    setItems(initialItems)
  }, [initialItems])

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  function handleDelete(itemId: string) {
    // Immediately update local state to remove the item
    setItems((prevItems) => prevItems.filter((item) => item.id !== itemId))
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event

    if (!over || active.id === over.id) {
      return
    }

    const oldIndex = items.findIndex((item) => item.id === active.id)
    const newIndex = items.findIndex((item) => item.id === over.id)

    const newItems = arrayMove(items, oldIndex, newIndex)
    setItems(newItems)

    // Update ranks in the database
    try {
      const updates = newItems.map((item, index) => ({
        id: item.id,
        rank: index + 1,
      }))

      await api.reorderItems(updates)

      // Show success message
      setReorderMessage({ type: 'success', text: 'Order saved' })
      setTimeout(() => setReorderMessage(null), 3000)

      if (onReorder) {
        onReorder()
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error reordering items:', error)
      // Revert on error
      setItems(initialItems)
      setReorderMessage({ type: 'error', text: 'Failed to save order' })
      setTimeout(() => setReorderMessage(null), 5000)
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        {reorderMessage && (
          <p
            className={`text-sm mb-4 px-4 py-2 rounded-lg ${
              reorderMessage.type === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
            }`}
          >
            {reorderMessage.text}
          </p>
        )}
        <div className="space-y-4">
          {items.map((item) => (
            <SortableItem
              key={item.id}
              item={item}
              onDelete={handleDelete}
              onEdit={(item) => onEditItem?.(item)}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
