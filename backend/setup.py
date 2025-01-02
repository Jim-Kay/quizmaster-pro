from setuptools import setup, find_packages

setup(
    name="quizmaster-backend",
    version="0.1.0",
    packages=find_packages(where=".", include=["api*", "models*", "crews*"]),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.28.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "crewai>=0.1.0",
    ],
)
