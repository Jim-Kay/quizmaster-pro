# QuizMaster Pro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered assessment and learning platform that leverages CrewAI for intelligent workflows. QuizMaster Pro provides a comprehensive solution for creating, managing, and analyzing educational assessments through AI-driven automation.

## Features

- **AI-Powered Assessment Generation**: Automatically generate quizzes and tests using CrewAI workflows
- **Customizable Blueprints**: Create reusable assessment templates with configurable parameters
- **Real-time Analytics**: Track learner progress and assessment effectiveness
- **API Integration**: RESTful API for seamless integration with other systems
- **Scalable Architecture**: Built with FastAPI and PostgreSQL for high performance
- **Modern Frontend**: Next.js-based user interface (in development)

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- PostgreSQL 14+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/quizmaster-pro.git
cd quizmaster-pro
```

2. Set up the backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
python backend/db/init_db.py
```

5. Start the development server:
```bash
uvicorn backend.main:app --reload
```

## API Documentation

The QuizMaster Pro API provides endpoints for managing assessments, blueprints, and user data. The API follows RESTful principles and uses JSON for data exchange.

Key API Endpoints:
- `GET /api/blueprints` - List available assessment blueprints
- `POST /api/blueprints` - Create new assessment blueprint
- `GET /api/assessments` - List generated assessments
- `POST /api/assessments` - Generate new assessment

Interactive API documentation is available at `http://localhost:8000/docs` when the server is running.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code follows our coding standards and includes appropriate tests.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Project Maintainer: [Your Name] - your.email@example.com

Project Link: [https://github.com/your-org/quizmaster-pro](https://github.com/your-org/quizmaster-pro)

## Project Structure

The project is organized into the following main components:

- `/backend` - FastAPI backend with CrewAI integration
  - `/api` - API endpoints and routers
  - `/db` - Database models and migrations
  - `/models` - Data models and schemas
  - `/tests` - Unit and integration tests

- `/frontend` - Next.js frontend application (in development)
  - `/app` - Next.js page routes
  - `/components` - React components
  - `/lib` - Utility functions
  - `/tests` - Frontend tests

- `/documentation` - Project documentation and design specs
