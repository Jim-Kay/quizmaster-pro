import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { z } from 'zod';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;

const objectiveSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10),
  type: z.enum(['terminal', 'enabling']),
  parentId: z.string().uuid().optional(),
});

const blueprintSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10),
  objectives: z.array(objectiveSchema),
});

export async function GET(
  request: Request,
  { params }: { params: { topicId: string; blueprintId: string } }
) {
  try {
    const session = await getServerSession(authConfig);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}/blueprints/${params.blueprintId}`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Error fetching blueprint:', error);
      return NextResponse.json(
        { error: 'Failed to fetch blueprint' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in GET /api/topics/[topicId]/blueprints/[blueprintId]:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: { topicId: string; blueprintId: string } }
) {
  try {
    const session = await getServerSession(authConfig);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const body = await request.json();
    const validatedData = blueprintSchema.partial().parse(body);

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}/blueprints/${params.blueprintId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(validatedData),
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Error updating blueprint:', error);
      return NextResponse.json(
        { error: 'Failed to update blueprint' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error in PATCH /api/topics/[topicId]/blueprints/[blueprintId]:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: { topicId: string; blueprintId: string } }
) {
  try {
    const session = await getServerSession(authConfig);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.topicId}/blueprints/${params.blueprintId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Error deleting blueprint:', error);
      return NextResponse.json(
        { error: 'Failed to delete blueprint' },
        { status: response.status }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error in DELETE /api/topics/[topicId]/blueprints/[blueprintId]:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
