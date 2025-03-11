# syntax=docker/dockerfile:1.4
# First stage: Build dependencies with Rust
FROM python:3.11-alpine AS builder

WORKDIR /code

# Install system dependencies + Rust installation requirements
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    postgresql-dev \
    libpq \
    mariadb-dev \
    mariadb-connector-c-dev \
    libgcc \
    libstdc++ \
    curl \
    openssl-dev

# Install Rust using rustup (more efficient than apk version)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Poetry
RUN pip install "poetry>=1.6.0"

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies with BuildKit caching
RUN poetry install --no-root --no-interaction --no-ansi 

# Final stage
FROM python:3.11-alpine

# Runtime dependencies
RUN apk add --no-cache \
    libpq \
    mariadb-connector-c \
    libstdc++ \
    libgcc

WORKDIR /code

# Copy installed dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]