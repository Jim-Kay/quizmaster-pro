import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';
import { z } from 'zod';

const questionSchema = z.object({
  content: z.string().min(10),
  type: z.enum(['multiple_choice', 'short_answer', 'essay']),
  options: z.array(z.string()).optional(),
  correctAnswer: z.string().optional(),
  points: z.number().min(1),
  objectiveId: z.string().uuid(),
});

const assessmentSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10).optional(),
  timeLimit: z.number().min(5).optional(), // in minutes
  passingScore: z.number().min(0).max(100),
  questions: z.array(questionSchema),
});

export async function GET(
  request: Request,
  { params }: { params: { id: string; blueprintId: string } }
) {
  const session = await getServerSession();
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.id}/blueprints/${params.blueprintId}/assessments`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Blueprint not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching assessments:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

export async function POST(
  request: Request,
  { params }: { params: { id: string; blueprintId: string } }
) {
  const session = await getServerSession();
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const body = await request.json();
    const validatedData = assessmentSchema.parse(body);

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/topics/${params.id}/blueprints/${params.blueprintId}/assessments`,
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
      if (response.status === 404) {
        return new NextResponse('Blueprint not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { errors: error.errors },
        { status: 400 }
      );
    }
    console.error('Error creating assessment:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
