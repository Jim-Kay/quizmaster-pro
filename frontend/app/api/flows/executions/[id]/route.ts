import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const authHeader = request.headers.get('Authorization');
  console.log('[Flow API] Getting execution:', params.id);
  console.log('[Flow API] Auth header present:', !!authHeader);
  
  try {
    console.log('[Flow API] Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}`);
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}`, {
      headers: {
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    console.log('[Flow API] Response status:', response.status);

    if (response.status === 401) {
      console.log('[Flow API] Unauthorized request');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!response.ok) {
      console.log('[Flow API] Error response:', response.status, response.statusText);
      return NextResponse.json({ error: `Failed to fetch execution: ${response.statusText}` }, { status: response.status });
    }

    const data = await response.json();
    console.log('[Flow API] Execution data:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Flow API] Error:', error);
    return NextResponse.json({ error: 'Failed to fetch execution' }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const authHeader = request.headers.get('Authorization');
  console.log('[Flow API] Starting execution:', params.id);
  console.log('[Flow API] Auth header present:', !!authHeader);
  
  try {
    console.log('[Flow API] Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}/start`);
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify(await request.json()),
    });

    console.log('[Flow API] Response status:', response.status);

    if (response.status === 401) {
      console.log('[Flow API] Unauthorized request');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!response.ok) {
      console.log('[Flow API] Error response:', response.status, response.statusText);
      return NextResponse.json({ error: `Failed to start execution: ${response.statusText}` }, { status: response.status });
    }

    const data = await response.json();
    console.log('[Flow API] Execution started:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Flow API] Error:', error);
    return NextResponse.json({ error: 'Failed to start execution' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const authHeader = request.headers.get('Authorization');
  console.log('[Flow API] Deleting execution:', params.id);
  console.log('[Flow API] Auth header present:', !!authHeader);
  
  try {
    console.log('[Flow API] Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}`);
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${params.id}`, {
      method: 'DELETE',
      headers: {
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    console.log('[Flow API] Response status:', response.status);

    if (response.status === 401) {
      console.log('[Flow API] Unauthorized request');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!response.ok) {
      console.log('[Flow API] Error response:', response.status, response.statusText);
      return NextResponse.json({ error: `Failed to delete execution: ${response.statusText}` }, { status: response.status });
    }

    const data = await response.json();
    console.log('[Flow API] Execution deleted:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Flow API] Error:', error);
    return NextResponse.json({ error: 'Failed to delete execution' }, { status: 500 });
  }
}
