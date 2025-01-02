'use client';

import { signIn } from "next-auth/react";
import { useSearchParams, useRouter } from "next/navigation";

export default function SignIn() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const handleSignIn = async () => {
    const callbackUrl = searchParams.get('callbackUrl') || '/';
    console.log('Signing in with callbackUrl:', callbackUrl);
    
    try {
      // In mock mode, use the mock provider
      if (process.env.NEXT_PUBLIC_MOCK_AUTH === "true") {
        const result = await signIn("mock", { 
          callbackUrl,
          redirect: true
        });
        console.log('Sign in result:', result);
      } else {
        // In production mode, use Auth0
        await signIn("oidc", { callbackUrl });
      }
    } catch (error) {
      console.error('Sign in error:', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Welcome to QuizMaster Pro
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {process.env.NEXT_PUBLIC_MOCK_AUTH === "true"
              ? "Development Mode - Auto Sign In"
              : "Sign in to access your assessments and progress"}
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <button
            onClick={handleSignIn}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {process.env.NEXT_PUBLIC_MOCK_AUTH === "true"
              ? "Development Sign In"
              : "Sign in with Auth0"}
          </button>
        </div>
      </div>
    </div>
  );
}
