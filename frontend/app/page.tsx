'use client'

import Link from 'next/link'
import { ThemeToggle } from '@/components/ThemeToggle'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-4xl mx-auto px-8 py-16">
        <div className="flex justify-end mb-8">
          <ThemeToggle />
        </div>
        <div className="text-center">
          <h1 className="text-5xl font-bold mb-4">Presently</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Share wishlists with family and friends. Never wonder what to buy again!
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/auth/register"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Get Started
            </Link>
            <Link
              href="/auth/login"
              className="px-6 py-3 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 font-medium"
            >
              Sign In
            </Link>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Create Groups</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Organize wishlists by family, friends, or any group you want.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Add Wishlists</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Share what you want with your groups. Include links, prices, and priorities.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Secret Purchases</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Claim items without the recipient knowing. Keep the surprise alive!
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
