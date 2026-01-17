#!/bin/bash

# CTF Platform Deployment Script

echo "==================================="
echo "CTF Platform Deployment Script"
echo "==================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and update the SECRET_KEY and other settings!"
    read -p "Press enter to continue after editing .env file..."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed."

# Build and start containers
echo ""
echo "Building and starting containers..."
docker compose up -d --build

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo ""
echo "Checking service status..."
docker compose ps

echo ""
echo "==================================="
echo "✅ Deployment completed!"
echo "==================================="
echo ""
echo "Access the platform at: http://localhost:5000"
echo "Default admin credentials:"
echo "  Email: admin@ctf.local"
echo "  Password: admin123"
echo ""
echo "⚠️  Remember to change the admin password after first login!"
echo ""
echo "Useful commands:"
echo "  View logs: docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart services: docker compose restart"
echo ""
