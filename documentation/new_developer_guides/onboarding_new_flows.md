# Onboarding New Flows with the Flow Wrapper

This guide explains how to add new CrewAI flows to the QuizMasterPro platform using our flow wrapper implementation.

## Overview

The flow wrapper provides a standardized way to:
1. Execute CrewAI flows asynchronously
2. Monitor flow execution status
3. Handle flow state and errors
4. Stream execution logs in real-time
5. Cache flow results for improved performance
6. Expose flows through REST endpoints

## Implementation Steps

### 1. Create Your Flow Class

Create a new directory under `backend/api/flows/` for your flow:

```python
# backend/api/flows/your_flow/src/your_flow/main.py

from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start

class YourFlowState(BaseModel):
    # Define your flow's state
    input_data: str = ""
    result: str = ""

class YourFlow(Flow[YourFlowState]):
    @start()
    def initialize(self):
        """First step in the flow."""
        print(f"Starting flow with input: {self.state.input_data}")
        # Print statements will be captured in the log file
        
    @listen(initialize)
    def process_data(self):
        """Process the data using CrewAI."""
        # Initialize and run your crew
        # The crew's output will be automatically logged
        result = (
            YourCrew()
            .crew()
            .kickoff(inputs={"data": self.state.input_data})
        )
        self.state.result = result.raw
        
    @listen(process_data)
    def finalize(self):
        """Final step in the flow."""
        print(f"Flow completed with result: {self.state.result}")
```

### 2. Register Your Flow

Add your flow to `backend/api/main.py`:

```python
from api.flows.your_flow.src.your_flow.main import YourFlow

# Initialize and register flows with optional caching
flow_wrapper = FlowWrapper(enable_caching=True)  # Set to False to disable caching globally
flow_wrapper.register_flow("your_flow_name", YourFlow)
```

### 3. Execute and Monitor Your Flow

The flow wrapper provides several endpoints for execution and monitoring:

1. Create a new execution:
```http
POST /api/flows/executions
{
    "flow_name": "your_flow_name",
    "initial_state": {
        "input_data": "your input here"
    },
    "use_cache": true  # Optional: control caching per execution
}
```

2. Start the execution:
```http
POST /api/flows/executions/{execution_id}/start
```

3. Monitor status:
```http
GET /api/flows/executions/{execution_id}
```

4. Stream logs in real-time:
```http
GET /api/flows/executions/{execution_id}/logs
```

## Flow Execution Lifecycle

1. **Creation (PENDING)**
   - Flow execution is created with initial state
   - Status is set to PENDING
   - Execution ID is generated
   - Cache key is generated (if caching enabled)
   - Log file is prepared

2. **Cache Check (if enabled)**
   - If caching is enabled (both globally and per-execution)
   - Check for existing results with matching cache key
   - If found, return cached results immediately
   - If not found, proceed to execution

3. **Execution (RUNNING)**
   - Flow is started in a background task
   - Status is updated to RUNNING
   - State updates are tracked
   - Logs are written to file

4. **Completion (COMPLETED/FAILED)**
   - Flow finishes execution
   - Final state is saved
   - Results are cached (if caching enabled)
   - Status is set to COMPLETED or FAILED
   - Log file is complete but remains accessible

## Caching Configuration

### Global Caching

Control caching at the FlowWrapper level:

```python
# Enable caching for all flows (default)
flow_wrapper = FlowWrapper(enable_caching=True)

# Disable caching for all flows
flow_wrapper = FlowWrapper(enable_caching=False)
```

### Per-Execution Caching

Control caching for individual flow executions:

```python
# Using the REST API
POST /api/flows/executions
{
    "flow_name": "your_flow_name",
    "initial_state": { ... },
    "use_cache": false  # Disable caching for this execution
}

# Using the FlowTester
result = await tester.execute_flow(
    flow_name="your_flow_name",
    initial_state={ ... },
    use_cache=False  # Disable caching for this execution
)
```

### Cache Storage

- Cache files are stored in `cache/flows/`
- Each cache entry is identified by a hash of:
  * Flow name
  * Initial state (sorted for consistency)
- Cache files store:
  * Raw flow output
  * Final state
  * Execution timestamp
  * Error information (if any)

## Logging and Monitoring

### Log File Structure

Each flow execution gets its own log file:
- Location: `logs/flow_{execution_id}.log`
- Contains:
  * Flow execution steps
  * CrewAI crew output
  * Print statements from your flow
  * Error messages if any
  * Cache hit/miss information

### Accessing Logs

1. **Through REST API**
```python
import requests

def stream_logs(execution_id):
    response = requests.get(
        f"/api/flows/executions/{execution_id}/logs",
        stream=True
    )
    for chunk in response.iter_content(chunk_size=None):
        print(chunk.decode())
```

2. **Browser JavaScript**
```javascript
async function streamLogs(executionId) {
    const response = await fetch(
        `/api/flows/executions/${executionId}/logs`
    );
    const reader = response.body.getReader();
    
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        console.log(new TextDecoder().decode(value));
    }
}
```

3. **Node.js**
```javascript
async function streamLogs(executionId) {
    const response = await fetch(
        `/api/flows/executions/${executionId}/logs`
    );
    for await (const chunk of response.body) {
        console.log(chunk.toString());
    }
}
```

### Log Content Best Practices

1. **Structured Logging**
   ```python
   # In your flow
   @start()
   def initialize(self):
       print(f"[STEP] Initialize - Input: {self.state.input_data}")
       
   @listen(initialize)
   def process_data(self):
       print("[START] Processing data")
       result = self.complex_operation()
       print(f"[COMPLETE] Processing - Result: {result}")
   ```

2. **Error Logging**
   ```python
   @listen(initialize)
   def process_data(self):
       try:
           result = self.complex_operation()
           print(f"[SUCCESS] Operation complete: {result}")
       except Exception as e:
           print(f"[ERROR] Operation failed: {str(e)}")
           raise
   ```

3. **Progress Updates**
   ```python
   @listen(initialize)
   def long_running_task(self):
       print("[START] Beginning long task")
       for i in range(total_steps):
           result = self.process_step(i)
           print(f"[PROGRESS] Step {i}/{total_steps}: {result}")
       print("[COMPLETE] Long task finished")
   ```

## Testing Your Flow

The `FlowTester` utility helps test your flows:

```python
from api.tests.utils.flow_tester import FlowTester

async def test_your_flow():
    tester = FlowTester()
    
    # Test without cache
    result = await tester.execute_flow(
        flow_name="your_flow",
        initial_state={"input_data": "test input"},
        use_cache=False  # Force fresh execution
    )
    
    # Test with cache
    cached_result = await tester.execute_flow(
        flow_name="your_flow",
        initial_state={"input_data": "test input"},
        use_cache=True  # Use cached results if available
    )
```

## Best Practices

1. **Cache Invalidation**
   - Consider when cached results might become stale
   - Use cache selectively for deterministic operations
   - Disable cache for operations that need fresh data

2. **State Management**
   - Keep state minimal and well-defined
   - Use Pydantic models for validation
   - Consider what needs to be cached

3. **Error Handling**
   - Log errors comprehensively
   - Cache error states for debugging
   - Provide clear error messages

4. **Testing**
   - Test both with and without cache
   - Verify cache hit/miss behavior
   - Check error handling and recovery

By following these guidelines, your flow will be:
- Well-structured and maintainable
- Properly integrated with the platform
- Efficiently cached when appropriate
- Monitored and debuggable
- Secure and reliable
