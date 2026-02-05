'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/contexts/AuthContext';
import type { Invitation } from '@/lib/types';

interface InvitePageProps {
  params: { token: string };
}

export default function InvitePage({ params }: InvitePageProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { token } = params;
  const [loading, setLoading] = useState(true);
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [alreadyMember, setAlreadyMember] = useState(false);

  // Load invitation when component mounts
  useEffect(() => {
    if (authLoading) return;

    async function loadInvitation(inviteToken: string) {
      try {
        // Fetch invitation details from backend
        const invitationData = await api.getInvitation(inviteToken);
        setInvitation(invitationData);
        setLoading(false);
      } catch (err: any) {
        if (process.env.NODE_ENV === 'development') console.error('Error loading invitation:', err);
        setError(err.message || 'Failed to load invitation. The invitation may be invalid or expired.');
        setLoading(false);
      }
    }

    loadInvitation(token);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, authLoading]);

  // Auto-accept invitation when user is authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated && invitation && !accepting && !accepted) {
      acceptInvitation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authLoading, invitation, accepting, accepted]);

  async function acceptInvitation() {
    if (!token) return;

    setAccepting(true);
    try {
      const result = await api.acceptInvitation(token);

      if (result.already_member) {
        setAlreadyMember(true);
      }

      setAccepted(true);

      // Redirect to group page after 2 seconds
      setTimeout(() => {
        router.push(`/dashboard/groups/${result.group_id}`);
      }, 2000);
    } catch (err: any) {
      if (process.env.NODE_ENV === 'development') console.error('Error accepting invitation:', err);
      setError(err.message || 'Failed to accept invitation');
      setAccepting(false);
    }
  }

  // Loading state
  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading invitation...</p>
        </div>
      </div>
    );
  }

  // Error state (invalid or expired invitation)
  if (error && !invitation) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-card rounded-lg shadow p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-destructive mb-4">
            Invalid or Expired Invitation
          </h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Link
            href="/auth/login"
            className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  // Accepting/accepted state (show while processing or after success)
  if (accepting || accepted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-card rounded-lg shadow p-8 text-center">
          <div className="text-6xl mb-4">{error ? '❌' : '🎉'}</div>
          <h1 className="text-2xl font-bold text-primary mb-4">
            {error
              ? 'Failed to Join Group'
              : alreadyMember
              ? 'Already a Member!'
              : accepting
              ? 'Joining Group...'
              : 'Welcome to the Group!'}
          </h1>
          <p className="text-muted-foreground mb-6">
            {error
              ? 'There was an error adding you to the group. Please try again.'
              : alreadyMember
              ? `You're already a member of ${invitation?.group_name}.`
              : accepting
              ? 'Please wait while we add you to the group...'
              : `You've successfully joined ${invitation?.group_name}!`}
          </p>
          {error && (
            <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-destructive text-sm">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setAccepting(false);
                  setAccepted(false);
                }}
                className="mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
              >
                Try Again
              </button>
            </div>
          )}
          {!error && !accepting && (
            <Link
              href={`/dashboard/groups/${invitation?.group_id}`}
              className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90"
            >
              Go to Group
            </Link>
          )}
        </div>
      </div>
    );
  }

  // Not logged in OR logged in but not auto-accepted yet - show invitation details
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-card rounded-lg shadow p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">🎁</div>
          <h1 className="text-3xl font-bold mb-2 text-foreground">Presently</h1>
          <p className="text-sm text-muted-foreground">Wishlist sharing made simple</p>
        </div>

        {/* Error Message (if any) */}
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-destructive text-sm">{error}</p>
          </div>
        )}

        {/* Invitation Details */}
        <div className="bg-primary/10 border border-primary/20 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-3 text-foreground">You've Been Invited!</h2>
          <p className="text-muted-foreground mb-4">
            <strong>{invitation?.invited_by.name || invitation?.invited_by.email}</strong> has
            invited you to join the group{' '}
            <strong>"{invitation?.group_name}"</strong> on Presently.
          </p>
          {invitation?.group_description && (
            <p className="text-sm text-muted-foreground">{invitation.group_description}</p>
          )}
        </div>

        {/* What is Presently (only show if not authenticated) */}
        {!isAuthenticated && (
          <div className="bg-muted rounded-lg p-4 mb-6">
            <h3 className="font-semibold mb-2 text-foreground">What is Presently?</h3>
            <p className="text-sm text-muted-foreground">
              Presently is a wishlist app that makes gift-giving easier and more thoughtful. Create
              wishlists for yourself, see what your friends and family want, and secretly claim items
              to purchase - all without spoiling the surprise!
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          {isAuthenticated ? (
            // If authenticated, show manual accept button (in case auto-accept didn't work)
            <button
              onClick={acceptInvitation}
              className="block w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-center hover:opacity-90"
            >
              Accept Invitation
            </button>
          ) : (
            <>
              <Link
                href={`/auth/register?invite=${token}`}
                className="block w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium text-center hover:opacity-90"
              >
                Sign Up & Join Group
              </Link>
              <Link
                href={`/auth/login?invite=${token}`}
                className="block w-full px-6 py-3 bg-secondary text-secondary-foreground rounded-lg font-medium text-center hover:opacity-90"
              >
                Already have an account? Log In
              </Link>
            </>
          )}
        </div>

        {/* Expiration Notice */}
        {invitation?.expires_at && (
          <p className="text-xs text-muted-foreground text-center mt-6">
            This invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}
          </p>
        )}
      </div>
    </div>
  );
}
