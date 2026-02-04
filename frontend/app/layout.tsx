import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/contexts/AuthContext';
import { AuthLoadingGate } from '@/components/AuthLoadingGate';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Presently - Share Your Wishlist',
  description: 'A multi-group wishlist application for families and friends to share gift ideas and secretly claim items for purchase.',
};

// Force dynamic rendering to prevent build-time errors with Cognito
export const dynamic = 'force-dynamic';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <AuthProvider>
          <AuthLoadingGate>
            {children}
          </AuthLoadingGate>
        </AuthProvider>
      </body>
    </html>
  );
}
