import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    const isAuthenticated = !!req.nextauth?.token;
    const isAuthPage = req.nextUrl.pathname.startsWith('/auth/');

    // If user is authenticated and trying to access auth page, redirect to home
    if (isAuthenticated && isAuthPage) {
      return NextResponse.redirect(new URL('/', req.url));
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        return !!token;
      },
    },
    pages: {
      signIn: "/auth/signin",
    },
  }
);

export const config = {
  matcher: [
    "/topics/:path*",
    "/blueprints/:path*",
    "/assessments/:path*",
    "/auth/:path*",
  ],
};
