import { AuthOptions } from "next-auth";
import jwt from 'jsonwebtoken';

const MOCK_USER_ID = "550e8400-e29b-41d4-a716-446655440000"; // Same as backend
const JWT_SECRET = process.env.NEXTAUTH_SECRET || "development-secret";

const generateMockJwt = () => {
  const payload = {
    sub: MOCK_USER_ID,
    email: "jkay65@gmail.com",
    name: "Development User",
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60), // 24 hours
  };

  return jwt.sign(payload, process.env.NEXTAUTH_SECRET || "development-secret");
};

export const mockAuthConfig: AuthOptions = {
  providers: [
    {
      id: "mock",
      name: "Mock Auth",
      type: "credentials",
      credentials: {},
      async authorize(credentials: any, req) {
        // Get the callbackUrl from the request
        const callbackUrl = req?.body?.callbackUrl || "/";

        // Always return a mock user with the correct callback URL
        return {
          id: MOCK_USER_ID,
          email: "jkay65@gmail.com",
          name: "Development User",
          image: null,
          callbackUrl,
        };
      },
    },
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const mockToken = jwt.sign({ sub: MOCK_USER_ID }, JWT_SECRET, { algorithm: 'HS256' });
        return {
          ...token,
          user,
          accessToken: mockToken,
          accessTokenExpires: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
        };
      }

      // Return previous token if the access token has not expired yet
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Access token has expired, generate a new one
      return {
        ...token,
        accessToken: jwt.sign({ sub: MOCK_USER_ID }, JWT_SECRET, { algorithm: 'HS256' }),
        accessTokenExpires: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      };
    },
    async session({ session, token }: { session: any, token: any }) {
      session.user = token.user;
      session.accessToken = token.accessToken;
      session.accessTokenExpires = token.accessTokenExpires;
      return session;
    },
    async redirect({ url, baseUrl }) {
      // Try to decode the URL if it's encoded
      try {
        url = decodeURIComponent(url);
      } catch (e) {
        // If decoding fails, use the original URL
        console.warn('Failed to decode URL:', e);
      }

      // Check if URL is relative (starts with /)
      if (url.startsWith('/')) {
        return url;
      }
      // If URL is already absolute and starts with baseUrl, allow it
      else if (url.startsWith(baseUrl)) {
        // Extract the path from the absolute URL
        const path = url.slice(baseUrl.length);
        return path;
      }
      // Otherwise, redirect to home
      return '/';
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },
  secret: process.env.NEXTAUTH_SECRET || "development-secret",
  debug: process.env.NODE_ENV === "development",
};
