'use client';

import { SessionProvider } from 'next-auth/react';
import ChakraProvider from "@/components/providers/ChakraProvider";
import QueryProvider from '@/providers/QueryProvider';
import Navbar from "@/components/layout/Navbar";
import EnvironmentIndicator from "@/components/EnvironmentIndicator";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <ChakraProvider>
        <Navbar />
        <QueryProvider>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </QueryProvider>
        <EnvironmentIndicator />
      </ChakraProvider>
    </SessionProvider>
  );
}
