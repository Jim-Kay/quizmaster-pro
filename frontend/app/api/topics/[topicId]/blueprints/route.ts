import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { z } from 'zod';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

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

const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;

export async function GET(
  request: Request,
  { params }: { params: { topicId: string } }
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

    console.log('Fetching blueprints for topic:', params.topicId);
    const response = await fetch(
      `${backendUrl}/api/topics/${params.topicId}/blueprints`,
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
        return NextResponse.json({ error: 'Topic not found' }, { status: 404 });
      }
      return NextResponse.json(
        { error: 'Failed to fetch blueprints' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Received blueprints:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching blueprints:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: Request,
  { params }: { params: { topicId: string } }
) {
  try {
    const session = await getServerSession(authConfig);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const body = await request.json();
    const validatedData = blueprintSchema.parse(body);

    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error('BACKEND_URL environment variable is not set');
      return new NextResponse('Server configuration error', { status: 500 });
    }

    const response = await fetch(
      `${backendUrl}/api/topics/${params.topicId}/blueprints`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validatedData),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error (${response.status}):`, errorText);
      if (response.status === 404) {
        return new NextResponse('Topic not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error creating blueprint:', error);
    if (error instanceof z.ZodError) {
      return NextResponse.json({ message: 'Invalid request data', errors: error.errors }, { status: 400 });
    }
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
