'use client';

import { useState } from 'react';
import Link from 'next/link';
import { forgotPassword, confirmForgotPassword } from '@/lib/auth';

type Step = 'email' | 'code' | 'success';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await forgotPassword(email);
      setStep('code');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await confirmForgotPassword(email, code, newPassword);
      setStep('success');
    } catch (err: any) {
      setError(err.message || 'Failed to reset password. Please check your code and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full space-y-8 p-8 bg-card rounded-lg shadow">

        {step === 'email' && (
          <>
            <div>
              <h2 className="text-3xl font-bold text-center">Reset Password</h2>
              <p className="mt-2 text-center text-muted-foreground">
                Enter your email and we'll send you a reset code.
              </p>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleSendCode}>
              {error && (
                <div className="bg-destructive/10 text-destructive p-3 rounded">{error}</div>
              )}
              <div>
                <label htmlFor="email" className="block text-sm font-medium">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input mt-1"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 rounded-md shadow-sm text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Reset Code'}
              </button>
              <p className="text-center text-sm text-muted-foreground">
                <Link href="/auth/login" className="text-primary hover:opacity-80">
                  Back to sign in
                </Link>
              </p>
            </form>
          </>
        )}

        {step === 'code' && (
          <>
            <div>
              <h2 className="text-3xl font-bold text-center">Check Your Email</h2>
              <p className="mt-2 text-center text-muted-foreground">
                We sent a reset code to <span className="font-medium text-foreground">{email}</span>.
                Enter it below along with your new password.
              </p>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleResetPassword}>
              {error && (
                <div className="bg-destructive/10 text-destructive p-3 rounded">{error}</div>
              )}
              <div className="space-y-4">
                <div>
                  <label htmlFor="code" className="block text-sm font-medium">
                    Reset code
                  </label>
                  <input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    required
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="input mt-1 tracking-widest text-center text-lg"
                    placeholder="000000"
                  />
                </div>
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium">
                    New password
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium">
                    Confirm new password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input mt-1"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 rounded-md shadow-sm text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring disabled:opacity-50"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
              <p className="text-center text-sm text-muted-foreground">
                Didn't receive a code?{' '}
                <button
                  type="button"
                  onClick={() => setStep('email')}
                  className="text-primary hover:opacity-80"
                >
                  Try again
                </button>
              </p>
            </form>
          </>
        )}

        {step === 'success' && (
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold">Password Reset</h2>
            <p className="text-muted-foreground">
              Your password has been updated. You can now sign in with your new password.
            </p>
            <Link
              href="/auth/login"
              className="inline-block mt-4 py-2 px-6 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:opacity-90"
            >
              Sign In
            </Link>
          </div>
        )}

      </div>
    </div>
  );
}
