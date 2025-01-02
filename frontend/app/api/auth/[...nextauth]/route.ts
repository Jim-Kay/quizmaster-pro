import NextAuth from "next-auth";
import { AuthOptions } from "next-auth";
import { mockAuthConfig } from "./mock-provider";

// Use mock config in development, Auth0 in production
export const authOptions: AuthOptions = (process.env.NODE_ENV as string) === 'development' || (process.env.NODE_ENV as string) === 'test' ? mockAuthConfig : {
  providers: [
    {
      id: "oidc",
      name: "Auth0",
      type: "oauth",
      wellKnown: `${process.env.OIDC_ISSUER_URL}/.well-known/openid-configuration`,
      clientId: process.env.OIDC_CLIENT_ID,
      clientSecret: process.env.OIDC_CLIENT_SECRET,
      authorization: {
        params: {
          scope: "openid email profile",
          audience: process.env.OIDC_ISSUER_URL + "/api/v2/",
        },
      },
      idToken: true,
      checks: ["pkce", "state"],
      profile(profile) {
        return {
          id: profile.sub,
          name: profile.name,
          email: profile.email,
          image: profile.picture,
        };
      },
    },
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      if (account && user) {
        return {
          ...token,
          accessToken: typeof account.access_token === 'string' ? account.access_token : undefined,
          refreshToken: typeof account.refresh_token === 'string' ? account.refresh_token : undefined,
          accessTokenExpires: account.expires_at ? account.expires_at * 1000 : 0,
          user,
        };
      }
      return token;
    },
    async session({ session, token }: { session: any, token: any }) {
      session.user = token.user;
      session.accessToken = token.accessToken as string | undefined;
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
  debug: (process.env.NODE_ENV as string) === "development",
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
