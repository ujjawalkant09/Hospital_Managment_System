#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting deployment..."

# ---- CONFIG ----
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.docker"
PROJECT_NAME="hospital_management_system"

# ---- VALIDATIONS ----
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is not available"
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo " $ENV_FILE not found"
  exit 1
fi

echo "Prerequisites OK"


echo "Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down

echo "Building Docker images..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build


echo "Starting services..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d


echo "Containers status:"
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

echo "Deployment completed successfully"
