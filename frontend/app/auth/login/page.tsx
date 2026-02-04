'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/contexts/AuthContext';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signIn } = useAuth();
  const inviteToken = searchParams.get('invite');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await signIn({ email, password });

      // If there's an invite token, redirect to the invite page to accept it
      if (inviteToken) {
        router.push(`/invite/${inviteToken}`);
      } else {
        router.push('/dashboard');
      }
    } catch (err: any) {
      if (process.env.NODE_ENV === 'development') console.error('Login error:', err);
      setError(err.message || 'Invalid email or password');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center">Sign In</h2>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-300">
            Welcome back to Presently
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded">
              {error}
            </div>
          )}
          <div className="space-y-4">
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
                className="input mt-1"
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
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 rounded-md shadow-sm text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <p className="text-center text-sm text-gray-600 dark:text-gray-300">
            Don't have an account?{' '}
            <Link
              href={inviteToken ? `/auth/register?invite=${inviteToken}` : '/auth/register'}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-500"
            >
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full space-y-8 p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
