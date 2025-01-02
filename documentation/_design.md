= SPEC-1: AI-Powered Assessment and Learning Platform
:sectnums:
:toc:


== Current Implementation Status

The platform currently implements the following core features:

=== Completed Features
1. **Authentication & User Management**
   - Next-Auth integration for user authentication
   - Mock authentication support for development
   - User session management and persistence

2. **Settings Management**
   - User settings page with LLM provider selection
   - Secure storage of API keys (OpenAI/Anthropic)
   - Environment-specific configuration

3. **Database Infrastructure**
   - PostgreSQL database with SQLAlchemy ORM
   - Alembic migrations for schema management
   - User and settings data models

4. **Frontend Architecture**
   - Next.js 14 with App Router
   - Chakra UI for component library and styling
   - TypeScript for type safety
   - Component-based architecture
   - API route handlers for backend communication
   - Dynamic routing for topics (`/topics/[topicId]`) with:
     * Topic details view
     * Loading states with skeletons
     * Error handling

5. **Backend Architecture**
   - FastAPI backend with async support
   - PostgreSQL with asyncpg driver
   - Dependency injection pattern
   - Modular router structure
   - Environment-based configuration

6. **Testing Infrastructure**
   - Playwright for E2E testing
   - Jest for frontend unit tests
   - Pytest for backend testing
   - GitHub Actions CI/CD

=== In Progress Features
1. **Topic Management**
   - Basic CRUD operations for topics
   - Topic list view and detail view

2. **CrewAI Integration**
   - Initial crew setup and configuration
   - Basic agent definitions

=== Planned Features
1. **Assessment Blueprint Management**
2. **Question Generation**
3. **Assessment Session Management**
4. **Results Analysis**


== Background

The primary goal of this platform is to enable self-paced and structured learning of new technologies by leveraging AI-generated assessments. The platform will focus on the principles of Revised Bloom's Taxonomy to ensure that learning objectives and questions are well-categorized by cognitive complexity.

This platform is envisioned as a web application with an AI-powered backend using CrewAI for orchestrating intelligent workflows. It will assist users in refining topics, generating assessment blueprints, and creating questions aligned with enabling and terminal objectives. The platform will also support conducting assessments and analyzing results to identify knowledge gaps.

To future-proof the application, capabilities such as querying an LLM for further insights and dynamically generating follow-up questions to address identified gaps may be added. While initially designed for single-user use, the architecture will allow scaling to multi-user functionality with individualized topics, blueprints, and results.


== Requirements

The platform requirements are categorized using the MoSCoW prioritization framework:

=== Must Have
- Allow users to create and manage 'Topics' representing high-level subjects for assessment.
- Provide functionality to define 'Assessment Blueprints' with:
  * 8-10 Terminal Objectives linked to the topic.
  * 5-8 Enabling Objectives for each Terminal Objective.
- Enable AI-generated multiple-choice 'Questions' that:
  * Are categorized by enabling objectives and cognitive behavior levels.
  * Include explanations for correct answers with external references where applicable.
  * Provide rationales for distractors (incorrect answers) with references if applicable.
- Offer an interactive user interface to:
  * Create and edit Topics and Assessment Blueprints.
  * Generate and manage Questions linked to an Assessment Blueprint.
  * Start an Assessment Session and record responses.
- Implement a backend using CrewAI with specialized agents and workflows for:
  * Topic creation.
  * Assessment Blueprint refinement.
  * Question generation.
  * Assessment session management.
- Maintain a data store for storing topics, blueprints, questions, and assessment results.

=== Should Have
- Support multiple user accounts with isolated data storage for each user.
- Provide the ability to query the LLM during assessments for more information about a topic.
- Allow users to regenerate or extend questions dynamically to address knowledge gaps.

=== Could Have
- Integration with external APIs or knowledge sources to enrich explanations and references.
- Capability to track and analyze user progress across multiple assessments.
- Export options for assessment blueprints and questions (e.g., PDF, CSV).

=== Won't Have (Initial Phase)
- Advanced analytics or dashboards for tracking long-term performance trends.
- Support for collaborative assessments involving multiple users simultaneously.
- Offline functionality or native mobile application support.


== API Design

=== RESTful Endpoints

The platform follows RESTful conventions with proper resource nesting:

1. **Topics**
   ```
   GET    /api/topics                 # List topics
   POST   /api/topics                 # Create topic
   GET    /api/topics/{id}           # Get topic
   PUT    /api/topics/{id}           # Update topic
   DELETE /api/topics/{id}           # Delete topic
   ```

2. **Blueprints**
   ```
   GET    /api/topics/{topicId}/blueprints                    # List blueprints
   POST   /api/topics/{topicId}/blueprints/generate           # Generate blueprint
   GET    /api/topics/{topicId}/blueprints/{id}              # Get blueprint
   GET    /api/topics/{topicId}/blueprints/{id}/status       # Get generation status
   PUT    /api/topics/{topicId}/blueprints/{id}              # Update blueprint
   DELETE /api/topics/{topicId}/blueprints/{id}              # Delete blueprint
   ```

3. **Questions**
   ```
   GET    /api/topics/{topicId}/blueprints/{blueprintId}/questions                    # List questions
   POST   /api/topics/{topicId}/blueprints/{blueprintId}/questions/generate          # Generate questions
   GET    /api/topics/{topicId}/blueprints/{blueprintId}/questions/{id}              # Get question
   GET    /api/topics/{topicId}/blueprints/{blueprintId}/questions/{id}/status       # Get generation status
   PUT    /api/topics/{topicId}/blueprints/{blueprintId}/questions/{id}              # Update question
   DELETE /api/topics/{topicId}/blueprints/{blueprintId}/questions/{id}              # Delete question
   ```

4. **Assessments**
   ```
   GET    /api/topics/{topicId}/assessments                    # List assessments
   POST   /api/topics/{topicId}/assessments                    # Create assessment
   GET    /api/topics/{topicId}/assessments/{id}              # Get assessment
   PUT    /api/topics/{topicId}/assessments/{id}              # Update assessment
   DELETE /api/topics/{topicId}/assessments/{id}              # Delete assessment
   POST   /api/topics/{topicId}/assessments/{id}/submit       # Submit assessment
   ```

=== Response Formats

All API responses follow a consistent format:

1. **Success Response**
   ```json
   {
     "data": {
       // Resource data
     },
     "meta": {
       "timestamp": "2025-01-01T16:30:36-05:00"
     }
   }
   ```

2. **Error Response**
   ```json
   {
     "error": {
       "code": "NOT_FOUND",
       "message": "Resource not found",
       "details": "Topic with id 123 does not exist"
     },
     "meta": {
       "timestamp": "2025-01-01T16:30:36-05:00"
     }
   }
   ```

3. **List Response**
   ```json
   {
     "data": [
       // Array of resources
     ],
     "meta": {
       "total": 100,
       "page": 1,
       "per_page": 20,
       "timestamp": "2025-01-01T16:30:36-05:00"
     }
   }
   ```

4. **Status Response**
   ```json
   {
     "data": {
       "id": "123",
       "status": "generating",
       "progress": {
         "current": 5,
         "total": 10,
         "percentage": 50
       },
       "created_at": "2025-01-01T16:20:36-05:00",
       "updated_at": "2025-01-01T16:30:36-05:00"
     },
     "meta": {
       "timestamp": "2025-01-01T16:30:36-05:00"
     }
   }
   ```

=== Authentication

All API endpoints require authentication:

1. **Bearer Token**
   ```
   Authorization: Bearer <token>
   ```

2. **Error Responses**
   - 401 Unauthorized: Missing or invalid token
   - 403 Forbidden: Valid token but insufficient permissions

=== Rate Limiting

API endpoints are rate limited to prevent abuse:

1. **Default Limits**
   - 100 requests per minute per user
   - 1000 requests per hour per user

2. **Headers**
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 99
   X-RateLimit-Reset: 1704147036
   ```

== Method

=== System Architecture
The platform follows a modular, service-oriented architecture (SOA) powered by CrewAI workflows for intelligent task orchestration.  

[plantuml, architecture-diagram, png]
----
@startuml
package "User Interface" {
  [Web Application]
  [API Gateway]
}

package "CrewAI Backend" {
  [Topic Agent]
  [Blueprint Agent]
  [Question Generator Agent]
  [Assessment Agent]
}

package "Database" {
  [Graph Database] 
  [SQL Database]
}

[Web Application] --> [API Gateway]
[API Gateway] --> [CrewAI Backend]
[Topic Agent] --> [Graph Database]
[Blueprint Agent] --> [Graph Database]
[Question Generator Agent] --> [Graph Database]
[Assessment Agent] --> [SQL Database]
@enduml
----

=== Key Components

1. **User Interface**  
   - A web-based interface using Next.js.  
   - Interacts with the backend through a REST or GraphQL API Gateway.  

2. **CrewAI Backend**  
   - **Topic Agent**:  
     * Guides users through creating and refining a new 'Topic.'  
   - **Blueprint Agent**:  
     * Assists in defining Terminal and Enabling Objectives.  
   - **Question Generator Agent**:  
     * Generates multiple-choice questions categorized by objectives and cognitive levels.  
     * Provides explanations and references for correctness and distractors.  
   - **Assessment Agent**:  
     * Manages assessment sessions, records responses, and evaluates results.  
   - Workflow example: Question generation using CrewAI tools for prompt templates and question validation.  

3. **Database Design**  
   - **Graph Database (Neo4j or ArangoDB)**:  
     * Stores relationships between topics, objectives, and questions.  
   - **SQL Database (PostgreSQL)**:  
     * Tracks user profiles, assessment sessions, and results.  

=== Question Generation Algorithm

The LLM-driven question generator follows these steps:  
1. Parse the Assessment Blueprint to extract enabling objectives and cognitive levels.  
2. Generate questions for each enabling objective using CrewAI workflows.  
3. Validate questions by:  
   - Ensuring alignment with the cognitive level.  
   - Generating explanations for correct answers with external references where applicable.  
   - Fetching references (if available) for deeper learning.  

[plantuml, question-flow, png]
----
@startuml
start
:Parse Assessment Blueprint;
:Select Enabling Objective;
:Determine Cognitive Level;
:Generate Question via LLM;
:Generate Explanations for Options;
:Store Question with Metadata;
repeat while [More Objectives] is true
:Return Questions;
stop
@enduml
----



== Implementation

=== Step 1: Environment Setup
1. **Frontend Setup**  
   - Initialize a Next.js project.  
   - Configure routing and UI components using Material-UI or TailwindCSS.  
   - Implement authentication (e.g., Firebase Authentication or Auth0).  

2. **Backend Setup**  
   - Create a Python backend using FastAPI for API endpoints.  
   - Integrate CrewAI with specialized agents and workflows.  
   - Configure endpoints for topic, blueprint, question management, and assessments.  

3. **Database Setup**  
   - Deploy Neo4j for storing hierarchical relationships between topics, objectives, and questions.  
   - Deploy PostgreSQL for storing user profiles and assessment results.  
   - Connect the databases to the backend through ORM libraries like SQLAlchemy and Neo4j Python driver.  

=== Step 2: Implement CrewAI Workflows
1. **Topic Creation Workflow**  
   - Develop the Topic Agent to refine topic names and descriptions.  

2. **Blueprint Creation Workflow**  
   - Implement the Blueprint Agent to guide users in defining objectives.  

3. **Question Generation Workflow**  
   - Configure the Question Generator Agent to:  
     * Use prompt engineering for LLM-based question creation.  
     * Categorize questions by cognitive behavior levels.  
     * Generate explanations for answers and distractors.  

4. **Assessment Workflow**  
   - Build the Assessment Agent to present questions and record user responses.  
   - Include logic to dynamically generate follow-up questions to address knowledge gaps.  

=== Step 3: Frontend Development
1. Implement screens for:  
   - Topic Management: Create, edit, and delete topics.  
   - Blueprint Management: Define and modify objectives.  
   - Question Management: View, edit, and regenerate questions.  
   - Assessment Session: Display questions and record answers.  

2. Implement API calls to connect the frontend to the backend.  

=== Step 4: Testing and Validation
1. Unit Testing:  
   - Test individual components and workflows using pytest and Jest.  
2. Integration Testing:  
   - Validate end-to-end communication between frontend, backend, and database.  
3. User Testing:  
   - Conduct usability testing to gather feedback and refine workflows.  

=== Step 5: Deployment
1. Deploy the backend to AWS Lambda or a containerized environment using Docker and Kubernetes.  
2. Deploy the frontend to Vercel or Netlify for static hosting.  
3. Configure CI/CD pipelines with GitHub Actions or GitLab CI for automated builds and deployments.  


project-root/
├── frontend/                     # Frontend application (Next.js 14)
│   ├── app/                      # Next.js App Router structure
│   │   ├── api/                  # API route handlers
│   │   ├── assessments/         # Assessment pages
│   │   ├── auth/                # Authentication pages
│   │   ├── blueprints/         # Blueprint pages
│   │   ├── settings/           # Settings pages
│   │   ├── topics/             # Topic pages with dynamic routes
│   │   │   ├── [topicId]/      # Dynamic topic routes
│   │   │   ├── create/         # Topic creation
│   │   │   └── page.tsx        # Topics list page
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── components/              # Reusable UI components
│   │   ├── assessments/        # Assessment-related components
│   │   ├── blueprints/        # Blueprint-related components
│   │   ├── layout/            # Layout components
│   │   ├── providers/         # Context providers
│   │   └── topics/            # Topic-related components
│   ├── lib/                    # Utility functions and configurations
│   ├── providers/              # App-wide providers
│   ├── types/                  # TypeScript type definitions
│   └── tests/                  # E2E and integration tests
├── backend/                      # Backend application (FastAPI)
│   ├── api/                      # API and database layer
│   │   ├── models.py             # SQLAlchemy models (aligned with Pydantic)
│   │   ├── schemas/              # Pydantic schema models
│   │   ├── routers/              # API route handlers
│   │   │   ├── topics.py         # Topic-related API routes
│   │   │   ├── blueprint_generation.py  # Blueprint-related API routes
│   │   │   ├── questions.py      # Question-related API routes
│   │   │   └── assessments.py    # Assessment session routes
│   │   ├── crews/               # CrewAI implementation
│   │   │   ├── blueprint_crew/   # Blueprint generation crew
│   │   │   │   ├── config/      # Crew configuration files
│   │   │   │   └── blueprint_crew.py  # Blueprint crew implementation
│   │   │   ├── question_crew/    # Question generation crew
│   │   │   ├── assessment_crew/  # Assessment generation crew
│   │   │   ├── tools/           # Custom tools for crews
│   │   │   └── reference_documents/  # Reference materials for crews
│   │   └── dependencies.py       # FastAPI dependencies
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # Testing files
│   │   ├── unit/                # Unit tests for each module
│   │   └── integration/         # Integration tests for API
│   ├── setup.py                 # Python package setup
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables for backend
├── database/                    # Database initialization scripts
│   ├── init_postgres.sql       # SQL script for database setup
│   └── migrations/             # Alembic migration files
├── tests/                      # Testing files
│   ├── unit/                   # Unit tests for each module
│   ├── integration/            # Integration tests for API and database
│   ├── testdata/              # Sample test data
│   └── test_config.py         # Test configuration settings
├── docker/                    # Docker configuration
│   ├── Dockerfile.backend     # Dockerfile for backend
│   ├── Dockerfile.frontend    # Dockerfile for frontend
│   └── docker-compose.yml     # Docker Compose setup
├── docs/                     # Documentation
│   ├── design-docs/         # Architecture and design documentation
│   ├── user-manual/         # End-user guide
│   └── api-docs/            # API endpoint documentation
├── .gitignore              # Git ignore file
├── README.md              # Project overview
└── LICENSE               # License file


## Development Environment Setup

### Prerequisites
- Node.js (v18 or later)
- npm (v9 or later)
- Git
- A free Auth0 account
- ngrok (for HTTPS during development)

### Initial Setup

1. **Clone and Install Dependencies**
   ```bash
   git clone [repository-url]
   cd quizmaster-pro
   cd frontend
   npm install
   ```

2. **Install ngrok Globally**
   ```bash
   npm install -g ngrok
   ```

3. **Auth0 Configuration**
   1. Create a new Auth0 application:
      - Go to Auth0 Dashboard
      - Applications > Create Application
      - Select "Regular Web Application"
      - Note down:
        - Domain (OIDC_ISSUER_URL)
        - Client ID
        - Client Secret

   2. Configure Auth0 Application Settings:
      - Application Type: Regular Web Application
      - Token Endpoint Authentication Method: Post
      - Allowed Callback URLs: `https://[your-ngrok-url]/api/auth/callback/oidc`
      - Allowed Logout URLs: `https://[your-ngrok-url]`
      - Application Login URI: `https://[your-ngrok-url]/auth/signin`
      - Allowed Web Origins: `https://[your-ngrok-url]`

4. **Environment Configuration**
   Create a `.env.local` file in the frontend directory:
   ```env
   NEXTAUTH_URL=https://[your-ngrok-url]
   NEXTAUTH_SECRET=[generate-with-openssl-rand-base64-32]
   OIDC_ISSUER_URL=https://[your-auth0-domain]
   OIDC_CLIENT_ID=[your-client-id]
   OIDC_CLIENT_SECRET=[your-client-secret]
   ```

### Starting the Development Environment

1. **Start the Next.js Development Server**
   ```bash
   cd frontend
   npm run dev
   ```
   This will start the development server on port 3000.

2. **Start ngrok HTTPS Tunnel**
   In a new terminal:
   ```bash
   ngrok http 3000
   ```
   Note: Each time you restart ngrok, you'll get a new URL and will need to:
   - Update `.env.local` with the new URL
   - Update Auth0 application settings with the new URL

3. **Generate NEXTAUTH_SECRET (First Time Only)**
   ```bash
   openssl rand -base64 32
   ```
   Add the output to your `.env.local` file as NEXTAUTH_SECRET.

### Development Workflow

1. **Starting the Environment**
   - Start the Next.js server
   - Start ngrok
   - Update URLs if ngrok URL changed
   - Verify Auth0 configuration matches current ngrok URL

2. **Making Changes**
   - Frontend changes will auto-refresh
   - Authentication-related changes require server restart
   - Environment variable changes require server restart

3. **Troubleshooting**
   - Check ngrok tunnel status and URL
   - Verify Auth0 configuration matches current URLs
   - Check `.env.local` configuration
   - Clear browser cookies if auth state is incorrect
   - Check Next.js server logs for errors

### Common Issues and Solutions

1. **Port Already in Use**
   ```bash
   # Find process using port 3000
   netstat -ano | findstr :3000
   # Kill process by PID
   taskkill /PID [PID] /F
   ```

2. **Auth0 Login Issues**
   - Verify all URLs in Auth0 match current ngrok URL
   - Check browser console for CORS errors
   - Verify callback URL is correct
   - Clear browser cookies and try again

3. **Next.js Server Issues**
   - Clear `.next` directory
   ```bash
   rm -rf .next
   npm run dev
   ```

4. **Environment Sync**
   - Keep a checklist of URLs to update when ngrok changes:
     - `.env.local` NEXTAUTH_URL
     - Auth0 Callback URLs
     - Auth0 Logout URLs
     - Auth0 Web Origins
     - Auth0 Application Login URI

### Best Practices

1. **Local Development**
   - Use consistent terminal windows for each service
   - Keep ngrok URL in a notepad for quick updates
   - Use browser incognito mode for testing auth flows

2. **Auth0 Development**
   - Create separate Auth0 applications for development/production
   - Use environment variables for all Auth0 configuration
   - Test with multiple user accounts

3. **Security**
   - Never commit `.env.local` to version control
   - Regularly rotate Auth0 client secrets
   - Use secure NEXTAUTH_SECRET values


## Authentication Setup Guide

### Overview
The platform uses Next-Auth for frontend authentication and JWT tokens for backend authentication. In development mode, it uses a mock authentication provider to simplify testing.

### Frontend Setup

1. **Next-Auth Configuration**
   - Configure Next-Auth in `/app/api/auth/[...nextauth]/route.ts`
   - Set up providers (e.g., OAuth, credentials)
   - Configure JWT token generation
   - Set required environment variables:
     ```
     NEXTAUTH_SECRET=your-secret-key
     NEXTAUTH_URL=http://localhost:3000
     ```

2. **Mock Authentication**
   - Development-only mock provider in `/app/api/auth/[...nextauth]/mock-provider.ts`
   - Provides consistent test user and JWT token
   - Usage in API routes:
     ```typescript
     import { getServerSession } from 'next-auth';
     import { mockAuthConfig } from '@/app/api/auth/[...nextauth]/mock-provider';

     const authConfig = process.env.NODE_ENV === 'development' ? mockAuthConfig : authOptions;
     const session = await getServerSession(authConfig);
     ```

3. **Protected API Routes**
   - Always check for valid session and access token
   - Include Authorization header in backend requests
   - Handle unauthorized responses appropriately
   - Example route handler:
     ```typescript
     export async function GET() {
       const session = await getServerSession(authConfig);
       if (!session?.accessToken) {
         return new NextResponse('Unauthorized', { status: 401 });
       }
       // Make authenticated backend request
     }
     ```

### Backend Setup

1. **JWT Verification**
   - Configure JWT secret in `api/auth.py`
   - Verify tokens using the same secret as frontend
   - Extract user ID and validate permissions
   - Example configuration:
     ```python
     JWT_SECRET = os.getenv("NEXTAUTH_SECRET")
     JWT_ALGORITHM = "HS256"
     ```

2. **FastAPI Dependencies**
   - Use `get_current_user` dependency for protected routes
   - Verify token in Authorization header
   - Return 401 for invalid/missing tokens
   - Example route protection:
     ```python
     @router.get("/protected-route")
     async def protected_endpoint(
         current_user_id: UUID4 = Depends(get_current_user)
     ):
         # Handle authenticated request
     ```

3. **Error Handling**
   - Provide clear error messages for auth failures
   - Log authentication errors appropriately
   - Return consistent error responses
   - Example error handler:
     ```python
     @app.exception_handler(AuthenticationError)
     async def auth_exception_handler(request, exc):
         return JSONResponse(
             status_code=401,
             content={"detail": str(exc)}
         )
     ```

### Security Considerations

1. **Token Management**
   - Use short-lived JWT tokens
   - Implement token refresh mechanism
   - Token expiration management

2. **Route Protection**
   - Server-side route protection
   - Client-side navigation guards
   - Session validation

3. **Error Handling**
   - Authentication error messages
   - Session timeout handling
   - Invalid token management

### User Experience

1. **Authentication Flow**
   - Single Sign-On with Auth0
   - Seamless login experience
   - Automatic redirect after authentication

2. **Session Management**
   - Persistent sessions
   - Secure session storage
   - Automatic session refresh

3. **UI Integration**
   - Dynamic navigation based on auth state
   - Protected content visibility
   - Loading states during authentication

### Future Enhancements

1. **Role-Based Access Control**
   - Integration with Auth0 roles
   - Permission-based component rendering
   - Role-specific features

2. **Multi-Factor Authentication**
   - Support for 2FA
   - Authentication method selection
   - Security preferences

3. **User Profile Management**
   - Profile information editing
   - Password change functionality
   - Account linking options

## Model Alignment Strategy

The platform uses a "single source of truth" approach to maintain consistency between frontend TypeScript types, backend Pydantic models, and SQLAlchemy database models. This strategy ensures type safety and reduces the likelihood of data inconsistencies across the application stack.

=== Core Principles

1. **Pydantic as Source of Truth**
   - All data structures are primarily defined as Pydantic models in `backend/models/schemas.py`
   - Models include comprehensive validation rules, field constraints, and documentation
   - Example models: `Blueprint`, `Topic`, `TerminalObjective`, `EnablingObjective`

2. **SQLAlchemy Model Alignment**
   - Database models in `backend/api/models.py` mirror Pydantic schemas
   - Use SQLAlchemy's ORM features while maintaining structural consistency
   - Implement computed properties to match Pydantic model fields
   Example:
   ```python
   class Blueprint(Base):
       # Core fields match Pydantic model
       id = Column(UUID(as_uuid=True), primary_key=True)
       title = Column(String(255), nullable=False)
       
       # Computed properties for derived fields
       @property
       def terminal_objectives_count(self) -> int:
           return len([obj for obj in self.objectives if obj.type == "terminal"])
   ```

3. **Automated TypeScript Type Generation**
   - Use `datamodel-code-generator` to generate TypeScript types
   - Types are automatically generated from Pydantic models
   - Generated types include:
     * All field constraints and validations
     * Proper nullable handling
     * Documentation strings
     * Enum literals
   - Types are stored in `frontend/types/schemas.ts`

=== Workflow for Schema Changes

When making changes to data structures:

1. Update the Pydantic model in `backend/models/schemas.py`
2. Modify the corresponding SQLAlchemy model in `backend/api/models.py`
3. Generate new TypeScript types:
   ```bash
   python backend/scripts/generate_types.py
   ```
4. Update frontend components to handle any breaking changes
5. Create and run database migrations if needed

=== Benefits

- **Type Safety**: End-to-end type checking from database to frontend
- **Consistency**: Single source of truth prevents model drift
- **Documentation**: Models are self-documenting through Pydantic schemas
- **Validation**: Consistent validation rules across all layers
- **Maintainability**: Changes are propagated automatically to TypeScript
- **Developer Experience**: IDE support and autocomplete throughout the stack

## Frontend Implementation

### Technology Stack
- **Framework**: Next.js 14 with TypeScript
- **Styling**: TailwindCSS for responsive design
- **State Management**: React Hooks (useState, useRouter)
- **Form Handling**: Native React form handling with validation

### Component Structure

#### Layout Components
- `Navbar`: Global navigation component with links to Topics, Blueprints, and Assessments
- `RootLayout`: Base layout with common styling and Navbar integration

#### Pages

1. **Home Page** (`/app/page.tsx`)
   - Welcome section with platform introduction
   - Grid layout showcasing three main features:
     - Topics management
     - Assessment Blueprints
     - Assessments
   - Quick access button to create new topics

2. **Topics Section**
   - **Topics List** (`/app/topics/page.tsx`)
     - Grid display of topics with title and description
     - Links to create blueprints and view details
     - Create New Topic button
   - **Create Topic** (`/app/topics/create/page.tsx`)
     - Form with validation for title and description
     - Responsive layout with cancel/submit actions

3. **Blueprints Section**
   - **Blueprints List** (`/app/blueprints/page.tsx`)
     - List of assessment blueprints with metadata
     - Shows number of terminal and enabling objectives
     - Options to generate assessments or view details
   - **Create Blueprint** (`/app/blueprints/create/page.tsx`)
     - Complex form supporting:
       - Multiple terminal objectives (up to 10)
       - Multiple enabling objectives per terminal objective (up to 8)
       - Cognitive level selection based on Bloom's Taxonomy
       - Dynamic form fields with add/remove functionality

4. **Assessments Section**
   - **Assessments List** (`/app/assessments/page.tsx`)
     - Display of available and completed assessments
     - Score visualization for completed assessments
     - Progress tracking with completion dates
     - Quick access to start or review assessments

### UI Features

1. **Responsive Design**
   - Mobile-first approach using Tailwind's responsive classes
   - Flexible grid layouts that adapt to screen size
   - Consistent spacing and typography

2. **Interactive Elements**
   - Hover effects on buttons and links
   - Form validation feedback
   - Loading states (to be implemented)
   - Error handling (to be implemented)

3. **Visual Hierarchy**
   - Clear headings and subheadings
   - Card-based layouts for content organization
   - Consistent color scheme using Tailwind's default palette
   - Visual feedback for interactive elements

4. **Navigation**
   - Breadcrumb navigation (to be implemented)
   - Back buttons for multi-step forms
   - Clear call-to-action buttons

### Planned Enhancements

1. **Assessment Interface**
   - Question display with multiple choice options
   - Progress indicator
   - Timer functionality
   - Save and resume capability

2. **User Experience**
   - Loading states for async operations
   - Error boundaries and error messages
   - Success notifications
   - Confirmation dialogs for destructive actions

3. **API Integration**
   - API client setup
   - Request/response handling
   - Error handling
   - Loading states

4. **Authentication**
   - Login/signup forms
   - Protected routes
   - User profile management

## Authentication Implementation

### Technology Stack
- **Authentication Framework**: NextAuth.js
- **Identity Provider**: Auth0 (OpenID Connect)
- **Session Strategy**: JWT with secure token handling
- **Protected Routes**: Next.js Middleware

### Authentication Components

1. **Session Provider** (`/components/providers/SessionProvider.tsx`)
   - Client-side wrapper for NextAuth SessionProvider
   - Handles authentication state management
   - Provides session context to child components

2. **Authentication Configuration** (`/app/api/auth/[...nextauth]/route.ts`)
   - OIDC configuration with Auth0
   - JWT token handling and refresh
   - Session callbacks for user profile management
   - Custom error handling

3. **Protected Routes** (`/middleware.ts`)
   - Route protection middleware
   - Secures specific paths:
     - `/topics/*`
     - `/blueprints/*`
     - `/assessments/*`
   - Automatic redirection to login for unauthenticated users

4. **Authentication Pages**
   - **Sign In** (`/app/auth/signin/page.tsx`)
     - Custom sign-in page
     - SSO integration with Auth0
     - Responsive design
   - **Error Page** (`/app/auth/error/page.tsx`)
     - Handles authentication errors
     - User-friendly error messages
     - Retry functionality

### Environment Configuration
```env
NEXTAUTH_URL=https://your-domain
NEXTAUTH_SECRET=[secure-random-string]
OIDC_ISSUER_URL=https://your-auth0-domain
OIDC_CLIENT_ID=[auth0-client-id]
OIDC_CLIENT_SECRET=[auth0-client-secret]
```

### Auth0 Configuration
1. **Application Settings**
   - Application Type: Regular Web Application
   - Token Endpoint Authentication Method: Post
   - ID Token Expiration: 36000 seconds

2. **Application URIs**
   - Application Login URI: `/auth/signin`
   - Allowed Callback URLs: `/api/auth/callback/oidc`
   - Allowed Logout URLs: Root URL
   - Allowed Web Origins: Root URL

3. **Token Configuration**
   - ID Token: Enabled
   - Access Token: Enabled
   - Refresh Token: Optional (based on requirements)

### Security Features

1. **Token Handling**
   - Use short-lived JWT tokens
   - Implement token refresh mechanism
   - Token expiration management

2. **Route Protection**
   - Server-side route protection
   - Client-side navigation guards
   - Session validation

3. **Error Handling**
   - Authentication error messages
   - Session timeout handling
   - Invalid token management

### User Experience

1. **Authentication Flow**
   - Single Sign-On with Auth0
   - Seamless login experience
   - Automatic redirect after authentication

2. **Session Management**
   - Persistent sessions
   - Secure session storage
   - Automatic session refresh

3. **UI Integration**
   - Dynamic navigation based on auth state
   - Protected content visibility
   - Loading states during authentication

### Future Enhancements

1. **Role-Based Access Control**
   - Integration with Auth0 roles
   - Permission-based component rendering
   - Role-specific features

2. **Multi-Factor Authentication**
   - Support for 2FA
   - Authentication method selection
   - Security preferences

3. **User Profile Management**
   - Profile information editing
   - Password change functionality
   - Account linking options

## Development Authentication Modes

The application supports two authentication modes:

1. **Production Mode**
   - Uses Auth0 OIDC authentication
   - Requires ngrok for HTTPS
   - Full SSO functionality
   - Real user profiles and tokens

2. **Development Mode**
   - Uses mock authentication provider
   - Works without Auth0 or ngrok
   - Auto-signs in as development user
   - No external dependencies

#### Switching Between Modes

1. **Development Mode Setup**
   ```env
   # .env.local.development
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=any-secret-value-for-development
   MOCK_AUTH=true
   NEXT_PUBLIC_MOCK_AUTH=true
   ```

2. **Production Mode Setup**
   ```env
   # .env.local.production
   NEXTAUTH_URL=https://[your-ngrok-url]
   NEXTAUTH_SECRET=[your-secret]
   OIDC_ISSUER_URL=https://[your-auth0-domain]
   OIDC_CLIENT_ID=[your-client-id]
   OIDC_CLIENT_SECRET=[your-client-secret]
   MOCK_AUTH=false
   NEXT_PUBLIC_MOCK_AUTH=false
   ```

3. **Switching Between Modes**
   ```bash
   # Switch to development mode
   copy .env.local.development .env.local
   npm run dev

   # Switch to production mode
   copy .env.local.production .env.local
   npm run dev
   ```

#### Mock Authentication Features
- Pre-configured user profile (jkay65@gmail.com)
- Automatic authentication
- No external service dependencies
- Consistent development experience
- Fast development iteration

#### When to Use Each Mode
- **Development Mode**: 
  - Local development
  - UI/UX development
  - Feature development
  - Unit testing
  
- **Production Mode**:
  - Testing Auth0 integration
  - Testing SSO flows
  - Integration testing
  - Pre-deployment verification

### Security Considerations

1. **Token Management**
   - Use short-lived JWT tokens
   - Implement token refresh mechanism
   - Token expiration management

2. **Route Protection**
   - Server-side route protection
   - Client-side navigation guards
   - Session validation

3. **Error Handling**
   - Authentication error messages
   - Session timeout handling
   - Invalid token management

### User Experience

1. **Authentication Flow**
   - Single Sign-On with Auth0
   - Seamless login experience
   - Automatic redirect after authentication

2. **Session Management**
   - Persistent sessions
   - Secure session storage
   - Automatic session refresh

3. **UI Integration**
   - Dynamic navigation based on auth state
   - Protected content visibility
   - Loading states during authentication

### Future Enhancements

1. **Role-Based Access Control**
   - Integration with Auth0 roles
   - Permission-based component rendering
   - Role-specific features

2. **Multi-Factor Authentication**
   - Support for 2FA
   - Authentication method selection
   - Security preferences

3. **User Profile Management**
   - Profile information editing
   - Password change functionality
   - Account linking options
