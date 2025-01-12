# QuizMaster Pro Docker Setup

## Overview
QuizMaster Pro uses Docker to run the backend FastAPI service, providing better process isolation and consistent environments across different machines. The frontend continues to run directly on the host machine.

## Architecture

### Backend (Docker Container)
- FastAPI application running in a Python 3.11 container
- Code mounted as a volume for hot reloading
- Environment variables passed from host to container
- Port 8000 exposed for API access
- Connects to PostgreSQL on host machine via `host.docker.internal`

### Hot Reloading
The backend code is mounted as a volume, which means:
- Code changes are reflected immediately
- No rebuild needed for Python code changes
- Uvicorn automatically reloads when files change

### When to Rebuild
The Docker image only needs to be rebuilt when:
1. `requirements.txt` changes (new dependencies)
2. `Dockerfile` changes (system-level changes)
3. Docker cache is causing issues

For all other changes (Python code, configuration, etc.), the hot reloading system will automatically detect and apply changes.

## Docker Configuration

### Dockerfile
Located at `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload"]
```

## Process Manager

The PowerShell-based process manager (`scripts/manage_processes.ps1`) handles:

1. Docker container lifecycle:
   - Starting/stopping containers
   - Managing environment variables
   - Viewing container logs
   - Rebuilding image when dependencies change

2. Container naming:
   - Container name: `quizmaster-backend`
   - Image name: `quizmaster-backend:latest`

3. Environment handling:
   - Development
   - Test
   - Production

## Usage

### Starting the Backend
1. Open the process manager: `.\scripts\manage_processes.ps1`
2. Select the desired environment (Development/Test/Production)
3. Click "Start Backend"
   - This will use existing image if available
   - Mount the backend code for hot reloading
   - Start container with selected environment

### Making Code Changes
1. Edit any Python files in the backend directory
2. Changes will be detected automatically
3. Uvicorn will reload the application
4. No rebuild needed!

### When to Rebuild
Click "Rebuild Image" only when:
1. You've added new dependencies to requirements.txt
2. You've modified the Dockerfile
3. You're experiencing Docker-related issues

### Viewing Logs
1. Click "View Logs" in the process manager
2. A new PowerShell window will open showing container logs
3. Logs will update in real-time

### Stopping the Backend
1. Click "Stop Backend" in the process manager
   - This will stop and remove the Docker container
   - Port 8000 will be freed automatically

## Troubleshooting

### Port 8000 Already In Use
The Docker container requires port 8000. If the port is in use:
1. The process manager will automatically stop and remove any existing container
2. You may need to manually stop other processes using port 8000:
   ```powershell
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

### Database Connection Issues
If the backend can't connect to PostgreSQL:
1. Ensure PostgreSQL is running on the host machine
2. Check that the database credentials are correct
3. Verify that `host.docker.internal` resolves correctly

### Hot Reloading Not Working
If code changes aren't reflected:
1. Check the logs for any Python errors
2. Ensure the backend code is properly mounted:
   ```powershell
   docker inspect quizmaster-backend
   ```
3. Look for the Volumes section to verify the mount
4. Try stopping and starting the container

## Benefits of Docker Setup

1. **Development Experience**
   - Hot reloading through volume mounting
   - No rebuilds needed for code changes
   - Easy environment switching

2. **Process Isolation**
   - Backend runs in its own container
   - No interference with other Python processes
   - Clean process termination

3. **Environment Consistency**
   - Same environment across all machines
   - Dependencies managed in container
   - No conflicts with host Python installation

4. **Resource Management**
   - Automatic port cleanup
   - No stray processes
   - Easy to monitor resource usage

## Future Improvements

1. **Multi-Container Setup**
   - Add PostgreSQL container
   - Use Docker Compose for service orchestration
   - Add Redis for caching

2. **Environment Enhancements**
   - Environment-specific Docker Compose files
   - Automated database migrations
   - Development/production parity
