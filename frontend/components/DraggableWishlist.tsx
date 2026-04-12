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
  onEdit,
  onMarkReceived,
}: {
  item: WishlistItem
  onDelete: (itemId: string) => void
  onEdit: (item: WishlistItem) => void
  onMarkReceived: (itemId: string) => void
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
      className="bg-card rounded-lg shadow hover:shadow-md transition-shadow group border border-border"
    >
      <div className="flex items-start gap-3 p-3 sm:p-4">
        <button
          className="mt-1 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground touch-none flex-shrink-0"
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
          <h3 className="font-semibold mb-1 break-words group-hover:text-primary transition-colors">
            {item.name}
          </h3>

          {item.description && (
            <p className="text-muted-foreground text-sm mb-2 break-words line-clamp-2">
              {item.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm mb-2">
            {item.price && (
              <span className="font-medium">
                ${Number(item.price).toFixed(2)}
              </span>
            )}

            {item.url && (
              <span className="text-primary text-xs">
                View →
              </span>
            )}
          </div>

          {item.groups && item.groups.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {item.groups.map((group) => (
                <span
                  key={group.id}
                  className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full"
                >
                  {group.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex-shrink-0 flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onMarkReceived(item.id)
            }}
            className="p-1.5 text-muted-foreground hover:text-green-600 transition-colors rounded"
            title="Mark as received"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
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
  const [undoItem, setUndoItem] = useState<WishlistItem | null>(null)

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
    setItems((prevItems) => prevItems.filter((item) => item.id !== itemId))
  }

  async function handleMarkReceived(itemId: string) {
    const item = items.find((i) => i.id === itemId)
    if (!item) return

    // Optimistically remove from list
    setItems((prevItems) => prevItems.filter((i) => i.id !== itemId))
    setUndoItem(item)

    try {
      await api.markReceived(itemId)
    } catch (error) {
      // Revert on failure
      setItems((prevItems) => [...prevItems, item].sort((a, b) => a.rank - b.rank))
      setUndoItem(null)
      if (process.env.NODE_ENV === 'development') console.error('Error marking item received:', error)
    }
  }

  async function handleUndo() {
    if (!undoItem) return
    setUndoItem(null)
    try {
      await api.markReceived(undoItem.id) // toggles back
      setItems((prevItems) => [...prevItems, undoItem].sort((a, b) => a.rank - b.rank))
    } catch (error) {
      if (process.env.NODE_ENV === 'development') console.error('Error undoing received:', error)
    }
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
        {reorderMessage && (
          <p
            className={`text-sm mb-4 px-4 py-2 rounded-lg ${
              reorderMessage.type === 'success'
                ? 'bg-primary/10 text-primary'
                : 'bg-destructive/10 text-destructive'
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
              onMarkReceived={handleMarkReceived}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
