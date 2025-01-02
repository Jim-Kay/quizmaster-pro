# SQLAlchemy Blueprint Generation Issue

## Problem Description

We're encountering an issue with blueprint generation getting "stuck" in the generating state. This happens because we don't have a proper way to track when the generation process started, making it difficult to identify and handle stalled or failed generation attempts.

## Current Implementation

The `Blueprint` model has a `status` field that can be:
- "draft"
- "generating" 
- "completed"
- "error"

However, just tracking the status isn't enough because we can't tell how long a blueprint has been in the "generating" state.

## Proposed Solution

Add a `generation_started_at` timestamp column to the `Blueprint` model to track when generation begins. This allows us to:

1. Identify stalled generations (e.g., if started more than 10 minutes ago)
2. Handle concurrent generation requests properly
3. Provide better error messages to users

### Model Changes

```python
class Blueprint(Base):
    # ... existing fields ...
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
```

### Logic Changes

1. When starting generation:
   ```python
   blueprint.status = "generating"
   blueprint.generation_started_at = datetime.now(timezone.utc)
   ```

2. When checking existing generations:
   ```python
   if existing_blueprint.generation_started_at:
       time_elapsed = datetime.now(timezone.utc) - existing_blueprint.generation_started_at
       if time_elapsed.total_seconds() > 600:  # 10 minutes
           existing_blueprint.status = "error"
           existing_blueprint.description = "Blueprint generation timed out after 10 minutes"
   ```

## Implementation Attempts

### 1. Alembic Migration Attempt

Tried to create an Alembic migration but encountered dependency issues:
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

This appears to be caused by a conflict between Pydantic versions used by different dependencies (CrewAI, LangChain, etc.).

### 2. Direct SQL Attempt

Tried to add the column using psql but encountered environment setup issues:
```
error executing cascade step: CORTEX_STEP_TYPE_RUN_COMMAND: failed to run command psql -U postgres -d quizmaster: exec: "psql": executable file not found in %PATH%
```

### 3. SQLAlchemy Direct Approach

Created a function to add the column using SQLAlchemy's async engine:
```python
async def add_generation_started_at_column():
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='blueprints' AND column_name='generation_started_at'"
        ))
        if not result.scalar():
            await conn.execute(text(
                "ALTER TABLE blueprints "
                "ADD COLUMN generation_started_at TIMESTAMP WITH TIME ZONE"
            ))
```

However, running this also encounters dependency issues when trying to import from the main application.

## Next Steps

1. **Dependency Resolution**: 
   - Consider pinning specific versions of Pydantic and other dependencies
   - Or create an isolated script that only imports SQLAlchemy

2. **Alternative Approaches**:
   - Use a separate migration tool like `yoyo-migrations`
   - Connect directly to PostgreSQL using psycopg2
   - Create a standalone script that doesn't import from the main application

3. **Temporary Workaround**:
   - Add better error handling in the generation process
   - Implement timeouts in the background tasks
   - Add cleanup jobs to reset stalled generations
