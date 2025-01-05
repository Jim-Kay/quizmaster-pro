import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}`);
  const data = await response.json();
  return NextResponse.json(data);
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}/start`, {
    method: 'POST',
  });
  const data = await response.json();
  return NextResponse.json(data);
}
