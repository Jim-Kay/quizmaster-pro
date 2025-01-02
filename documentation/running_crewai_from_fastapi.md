# Running CrewAI from FastAPI Endpoints

This guide explains how to properly integrate CrewAI with FastAPI endpoints, using our blueprint generation implementation as a practical example.

## Overview

Running CrewAI from FastAPI requires careful handling of asynchronous operations and background tasks. Here are the key considerations:

1. CrewAI operations are CPU-intensive and can take time
2. We need to avoid blocking the FastAPI event loop
3. Database operations need to be handled properly in async context
4. Status updates and error handling are crucial
5. API routes should follow REST conventions

## Implementation Pattern

### 1. API Route Structure

Follow RESTful conventions for your routes:

```python
router = APIRouter(tags=["blueprint_generation"])

# Generation endpoint
@router.post("/topics/{topic_id}/blueprints/generate")
async def generate_blueprint(
    topic_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    try:
        # Verify topic exists
        topic = await db.get(Topic, topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
            
        # Check for existing generation
        existing = await db.execute(
            select(Blueprint).where(
                and_(
                    Blueprint.topic_id == topic_id,
                    Blueprint.status == "generating"
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A blueprint is already being generated"
            )

        # Create initial blueprint
        blueprint = Blueprint(
            topic_id=topic_id,
            created_by=current_user_id,
            title=f"{topic.title} Blueprint",
            description="Generating blueprint...",
            status="generating",
            generation_started_at=datetime.now(timezone.utc)
        )
        db.add(blueprint)
        await db.commit()
        
        # Start background task
        background_tasks.add_task(
            generate_blueprint_background,
            blueprint.blueprint_id,
            topic.title,
            topic.description,
            current_user_id
        )
        
        return blueprint
    except Exception as e:
        logger.error(f"Error in generate_blueprint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Status endpoint
@router.get("/topics/{topic_id}/blueprints/{blueprint_id}/status")
async def get_blueprint_status(
    topic_id: UUID,
    blueprint_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        # First verify that the topic exists
        topic = await db.get(Topic, topic_id)
        if not topic:
            raise HTTPException(
                status_code=404,
                detail="Topic not found"
            )

        # Then get the blueprint, ensuring it belongs to the topic
        blueprint = await db.get(Blueprint, blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found"
            )
            
        if blueprint.topic_id != topic_id:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found for this topic"
            )

        # Check for timeout if status is generating
        if blueprint.status == "generating" and blueprint.generation_started_at:
            time_elapsed = datetime.now(timezone.utc) - blueprint.generation_started_at
            if time_elapsed.total_seconds() > 600:  # 10 minutes
                blueprint.status = "error"
                blueprint.description = "Blueprint generation timed out"
                await db.commit()

        return BlueprintStatusResponse(
            id=blueprint.blueprint_id,
            status=blueprint.status,
            title=blueprint.title,
            description=blueprint.description,
            terminal_objectives_count=blueprint.terminal_objectives_count or 0,
            enabling_objectives_count=blueprint.enabling_objectives_count or 0,
        )
    except Exception as e:
        logger.error(f"Error in get_blueprint_status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
```

### 2. Background Task Implementation

```python
def generate_blueprint_background(
    blueprint_id: UUID,
    topic_title: str,
    topic_description: str,
    current_user_id: UUID,
) -> None:
    """Background task to generate a blueprint using the BlueprintCrew."""
    import traceback
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    # Create async engine and session
    async_engine = create_async_engine(str(DATABASE_URL))
    AsyncSessionLocal = async_sessionmaker(bind=async_engine)

    async def _generate_blueprint():
        try:
            logger.info(f"Starting background blueprint generation for topic {topic_title}")
            
            async with AsyncSessionLocal() as session:
                try:
                    # Update blueprint status to generating
                    result = await session.execute(
                        select(Blueprint).filter(Blueprint.blueprint_id == blueprint_id)
                    )
                    blueprint = result.scalar_one()
                    blueprint.status = "generating"
                    await session.commit()
                    
                    # Initialize and run CrewAI
                    inputs = {
                        'topic': topic_title,
                        'description': topic_description,
                        'blueprint_id': blueprint_id,
                        'topic_id': None
                    }
                    logger.info("Initializing BlueprintCrew...")
                    blueprint_crew = BlueprintCrew(inputs=inputs)
                    
                    result = blueprint_crew.run()
                    logger.info("BlueprintCrew execution completed")
                    
                    # Update blueprint with results
                    blueprint = await session.get(Blueprint, blueprint_id)
                    blueprint.status = "completed"
                    blueprint.title = result.title
                    blueprint.description = result.description
                    await session.commit()
                    
                except Exception as e:
                    logger.error(f"Error in blueprint generation: {str(e)}")
                    logger.error(traceback.format_exc())
                    blueprint.status = "error"
                    blueprint.description = str(e)
                    await session.commit()
                    
        except Exception as e:
            logger.error(f"Critical error in _generate_blueprint: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try one last time to update status
            try:
                async with AsyncSessionLocal() as session:
                    blueprint = await session.get(Blueprint, blueprint_id)
                    if blueprint:
                        blueprint.status = "error"
                        blueprint.description = f"Critical error: {str(e)}"
                        await session.commit()
            except Exception as inner_e:
                logger.error(f"Failed to update error status: {str(inner_e)}")

    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_generate_blueprint())
    finally:
        loop.close()
```

### 3. CrewAI Class Structure

```python
class BlueprintCrew:
    def __init__(self, inputs: Dict[str, Any] = None):
        self.inputs = inputs
        # Initialize other configurations...

    def run(self) -> BlueprintPydantic:
        """Run the crew and return results."""
        try:
            crew = self.crew()
            result = crew.kickoff()
            return self.finalize_results(result)
        except Exception as e:
            raise ValueError(f"Blueprint generation failed: {str(e)}")

    def crew(self) -> Crew:
        """Create and configure the crew."""
        agent = self.blueprint_agent()
        task = self.design_blueprint_task()
        task.agent = agent

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
```

## Best Practices

1. **API Design**:
   - Follow REST conventions
   - Use proper HTTP methods
   - Include parent resources in routes
   - Validate relationships between resources

2. **Status Updates**:
   - Use descriptive status values:
     - "generating": Task is in progress
     - "completed": Task finished successfully
     - "error": Task failed with error
   - Include progress indicators (e.g., objective counts)
   - Add timestamps for monitoring

3. **Error Handling**:
   - Catch and log all exceptions
   - Update task status on failure
   - Store error details for debugging
   - Handle timeouts appropriately
   - Validate input data thoroughly

4. **Database Operations**:
   - Use async database sessions
   - Properly commit or rollback transactions
   - Handle database errors separately from CrewAI errors
   - Implement proper connection pooling
   - Use transactions for data consistency

5. **Background Tasks**:
   - Use FastAPI's BackgroundTasks for non-blocking operations
   - Return immediately with task details
   - Provide comprehensive status endpoints
   - Implement proper cleanup

6. **Monitoring**:
   - Implement detailed logging
   - Track task duration and completion rates
   - Monitor resource usage
   - Log all critical operations
   - Track error rates and types

## Common Issues and Solutions

1. **Long Running Tasks**
   - Problem: CrewAI tasks can take several minutes
   - Solution: Use background tasks and status updates
   - Solution: Implement timeouts and monitoring

2. **Memory Usage**
   - Problem: LLM operations can be memory intensive
   - Solution: Monitor and limit concurrent operations
   - Solution: Implement proper cleanup

3. **Error Handling**
   - Problem: LLM API calls can fail
   - Solution: Implement retries and fallbacks
   - Solution: Log detailed error information

4. **Database Connections**
   - Problem: Long-running tasks can timeout
   - Solution: Use proper connection pooling
   - Solution: Implement connection retry logic

5. **Race Conditions**
   - Problem: Multiple requests for same resource
   - Solution: Use database constraints
   - Solution: Implement proper locking

## Testing

1. **API Endpoint Tests**
```python
async def test_blueprint_status():
    """Test the blueprint status endpoint."""
    # Test data - using existing IDs from the database
    topic_id = "d9909b07-b0f1-4c01-ae7d-8e0c6b7c2f89"
    blueprint_id = "af091360-df1e-45a7-aa46-fc52ce887f46"
    
    try:
        # Step 1: Verify records exist
        records_exist = await verify_records_exist(topic_id, blueprint_id)
        if not records_exist:
            return False
        
        # Step 2: Test the status endpoint
        auth_token = create_test_token()
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
            url = f"/api/topics/{topic_id}/blueprints/{blueprint_id}/status"
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return True
            else:
                return False
                
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return False
```

2. **Test Coverage**
   - Test all API endpoints
   - Test background task execution
   - Verify error handling and status updates
   - Check database operations and transactions
   - Test concurrent requests
   - Test timeout scenarios
   - Test cleanup operations
   - Monitor memory usage and performance

3. **Test Data**
   - Use realistic test data
   - Test with various input sizes
   - Test edge cases
   - Test error scenarios
   - Test timeouts and retries

## Conclusion

When implementing long-running processes with CrewAI and FastAPI:
1. Design your API routes following REST conventions
2. Implement proper async/sync separation
3. Use background tasks for long operations
4. Implement comprehensive error handling
5. Provide detailed status updates
6. Test thoroughly, including edge cases
7. Monitor and log everything important
