# WebSocket Communication in QuizMaster Pro

This document outlines how to establish and use WebSocket connections in QuizMaster Pro.

## Backend Setup

### 1. FastAPI WebSocket Endpoint

```python
@router.websocket("/ws/endpoint")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        # 1. Accept the connection
        await websocket.accept()
        
        # 2. Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_status",
            "message": "Connected successfully"
        })
        
        # 3. Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                # Process data and send responses
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    except Exception as e:
        await websocket.close(code=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 2. Message Types

All WebSocket messages should follow this structure:
```typescript
interface WebSocketMessage {
    type: string;        // Message type (e.g., 'update', 'error')
    message?: string;    // Optional message content
    data?: any;         // Optional data payload
}
```

Common message types:
- `connection_status`: Initial connection confirmation
- `error`: Error messages
- `update`: Status updates
- `complete`: Operation completion

## Frontend Setup

### 1. WebSocket Connection

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/endpoint?token=${token}`);

ws.onopen = () => {
    console.log('Connected to WebSocket');
};

ws.onclose = () => {
    console.log('Disconnected from WebSocket');
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle different message types
    switch (data.type) {
        case 'update':
            handleUpdate(data);
            break;
        case 'error':
            handleError(data);
            break;
        // ... handle other message types
    }
};
```

### 2. React Component Integration

```typescript
function WebSocketComponent() {
    const [connected, setConnected] = useState(false);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        // Connect when component mounts
        const connect = () => {
            ws.current = new WebSocket('ws://localhost:8000/ws/endpoint');
            ws.current.onopen = () => setConnected(true);
            ws.current.onclose = () => setConnected(false);
        };
        
        connect();
        
        // Cleanup on unmount
        return () => {
            ws.current?.close();
        };
    }, []);

    // Send message function
    const sendMessage = (data: any) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data));
        }
    };
}
```

## Authentication

1. Pass authentication token as URL parameter:
```typescript
const wsUrl = `ws://localhost:8000/ws/endpoint?token=${authToken}`;
```

2. In development, use mock authentication:
```typescript
const MOCK_USER_ID = 'f9b5645d-898b-4d58-b10a-a6b50a9d234b';
const wsUrl = `ws://localhost:8000/ws/endpoint?token=${MOCK_USER_ID}`;
```

## Best Practices

1. **Connection Management**
   - Always handle connection errors gracefully
   - Implement reconnection logic with exponential backoff
   - Clean up WebSocket connections when components unmount

2. **Message Handling**
   - Use typed message interfaces
   - Handle all possible message types
   - Include error handling for malformed messages

3. **State Management**
   - Keep track of connection state
   - Buffer messages when connection is lost
   - Update UI to reflect connection status

4. **Security**
   - Always validate authentication tokens on the backend
   - Use secure WebSocket (wss://) in production
   - Sanitize input data before processing

## Example: DevTools WebSocket Testing

The DevTools page provides a complete example of WebSocket implementation:

1. Backend (`/api/routers/dev.py`):
   - WebSocket endpoint with simulation capabilities
   - Message handling with proper error management
   - Progress updates with timing information

2. Frontend (`/frontend/app/devtools/page.tsx`):
   - Connection management with reconnection logic
   - UI updates based on WebSocket messages
   - Configuration controls for testing

## Debugging Tips

1. **Backend Logs**
   - Enable debug logging for WebSocket connections
   - Log message payloads during development
   - Monitor connection lifecycle events

2. **Frontend Console**
   - Watch for connection events in browser console
   - Log received messages for debugging
   - Track connection state changes

3. **Network Tools**
   - Use browser DevTools Network tab
   - Monitor WebSocket frames
   - Check for connection issues

## Common Issues

1. **Connection Failures**
   - Check if backend is running and accessible
   - Verify authentication token is valid
   - Ensure CORS is properly configured

2. **Message Handling**
   - Validate message format on both ends
   - Handle JSON parsing errors
   - Check for missing required fields

3. **State Management**
   - Handle component unmounting properly
   - Clear message buffers when appropriate
   - Update UI state atomically
