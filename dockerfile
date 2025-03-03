# First stage: Build dependencies
FROM python:3.11-alpine AS builder

# Set working directory
WORKDIR /code

# Install system dependencies required for the packages
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev \
    postgresql-dev libpq curl mariadb-dev mariadb-connector-c-dev \
    rust cargo libgcc libstdc++

# Install poetry
RUN pip install "poetry>=1.6.0"

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use virtualenvs in Docker
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Second stage: Minimal final image
FROM python:3.11-alpine

# Install runtime dependencies
RUN apk add --no-cache libpq mariadb-connector-c libstdc++ libgcc

# Set working directory
WORKDIR /code

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY . .

# Expose the port (adjust if needed)
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]