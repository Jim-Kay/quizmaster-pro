# Important Rules to Remember

## Authentication and ID Types
- Authentication requires user_id to be in UUID4 format, but stored as string in the database
- All pages need authentication - see _design.md for more info
- When working with IDs in the codebase:
  ```python
  # Database and API:
  id: str  # Store IDs as strings in models and API routes
  user_id: str  # Store user_id as string, but ensure it's in UUID4 format
  
  # Generating IDs:
  from uuid import uuid4
  id = uuid4()  # Generates a UUID4 formatted string
  
  # Validation:
  from pydantic import UUID4  # Only use UUID4 for validation in auth
  user_id: UUID4  # Use UUID4 type for auth validation only
  ```

## Security
- All pages need authentication - see _design.md for more info
- Never hardcode sensitive information like API keys or secrets