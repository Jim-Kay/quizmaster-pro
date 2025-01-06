# Poem Generation Flow

This document explains the sequence of events that occur during poem generation in QuizMasterPro, from frontend interaction to backend execution.

## Overview

The poem generation process involves several components:
1. Frontend UI (PoemGenerator component)
2. Flow Execution API
3. Flow Wrapper
4. CrewAI Flow System
5. WebSocket Log Stream

## Sequence Diagram

```mermaid
sequenceDiagram
    participant UI as PoemGenerator UI
    participant FE as Frontend Hooks
    participant API as Flow Execution API
    participant DB as Database
    participant FW as Flow Wrapper
    participant Crew as CrewAI Flow
    participant WS as WebSocket

    UI->>FE: Click "Write Poem"
    Note over FE: Generate idempotency key<br/>from flow name + state
    
    FE->>API: POST /api/flows/executions
    
    API->>DB: Check idempotency key
    
    alt Key exists
        DB-->>API: Return existing execution
        API-->>FE: Return existing execution
    else Key not found
        API->>FW: Create new flow execution
        FW->>DB: Store execution record
        DB-->>FW: Return execution ID
        FW-->>API: Return execution details
        API->>DB: Store idempotency key
        API-->>FE: Return new execution
    end
    
    FE->>API: POST /executions/{id}/start
    API->>FW: Start flow execution
    FW->>Crew: Initialize and run flow
    
    par Log Streaming
        FE->>WS: Connect to /executions/{id}/logs/ws
        Crew->>DB: Write logs
        DB->>WS: Stream logs to client
        WS-->>FE: Send log messages
        FE->>UI: Update log display
    and Status Polling
        loop Every 5 seconds
            FE->>API: GET /executions/{id}
            API->>DB: Get execution status
            DB-->>API: Return status
            API-->>FE: Return status
            FE->>UI: Update status display
        end
    end
    
    Crew-->>FW: Flow completed
    FW->>DB: Update execution status
    
    Note over UI: Display completion status<br/>and final logs
```

## Detailed Flow Explanation

### 1. Initial Request
- User clicks "Write Poem" button in the PoemGenerator component
- Frontend generates an idempotency key based on:
  - Flow name ("poem")
  - Topic title and description
  - Timestamp (rounded to 5 seconds)
- Frontend sends POST request to create execution

### 2. Execution Creation
- Backend receives request with idempotency key
- Checks database for existing execution with same key
- If found, returns existing execution
- If not found:
  - Creates new flow execution record
  - Stores idempotency key in database
  - Returns execution details to frontend

### 3. Execution Start
- Frontend receives execution ID
- Sends request to start execution
- Backend initiates flow through FlowWrapper
- CrewAI flow begins execution

### 4. Parallel Processes
Two processes run concurrently:

#### Log Streaming
- Frontend establishes WebSocket connection
- CrewAI writes logs to database
- Logs are streamed in real-time through WebSocket
- Frontend updates UI with new log messages

#### Status Polling
- Frontend polls execution status every 5 seconds
- Backend checks database for current status
- UI updates progress bar and status display

### 5. Completion
- CrewAI flow completes
- FlowWrapper updates execution status
- Frontend receives final status
- UI displays completion state and final logs

## Error Handling

### Frontend
- Prevents multiple simultaneous executions
- Implements exponential backoff for WebSocket reconnection
- Displays user-friendly error messages
- Provides retry functionality

### Backend
- Validates all requests with JWT authentication
- Uses idempotency keys to prevent duplicate executions
- Implements proper error status codes
- Logs errors for debugging

## Important Considerations

1. **Idempotency**
   - Keys expire after 24 hours
   - Scoped to specific user
   - Based on flow input parameters

2. **State Management**
   - Frontend tracks execution state
   - Prevents concurrent executions
   - Handles disconnections gracefully

3. **Performance**
   - Logs streamed in real-time
   - Status polling rate limited
   - Database indexes for efficient queries

4. **Security**
   - All endpoints require authentication
   - User-scoped executions
   - Sanitized log output
