-- ============================================================================
-- Migration: Add received_at to wishlist_items
-- ============================================================================
-- Allows item owners to mark items as received after a gift event.
-- Items with received_at set are treated as archived and excluded from
-- active wishlist views by default.

ALTER TABLE wishlist_items
  ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ;

COMMENT ON COLUMN wishlist_items.received_at IS 'Set by the item owner when they have received this item as a gift. NULL means the item is still active.';
