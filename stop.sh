#!/usr/bin/env bash
set -euo pipefail

echo "Stopping Hospital Management System..."

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="hospital_management_system"

docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down

echo "All services stopped"
