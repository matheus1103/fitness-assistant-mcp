FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências primeiro
COPY requirements.txt* ./
COPY pyproject.toml* ./
RUN pip install -r requirements.txt || pip install mcp pydantic pydantic-settings python-dotenv sqlalchemy[asyncio] asyncpg

COPY . .

CMD ["python", "run_server.py"]
