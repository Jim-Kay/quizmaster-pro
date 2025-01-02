# QuizMaster Pro

An AI-powered assessment and learning platform that leverages CrewAI for intelligent workflows.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
- Copy `.env.example` to `.env`
- Fill in required configuration values

4. Start the backend server:
```bash
uvicorn backend.main:app --reload
```

## Project Structure

- `/backend` - FastAPI backend with CrewAI integration
- `/frontend` - Next.js frontend application (to be implemented)
- `/database` - Database models and migrations
