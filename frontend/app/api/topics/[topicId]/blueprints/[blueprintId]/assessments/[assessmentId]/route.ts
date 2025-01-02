import { getServerSession } from 'next-auth';
import { NextResponse } from 'next/server';
import { z } from 'zod';

const answerSchema = z.object({
  questionId: z.string().uuid(),
  answer: z.string(),
});

const submissionSchema = z.object({
  answers: z.array(answerSchema),
  completedAt: z.string().datetime(),
});

export async function GET(
  request: Request,
  { params }: { params: { id: string; blueprintId: string; assessmentId: string } }
) {
  const session = await getServerSession();
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/topics/${params.id}/blueprints/${params.blueprintId}/assessments/${params.assessmentId}`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Assessment not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching assessment:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

export async function POST(
  request: Request,
  { params }: { params: { id: string; blueprintId: string; assessmentId: string } }
) {
  const session = await getServerSession();
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const body = await request.json();
    const validatedData = submissionSchema.parse(body);

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/topics/${params.id}/blueprints/${params.blueprintId}/assessments/${params.assessmentId}/submit`,
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
        return new NextResponse('Assessment not found', { status: 404 });
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
    console.error('Error submitting assessment:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: { id: string; blueprintId: string; assessmentId: string } }
) {
  const session = await getServerSession();
  if (!session) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/topics/${params.id}/blueprints/${params.blueprintId}/assessments/${params.assessmentId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Assessment not found', { status: 404 });
      }
      throw new Error(`API error: ${response.status}`);
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting assessment:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
