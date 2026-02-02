-- ============================================================================
-- Migration: Add Multi-Use Invitation Support
-- ============================================================================
-- This migration adds support for shareable multi-use invitation links
-- that can be used by multiple people without requiring email

-- Add columns to group_invitations table
ALTER TABLE group_invitations
  ADD COLUMN IF NOT EXISTS max_uses INTEGER,                    -- NULL = unlimited uses
  ADD COLUMN IF NOT EXISTS current_uses INTEGER DEFAULT 0,      -- Track how many times used
  ADD COLUMN IF NOT EXISTS is_multi_use BOOLEAN DEFAULT FALSE;  -- Flag for multi-use invites

-- Make email optional (for multi-use links that don't target specific person)
ALTER TABLE group_invitations
  ALTER COLUMN email DROP NOT NULL;

-- Drop the unique constraint on (group_id, email) since multi-use links won't have email
ALTER TABLE group_invitations
  DROP CONSTRAINT IF EXISTS group_invitations_group_id_email_key;

-- Add new unique constraint only when email is provided
CREATE UNIQUE INDEX IF NOT EXISTS idx_group_invitations_group_email
  ON group_invitations(group_id, email)
  WHERE email IS NOT NULL;

-- Make expires_at optional (NULL = never expires)
ALTER TABLE group_invitations
  ALTER COLUMN expires_at DROP NOT NULL,
  ALTER COLUMN expires_at DROP DEFAULT;

-- Create table to track who accepted each invitation
CREATE TABLE IF NOT EXISTS invitation_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invitation_id UUID NOT NULL REFERENCES group_invitations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(invitation_id, user_id)  -- Each user can only accept an invitation once
);

CREATE INDEX IF NOT EXISTS idx_invitation_acceptances_invitation
  ON invitation_acceptances(invitation_id);

CREATE INDEX IF NOT EXISTS idx_invitation_acceptances_user
  ON invitation_acceptances(user_id);

-- Add comment for documentation
COMMENT ON TABLE invitation_acceptances IS 'Tracks which users accepted which multi-use invitations';
COMMENT ON COLUMN group_invitations.max_uses IS 'Maximum number of times this invitation can be used (NULL = unlimited)';
COMMENT ON COLUMN group_invitations.current_uses IS 'Number of times this invitation has been used';
COMMENT ON COLUMN group_invitations.is_multi_use IS 'Whether this is a multi-use shareable link';
