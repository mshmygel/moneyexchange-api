FROM python:3.12-slim

# environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# directory
WORKDIR /app

# system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy only Poetry files
COPY pyproject.toml poetry.lock* /app/

# project dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

COPY . /app/

# Expose port 8000
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
