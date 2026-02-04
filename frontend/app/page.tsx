'use client'

import Link from 'next/link'
import { ThemeToggle } from '@/components/ThemeToggle'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-8 py-16">
        <div className="flex justify-end mb-8">
          <ThemeToggle />
        </div>
        <div className="text-center">
          <h1 className="text-5xl font-bold text-foreground mb-4">Presently</h1>
          <p className="text-xl text-muted-foreground mb-8">
            Share wishlists with family and friends. Never wonder what to buy again!
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/auth/register"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 font-medium"
            >
              Get Started
            </Link>
            <Link
              href="/auth/login"
              className="px-6 py-3 bg-card text-primary border border-primary rounded-lg hover:bg-accent font-medium"
            >
              Sign In
            </Link>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="bg-card text-card-foreground p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Create Groups</h3>
            <p className="text-muted-foreground">
              Organize wishlists by family, friends, or any group you want.
            </p>
          </div>
          <div className="bg-card text-card-foreground p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Add Wishlists</h3>
            <p className="text-muted-foreground">
              Share what you want with your groups. Include links, prices, and priorities.
            </p>
          </div>
          <div className="bg-card text-card-foreground p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Secret Purchases</h3>
            <p className="text-muted-foreground">
              Claim items without the recipient knowing. Keep the surprise alive!
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
