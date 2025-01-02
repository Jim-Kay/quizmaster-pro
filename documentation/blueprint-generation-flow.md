# Blueprint Generation Flow

This document explains the implementation of the blueprint generation feature in QuizMaster Pro, which serves as a reference for implementing similar long-running processes in the application.

## Overview

Blueprint generation is a long-running process that involves:
1. Initiating the generation process
2. Redirecting to a status page
3. Polling for status updates
4. Handling completion or errors

## Components Structure

```
frontend/
├── app/
│   ├── topics/[topicId]/
│   │   └── blueprints/
│   │       ├── generate/
│   │       │   ├── page.tsx           # Initial generation page
│   │       │   └── content.tsx        # Main generation UI component
│   │       └── generate-status/
│   │           └── page.tsx           # Status polling page
│   └── api/
│       └── topics/[topicId]/
│           └── blueprints/
│               └── generate/
│                   └── status/
│                       └── route.ts    # Frontend API route
backend/
└── api/
    └── routers/
        └── blueprint_generation.py     # Backend API endpoints
```

## Implementation Details

### 1. Starting Generation

#### Frontend (`content.tsx`)
```typescript
const startGeneration = async () => {
    setIsGenerating(true);
    try {
        const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error(`Failed to start generation: ${response.status}`);
        }

        const data = await response.json();
        setBlueprintId(data.id);
        setStatus(data);
        pollStatus(data.id);
    } catch (error) {
        setIsGenerating(false);
        showErrorToast('Failed to start generation');
    }
};
```

#### Backend (`blueprint_generation.py`)
```python
@router.post("/topics/{topic_id}/blueprints/generate")
async def generate_blueprint(
    topic_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Create initial blueprint record
    blueprint = Blueprint(
        topic_id=topic_id,
        status="generating",
        generation_started_at=datetime.now(timezone.utc)
    )
    db.add(blueprint)
    await db.commit()

    # Start background task
    background_tasks.add_task(generate_blueprint_background, blueprint.id)
    
    return blueprint
```

### 2. Status Polling Implementation

#### Frontend Status Polling (`content.tsx`)
```typescript
const POLL_INTERVAL = 5000;  // 5 seconds
const MAX_RETRIES = 100;
const RETRY_DELAY = 5000;    // 5 second retry delay

const pollStatus = async (blueprintId: string, retryCount = 0) => {
    if (!isGenerating || !blueprintId) return;

    try {
        const response = await fetch(
            `/api/topics/${topicId}/blueprints/${blueprintId}/status`
        );
        
        if (!response.ok) {
            throw new Error(`Failed to fetch status: ${response.status}`);
        }

        const data = await response.json();
        setStatus(data);

        switch (data.status) {
            case 'completed':
                setIsGenerating(false);
                showSuccessToast('Generation completed!');
                router.push(`/topics/${topicId}/blueprints/${blueprintId}`);
                break;
            
            case 'error':
                setIsGenerating(false);
                showErrorToast(data.error || 'Generation failed');
                break;
            
            default:
                // Continue polling for non-terminal states
                setTimeout(() => pollStatus(blueprintId, 0), POLL_INTERVAL);
        }
    } catch (error) {
        // Implement retry logic
        if (retryCount < MAX_RETRIES) {
            setTimeout(
                () => pollStatus(blueprintId, retryCount + 1), 
                RETRY_DELAY
            );
        } else {
            setIsGenerating(false);
            showErrorToast('Failed to check status');
        }
    }
};
```

#### Backend Status Endpoint (`blueprint_generation.py`)
```python
@router.get("/topics/{topic_id}/blueprints/{blueprint_id}/status")
async def get_blueprint_status(
    topic_id: UUID,
    blueprint_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Verify topic exists
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Get blueprint status
    blueprint = await db.get(Blueprint, blueprint_id)
    if not blueprint or blueprint.topic_id != topic_id:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    # Check for timeout
    if blueprint.status == "generating" and blueprint.generation_started_at:
        time_elapsed = datetime.now(timezone.utc) - blueprint.generation_started_at
        if time_elapsed.total_seconds() > 600:  # 10 minutes
            blueprint.status = "error"
            blueprint.description = "Generation timed out"
            await db.commit()

    return BlueprintStatusResponse(
        id=blueprint.blueprint_id,
        status=blueprint.status,
        title=blueprint.title,
        description=blueprint.description,
        terminal_objectives_count=blueprint.terminal_objectives_count or 0,
        enabling_objectives_count=blueprint.enabling_objectives_count or 0,
    )
```

## Asynchronous vs Synchronous Operations

Understanding which parts of the blueprint generation process should be synchronous versus asynchronous is crucial for building a responsive and scalable application.

### Synchronous Operations

These operations need to complete before proceeding:

1. **Initial Blueprint Creation**
   ```python
   # Backend: Synchronous database operations
   blueprint = Blueprint(
       topic_id=topic_id,
       status="generating",
       generation_started_at=datetime.now(timezone.utc)
   )
   db.add(blueprint)
   await db.commit()  # Wait for commit to ensure blueprint exists
   ```

2. **Status Checks**
   ```python
   # Backend: Synchronous validation
   topic = await db.get(Topic, topic_id)  # Must verify topic exists
   if not topic:
       raise HTTPException(status_code=404)

   blueprint = await db.get(Blueprint, blueprint_id)  # Must get current status
   if not blueprint:
       raise HTTPException(status_code=404)
   ```

3. **Error Handling**
   ```typescript
   // Frontend: Synchronous error processing
   if (!response.ok) {
       const error = await response.text();  // Must get error details
       throw new Error(`Failed to start generation: ${error}`);
   }
   ```

### Asynchronous Operations

These operations run independently of the main request-response cycle:

1. **Blueprint Generation Process**
   ```python
   # Backend: Async background task
   @router.post("/topics/{topic_id}/blueprints/generate")
   async def generate_blueprint(
       background_tasks: BackgroundTasks,  # FastAPI background task manager
   ):
       # Start the long-running process asynchronously
       background_tasks.add_task(
           generate_blueprint_background,
           blueprint.blueprint_id
       )
       return blueprint  # Return immediately, don't wait for generation
   ```

2. **Status Polling**
   ```typescript
   // Frontend: Async polling with setTimeout
   const pollStatus = async (blueprintId: string) => {
       try {
           const response = await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}/status`);
           const data = await response.json();
           
           if (data.status !== 'completed') {
               // Schedule next poll asynchronously
               setTimeout(() => pollStatus(blueprintId), POLL_INTERVAL);
           }
       } catch (error) {
           // Handle errors asynchronously
           setTimeout(() => pollStatus(blueprintId), RETRY_DELAY);
       }
   };
   ```

3. **UI Updates**
   ```typescript
   // Frontend: Async state updates
   useEffect(() => {
       if (isGenerating && blueprintId) {
           pollStatus(blueprintId);  // Start async polling
       }
       
       return () => {
           // Cleanup runs asynchronously when component unmounts
           setIsGenerating(false);
       };
   }, [isGenerating, blueprintId]);
   ```

### Why This Separation Matters

1. **User Experience**
   - Synchronous operations in the critical path must be fast
   - Long-running operations must be asynchronous to keep UI responsive
   - Status updates should be asynchronous to prevent UI blocking

2. **Resource Management**
   - Database connections are released quickly for sync operations
   - Background tasks can use separate connection pools
   - Memory usage is better managed with async operations

3. **Scalability**
   - Async background tasks can be distributed across workers
   - Web servers remain responsive to new requests
   - Database connections are used efficiently

4. **Error Handling**
   - Sync operations can fail fast with immediate feedback
   - Async operations can implement retry logic
   - Different error handling strategies for different types of failures

### Best Practices for Async/Sync Design

1. **Keep Synchronous Operations Light**
   ```python
   # Good: Quick database check
   blueprint = await db.get(Blueprint, blueprint_id)
   
   # Bad: Long-running operation in request handler
   blueprint = await generate_entire_blueprint()  # Don't do this
   ```

2. **Use Background Tasks for Heavy Lifting**
   ```python
   # Good: Offload to background task
   background_tasks.add_task(generate_blueprint_background, blueprint_id)
   
   # Bad: Blocking the request thread
   await long_running_generation()  # Don't do this
   ```

3. **Implement Proper Cleanup**
   ```typescript
   // Good: Cleanup on component unmount
   useEffect(() => {
       if (isGenerating) {
           const pollId = setInterval(pollStatus, 5000);
           return () => clearInterval(pollId);  // Clean up
       }
   }, [isGenerating]);
   ```

4. **Handle Edge Cases**
   ```python
   # Good: Handle concurrent generation attempts
   existing_blueprint = await db.execute(
       select(Blueprint).where(
           and_(
               Blueprint.topic_id == topic_id,
               Blueprint.status == "generating"
           )
       )
   ).scalar_one_or_none()
   
   if existing_blueprint:
       raise HTTPException(status_code=400)
   ```

### Common Async/Sync Pitfalls

1. **Blocking Operations in Async Code**
   ```python
   # Bad: Blocking I/O in async function
   time.sleep(5)  # Blocks the event loop
   
   # Good: Async sleep
   await asyncio.sleep(5)  # Cooperative with event loop
   ```

2. **Memory Leaks in Polling**
   ```typescript
   // Bad: No cleanup
   setInterval(pollStatus, 5000);
   
   // Good: Proper cleanup
   const interval = setInterval(pollStatus, 5000);
   return () => clearInterval(interval);
   ```

3. **Race Conditions**
   ```python
   # Bad: Race condition prone
   blueprint.status = "generating"
   await db.commit()
   
   # Good: Use database locks or constraints
   await db.execute(
       update(Blueprint)
       .where(Blueprint.status == "draft")
       .values(status="generating")
   )
   ```

## Progress Tracking

The UI shows a progress bar calculated based on the number of objectives generated:

```typescript
const calculateProgress = (status: BlueprintStatus | null): number => {
    if (!status) return 0;
    
    switch (status.status) {
        case 'completed':
            return 100;
        case 'error':
            return 0;
        case 'generating':
            // Calculate progress based on objectives count
            const targetObjectives = 10;
            const progress = (status.terminal_objectives_count / targetObjectives) * 100;
            return Math.min(Math.max(progress, 5), 90);
        default:
            return 0;
    }
};
```

## Best Practices

1. **Error Handling**
   - Implement retry logic for transient failures
   - Show user-friendly error messages
   - Log errors for debugging
   - Handle timeouts appropriately

2. **State Management**
   - Keep track of generation state
   - Handle component unmounting
   - Clean up intervals/timeouts
   - Update UI based on status changes

3. **User Experience**
   - Show loading states
   - Display progress indicators
   - Provide clear success/error messages
   - Enable cancellation if possible

4. **API Design**
   - Use RESTful routes
   - Include proper validation
   - Return appropriate status codes
   - Include detailed error messages

## Implementing Similar Features

To implement a similar long-running process:

1. **Backend Setup**
   - Create a database model for the process
   - Add status tracking fields
   - Implement background task processing
   - Create status endpoint

2. **Frontend Implementation**
   - Build initiation UI
   - Create status polling component
   - Handle all possible states
   - Implement proper error handling

3. **API Routes**
   - Follow REST conventions
   - Include proper validation
   - Handle authentication/authorization
   - Return appropriate responses

4. **Testing**
   - Test happy path
   - Test error scenarios
   - Test timeout handling
   - Test retry logic

## Common Pitfalls

1. **Memory Leaks**
   - Always clean up intervals/timeouts
   - Handle component unmounting
   - Cancel unnecessary requests

2. **Race Conditions**
   - Handle multiple concurrent requests
   - Implement proper locking if needed
   - Track request state properly

3. **Error States**
   - Handle all possible error scenarios
   - Provide clear error messages
   - Implement proper retry logic

4. **Performance**
   - Use appropriate polling intervals
   - Implement exponential backoff
   - Cache responses when possible
   - Clean up resources properly

## Conclusion

This implementation provides a robust foundation for handling long-running processes in a web application. The key aspects are:
- Clear separation of concerns
- Proper error handling
- Good user experience
- Scalable architecture

When implementing similar features, focus on these aspects while adapting the specific business logic to your needs.
