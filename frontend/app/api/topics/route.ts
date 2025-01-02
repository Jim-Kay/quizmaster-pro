import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';
import { Topic, topicCreateSchema } from '@/lib/models/schemas';
import { mockAuthConfig } from '../auth/[...nextauth]/mock-provider';
import { z } from 'zod';

export async function GET() {
  const session = await getServerSession(mockAuthConfig);
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL}/api/topics`, {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    return NextResponse.json(data);
  } catch (error: unknown) {
    console.error('Error fetching topics:', error);
    if (error instanceof Error) {
      console.error('Error details:', error.message, error.stack);
    } else {
      console.error('Unknown error type:', error);
    }
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

export async function POST(request: Request) {
  const session = await getServerSession(mockAuthConfig);
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const validatedData = topicCreateSchema.parse(await request.json());

    const response = await fetch(`${process.env.BACKEND_URL}/api/topics`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(validatedData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', response.status, errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log('Response data:', data);
    return NextResponse.json(data, { status: 201 });
  } catch (error: unknown) {
    console.error('Error creating topic:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { errors: error.errors },
        { status: 400 }
      );
    }
    
    if (error instanceof Error) {
      console.error('Error details:', error.message, error.stack);
    } else {
      console.error('Unknown error type:', typeof error, error);
    }
    
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
