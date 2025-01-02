# QuizMasterPro Setup Guide

This guide will help you set up the QuizMasterPro development environment on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.9 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Git

## Initial Setup

### 1. Clone the Repository

```bash
git clone [your-repository-url]
cd QuizMasterPro
```

### 2. Backend Setup

#### 2.1 Python Environment
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2.2 Database Setup
```bash
# Create a new PostgreSQL database
createdb quizmaster
createdb quizmaster_test  # For running tests
```

#### 2.3 Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and set the following variables:
```env
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=quizmaster
```

### 3. Frontend Setup

#### 3.1 Install Node.js Dependencies
```bash
cd frontend
npm install
```

#### 3.2 Frontend Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env.local
```

2. Edit `.env.local` and set:
```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=[generate-with-openssl-rand-base64-32]
```

## Running the Application

### 1. Start the Backend
```bash
# From the root directory, with virtual environment activated
cd backend
uvicorn main:app --reload
```
The backend API will be available at `http://localhost:8000`

### 2. Start the Frontend
```bash
# From the frontend directory
npm run dev
```
The frontend will be available at `http://localhost:3000`

## Running Tests

### Backend Tests
```bash
# From the backend directory
pytest
```

### Frontend Tests
```bash
# From the frontend directory
npm test
```

### E2E Tests
```bash
# From the frontend directory
npm run test:e2e
```

## Development Tools

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

### Mock Data
```bash
# Add mock user for development
python backend/db/add_mock_user.py
```

## Common Issues and Solutions

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check if the database exists and is accessible

### Authentication Issues
- Ensure `NEXTAUTH_SECRET` is properly set
- Check if the database contains the required auth tables
- Verify that cookies are enabled in your browser

### Development Server Issues
- Clear the `.next` cache directory if experiencing frontend issues
- Restart the development servers
- Check for port conflicts (8000 for backend, 3000 for frontend)

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Playwright Testing](https://playwright.dev/)

## Getting Help

If you encounter any issues not covered in this guide:
1. Check the existing GitHub issues
2. Review the error logs in the `logs/` directory
3. Create a new issue with detailed reproduction steps

## Contributing

Please refer to our [Contributing Guidelines](./contributing.md) for information about making contributions to the project.
