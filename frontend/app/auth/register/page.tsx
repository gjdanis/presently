'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/contexts/AuthContext';

function RegisterForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [confirmingCode, setConfirmingCode] = useState(false);
  const [success, setSuccess] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signUp, confirmSignUp, resendConfirmationCode, signIn } = useAuth();
  const inviteToken = searchParams.get('invite');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate password match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      const result = await signUp({ email, password, name });

      // Check if user is auto-confirmed (dev environment)
      if (result.userConfirmed) {
        // User is already confirmed, sign them in directly
        await signIn({ email, password });
        setSuccess(true);

        setTimeout(() => {
          if (inviteToken) {
            router.push(`/invite/${inviteToken}`);
          } else {
            router.push('/dashboard');
          }
        }, 1500);
      } else {
        // Cognito will send a verification code to the email
        setNeedsConfirmation(true);
      }

      setLoading(false);
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.message || 'Failed to create account');
      setLoading(false);
    }
  };

  const handleConfirmCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setConfirmingCode(true);
    setError(null);

    try {
      await confirmSignUp({ email, code: confirmationCode });

      // After confirmation, sign in the user
      await signIn({ email, password });

      setSuccess(true);

      // Redirect after short delay
      setTimeout(() => {
        if (inviteToken) {
          router.push(`/invite/${inviteToken}`);
        } else {
          router.push('/dashboard');
        }
      }, 1500);
    } catch (err: any) {
      console.error('Confirmation error:', err);
      setError(err.message || 'Invalid confirmation code');
      setConfirmingCode(false);
    }
  };

  const handleResendCode = async () => {
    try {
      await resendConfirmationCode(email);
      setError(null);
      // Show success message temporarily
      const originalError = error;
      setError('Verification code resent to your email');
      setTimeout(() => setError(originalError), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to resend code');
    }
  };

  // Success state
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-green-600">Account Created!</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              Redirecting you to your dashboard...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Email confirmation state
  if (needsConfirmation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div>
            <h2 className="text-3xl font-bold text-center">Verify Your Email</h2>
            <p className="mt-2 text-center text-gray-600 dark:text-gray-300">
              We sent a verification code to <strong>{email}</strong>
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleConfirmCode}>
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Verification Code
              </label>
              <input
                id="code"
                name="code"
                type="text"
                required
                value={confirmationCode}
                onChange={(e) => setConfirmationCode(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-center text-2xl tracking-widest"
                placeholder="123456"
                maxLength={6}
              />
              <p className="mt-2 text-xs text-gray-500 text-center">
                Enter the 6-digit code from your email
              </p>
            </div>

            <button
              type="submit"
              disabled={confirmingCode}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
            >
              {confirmingCode ? 'Verifying...' : 'Verify Email'}
            </button>

            <div className="text-center">
              <button
                type="button"
                onClick={handleResendCode}
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500"
              >
                Didn't receive a code? Resend
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Registration form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center">Create Account</h2>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-300">
            Join Presently today
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleRegister}>
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Full Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Must be at least 8 characters with uppercase, lowercase, number, and symbol
              </p>
            </div>
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>

          <p className="text-center text-sm text-gray-600 dark:text-gray-300">
            Already have an account?{' '}
            <Link
              href={inviteToken ? `/auth/login?invite=${inviteToken}` : '/auth/login'}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-500"
            >
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="text-center">Loading...</div>
          </div>
        </div>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
