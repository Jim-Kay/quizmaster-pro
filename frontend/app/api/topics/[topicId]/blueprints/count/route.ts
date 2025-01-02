import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;

export async function GET(
  request: Request,
  { params }: { params: { topicId: string } }
) {
  const session = await getServerSession(authConfig);
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error('BACKEND_URL environment variable is not set');
      return new NextResponse('Server configuration error', { status: 500 });
    }

    const response = await fetch(
      `${backendUrl}/api/topics/${params.topicId}/blueprints/count`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    console.error('Error fetching blueprint count:', error);
    if (error instanceof Error) {
      console.error('Error details:', error.message, error.stack);
    } else {
      console.error('Unknown error type:', error);
    }
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
