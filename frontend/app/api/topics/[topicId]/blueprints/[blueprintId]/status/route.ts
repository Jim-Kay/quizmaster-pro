import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;

export async function GET(
  request: Request,
  { params }: { params: { topicId: string; blueprintId: string } }
) {
  try {
    const session = await getServerSession(authConfig);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error('BACKEND_URL environment variable is not set');
      return new NextResponse('Server configuration error', { status: 500 });
    }

    const response = await fetch(
      `${backendUrl}/api/topics/${params.topicId}/blueprints/${params.blueprintId}/status`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error (${response.status}):`, errorText);
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Blueprint not found' },
          { status: 404 }
        );
      }
      return NextResponse.json(
        { error: 'Failed to fetch blueprint status' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching blueprint status:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
