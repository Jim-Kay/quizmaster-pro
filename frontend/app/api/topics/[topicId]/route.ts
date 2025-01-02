import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;

const topicSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10),
});

// Function to ensure dates are in ISO format
function ensureValidDates(data: any) {
  const now = new Date().toISOString();
  return {
    ...data,
    created_at: data.created_at ? new Date(data.created_at).toISOString() : now,
    updated_at: data.updated_at ? new Date(data.updated_at).toISOString() : now,
  };
}

export async function GET(
  request: Request,
  { params }: { params: { topicId: string } }
) {
  console.log('GET /api/topics/[topicId] called with id:', params.topicId);
  const session = await getServerSession(authConfig);
  if (!session?.accessToken) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Topic not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    const topicWithDates = ensureValidDates(data);
    return NextResponse.json(topicWithDates);
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: Request,
  { params }: { params: { topicId: string } }
) {
  const session = await getServerSession(authConfig);
  if (!session?.accessToken) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const body = await request.json();
    const validatedData = topicSchema.parse(body);

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(validatedData),
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Topic not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    const topicWithDates = ensureValidDates(data);
    return NextResponse.json(topicWithDates);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: { topicId: string } }
) {
  const session = await getServerSession(authConfig);
  if (!session?.accessToken) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Topic not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
