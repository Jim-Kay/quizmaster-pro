import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('Authorization');
  console.log('[Flow API] Creating new execution');
  console.log('[Flow API] Auth header present:', !!authHeader);
  
  try {
    const body = await request.json();
    console.log('[Flow API] Creating execution with body:', JSON.stringify(body, null, 2));
    
    // Add idempotency key based on flow name and initial state
    const idempotencyKey = Buffer.from(JSON.stringify({
      flow_name: body.flow_name,
      initial_state: body.initial_state
    })).toString('base64');
    
    console.log('[Flow API] Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions`);
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': idempotencyKey,
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify(body),
    });

    console.log('[Flow API] Response status:', response.status);

    if (response.status === 401) {
      console.log('[Flow API] Unauthorized request');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!response.ok) {
      console.log('[Flow API] Error response:', response.status, response.statusText);
      const errorText = await response.text();
      console.log('[Flow API] Error details:', errorText);
      return NextResponse.json({ error: `Failed to create execution: ${response.statusText}`, details: errorText }, { status: response.status });
    }

    const data = await response.json();
    console.log('[Flow API] Execution created:', JSON.stringify(data, null, 2));
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Flow API] Error:', error);
    return NextResponse.json({ error: 'Failed to create execution' }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('Authorization');
  console.log('[Flow API] Listing executions');
  console.log('[Flow API] Auth header present:', !!authHeader);
  
  try {
    // Get query parameters
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const flowName = url.searchParams.get('flow_name');
    
    // Build query string
    const queryParams = new URLSearchParams();
    if (status) queryParams.append('status', status);
    if (flowName) queryParams.append('flow_name', flowName);
    const queryString = queryParams.toString();
    
    console.log('[Flow API] Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions${queryString ? `?${queryString}` : ''}`);
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions${queryString ? `?${queryString}` : ''}`, {
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
      const errorText = await response.text();
      console.log('[Flow API] Error details:', errorText);
      return NextResponse.json({ error: `Failed to list executions: ${response.statusText}`, details: errorText }, { status: response.status });
    }

    const data = await response.json();
    console.log('[Flow API] Executions listed:', JSON.stringify(data, null, 2));
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Flow API] Error:', error);
    return NextResponse.json({ error: 'Failed to list executions' }, { status: 500 });
  }
}
