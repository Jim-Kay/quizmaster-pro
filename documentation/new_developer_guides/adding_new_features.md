# Adding New Features to QuizMaster Pro

This guide walks you through the process of adding a new feature to QuizMaster Pro, from database to frontend. We'll use the existing "Topics" and "Blueprints" implementations as reference examples.

## 1. Database Setup

### 1.1 Create a New Model
First, add your model to `backend/api/models.py`:

```python
class YourModel(Base):
    __tablename__ = "your_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Add relationships if needed
    user = relationship("User", back_populates="your_models")
```

### 1.2 Create Database Migration
Use Alembic to create and apply the migration:

```bash
cd backend
alembic revision --autogenerate -m "Add your_models table"
alembic upgrade head
```

## 2. Backend API Setup

### 2.1 Create Pydantic Schemas
Add your schemas in `backend/api/routers/schemas.py`:

```python
class YourModelBase(BaseModel):
    title: str
    description: str | None = None

class YourModelCreate(YourModelBase):
    pass

class YourModelResponse(YourModelBase):
    id: UUID4
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### 2.2 URL Structure
Follow these URL structure patterns:

1. Standalone Resources (e.g., Topics):
   - GET /api/topics - List all topics
   - GET /api/topics/{topicId} - Get a specific topic
   - POST /api/topics - Create a new topic
   - PUT /api/topics/{topicId} - Update a topic
   - DELETE /api/topics/{topicId} - Delete a topic

2. Nested Resources (e.g., Blueprints under Topics):
   - GET /api/topics/{topicId}/blueprints - List blueprints for a topic
   - GET /api/topics/{topicId}/blueprints/{blueprintId} - Get a specific blueprint
   - POST /api/topics/{topicId}/blueprints - Create a blueprint
   - PUT /api/topics/{topicId}/blueprints/{blueprintId} - Update a blueprint
   - DELETE /api/topics/{topicId}/blueprints/{blueprintId} - Delete a blueprint
   - GET /api/topics/{topicId}/blueprints/count - Get count of blueprints
   - POST /api/topics/{topicId}/blueprints/generate - Generate blueprints

### 2.3 Create API Router
Create `backend/api/routers/your_models.py`:

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import UUID4

from ..dependencies import get_current_user, get_db
from ..models import YourModel
from . import schemas

router = APIRouter(
    tags=["your_models"]
)

# For standalone resources (e.g., topics)
@router.get("/", response_model=List[schemas.YourModelResponse])
async def get_your_models(
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(YourModel).where(YourModel.created_by == current_user_id)
    result = await db.execute(query)
    return result.scalars().all()

# For nested resources (e.g., blueprints under topics)
@router.get("/{parent_id}/your-models", response_model=List[schemas.YourModelResponse])
async def get_your_models(
    parent_id: UUID4,
    current_user_id: UUID4 = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(YourModel).where(
        YourModel.parent_id == parent_id,
        YourModel.created_by == current_user_id
    )
    result = await db.execute(query)
    return result.scalars().all()
```

### 2.4 Register Router
Add your router in `backend/api/main.py`. The prefix should match your URL structure:

```python
# For standalone resources
app.include_router(your_models.router, prefix="/api/your-models")

# For nested resources
app.include_router(your_models.router, prefix="/api/parent-models/{parent_id}/your-models")
```

## 3. Frontend Setup

### 3.1 Create API Client
Add your API client in `frontend/api/your-models.ts`:

```typescript
import { UUID } from './types';

export interface YourModel {
  id: UUID;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export class YourModelsApi {
  // For standalone resources
  static async getYourModels(): Promise<YourModel[]> {
    const response = await fetch('/api/your-models');
    if (!response.ok) throw new Error('Failed to fetch');
    return response.json();
  }

  // For nested resources
  static async getYourModels(parentId: UUID): Promise<YourModel[]> {
    const response = await fetch(`/api/parent-models/${parentId}/your-models`);
    if (!response.ok) throw new Error('Failed to fetch');
    return response.json();
  }
}
```

### 3.2 Create Next.js API Routes
Follow this directory structure for your API routes:

```
frontend/app/api/
├── your-models/
│   ├── route.ts                    # For standalone resources
│   └── [modelId]/
│       └── route.ts
└── parent-models/
    └── [parentId]/
        └── your-models/
            ├── route.ts            # For nested resources
            ├── count/
            │   └── route.ts
            └── [modelId]/
                └── route.ts
```

Example route file for nested resources:

```typescript
import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';

export async function GET(
  request: Request,
  { params }: { params: { parentId: string; modelId: string } }
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.accessToken) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const response = await fetch(
      `${process.env.BACKEND_URL}/api/parent-models/${params.parentId}/your-models/${params.modelId}`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch model' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### 3.3 Create React Components
Create your components in `frontend/components/your-models/`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { YourModel, yourModelsApi } from '@/api/your-models';

export function YourModelsList() {
  const { data: models, isLoading } = useQuery<YourModel[]>({
    queryKey: ['your-models'],
    queryFn: () => yourModelsApi.getYourModels(),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <ul>
      {models?.map(model => (
        <li key={model.id}>
          <h3>{model.title}</h3>
          <p>{model.description}</p>
        </li>
      ))}
    </ul>
  );
}
```

### 3.4 Create Pages
Add your pages in `frontend/app/your-models/`:

```typescript
'use client';

import { YourModelsList } from '@/components/your-models/YourModelsList';

export default function YourModelsPage() {
  return (
    <div>
      <h1>Your Models</h1>
      <YourModelsList />
    </div>
  );
}
```

## 4. Best Practices

1. **URL Structure**:
   - Use kebab-case for URL paths
   - Use plural nouns for resource collections
   - Place IDs in path parameters, not query parameters
   - Use consistent parameter names (e.g., `topicId`, `blueprintId`)

2. **Error Handling**:
   - Always return appropriate HTTP status codes
   - Include meaningful error messages
   - Log errors on both frontend and backend

3. **Authentication**:
   - Always check user authentication in API routes
   - Use `getServerSession` in Next.js API routes
   - Pass authentication tokens to backend APIs

4. **TypeScript**:
   - Define interfaces for all data structures
   - Use proper type annotations
   - Avoid using `any` type

5. **API Design**:
   - Follow RESTful conventions
   - Use appropriate HTTP methods
   - Keep endpoints focused and single-purpose
   - Use consistent response formats
