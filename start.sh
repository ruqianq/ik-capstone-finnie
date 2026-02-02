#!/bin/bash
# Quick start script for FinnIE

set -e

echo "========================================"
echo "  FinnIE Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your GOOGLE_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check if GOOGLE_API_KEY is set
source .env
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
    echo "✗ GOOGLE_API_KEY is not set in .env"
    echo "  Please edit .env and add your actual API key"
    exit 1
fi

echo "✓ GOOGLE_API_KEY is configured"
echo ""

# Start services
echo "Starting FinnIE services..."
echo ""
docker compose up --build -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are up
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "========================================"
    echo "  ✓ FinnIE is running!"
    echo "========================================"
    echo ""
    echo "Access the following endpoints:"
    echo "  • API:            http://localhost:8000"
    echo "  • API Docs:       http://localhost:8000/docs"
    echo "  • Health Check:   http://localhost:8000/health"
    echo "  • Phoenix:        http://localhost:6006"
    echo ""
    echo "To test the API, run:"
    echo "  python test_api.py"
    echo ""
    echo "To view logs:"
    echo "  docker compose logs -f"
    echo ""
    echo "To stop services:"
    echo "  docker compose down"
    echo ""
else
    echo ""
    echo "✗ Services failed to start"
    echo "Check logs with: docker compose logs"
    exit 1
fi
