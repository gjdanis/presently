'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/contexts/AuthContext';
import type { Invitation } from '@/lib/types';

interface InvitePageProps {
  params: Promise<{ token: string }>;
}

export default function InvitePage({ params }: InvitePageProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [alreadyMember, setAlreadyMember] = useState(false);

  // Unwrap params promise
  useEffect(() => {
    params.then((p) => setToken(p.token));
  }, [params]);

  // Load invitation when token is available
  useEffect(() => {
    if (!token || authLoading) return;

    async function loadInvitation() {
      try {
        // Fetch invitation details from backend
        const invitationData = await api.getInvitation(token);
        setInvitation(invitationData);

        // If user is logged in, auto-accept
        if (isAuthenticated) {
          await acceptInvitation();
        }

        setLoading(false);
      } catch (err: any) {
        console.error('Error loading invitation:', err);
        setError(err.message || 'Failed to load invitation. The invitation may be invalid or expired.');
        setLoading(false);
      }
    }

    loadInvitation();
  }, [token, isAuthenticated, authLoading]);

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
      console.error('Error accepting invitation:', err);
      setError(err.message || 'Failed to accept invitation');
      setAccepting(false);
    }
  }

  // Loading state
  if (loading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading invitation...</p>
        </div>
      </div>
    );
  }

  // Error state (invalid or expired invitation)
  if (error && !invitation) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
            Invalid or Expired Invitation
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mb-6">{error}</p>
          <Link
            href="/auth/login"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  // Success state (accepted)
  if (accepted || (isAuthenticated && accepting)) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold text-green-600 dark:text-green-400 mb-4">
            {alreadyMember
              ? 'Already a Member!'
              : accepting
              ? 'Joining Group...'
              : 'Welcome to the Group!'}
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            {alreadyMember
              ? `You're already a member of ${invitation?.group_name}.`
              : accepting
              ? 'Please wait while we add you to the group...'
              : `You've successfully joined ${invitation?.group_name}!`}
          </p>
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
            </div>
          )}
          {!error && !accepting && (
            <Link
              href={`/dashboard/groups/${invitation?.group_id}`}
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              Go to Group
            </Link>
          )}
        </div>
      </div>
    );
  }

  // Not logged in - show invitation details
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">🎁</div>
          <h1 className="text-3xl font-bold mb-2 text-gray-900 dark:text-gray-100">Presently</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Wishlist sharing made simple</p>
        </div>

        {/* Invitation Details */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">You've Been Invited!</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            <strong>{invitation?.invited_by.name || invitation?.invited_by.email}</strong> has
            invited you to join the group{' '}
            <strong>"{invitation?.group_name}"</strong> on Presently.
          </p>
          {invitation?.group_description && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{invitation.group_description}</p>
          )}
        </div>

        {/* What is Presently */}
        <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-2 text-gray-900 dark:text-gray-100">What is Presently?</h3>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Presently is a wishlist app that makes gift-giving easier and more thoughtful. Create
            wishlists for yourself, see what your friends and family want, and secretly claim items
            to purchase - all without spoiling the surprise!
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Link
            href={`/auth/register?invite=${token}`}
            className="block w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium text-center hover:bg-blue-700"
          >
            Sign Up & Join Group
          </Link>
          <Link
            href={`/auth/login?invite=${token}`}
            className="block w-full px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg font-medium text-center hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Already have an account? Log In
          </Link>
        </div>

        {/* Expiration Notice */}
        {invitation?.expires_at && (
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-6">
            This invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}
          </p>
        )}
      </div>
    </div>
  );
}
