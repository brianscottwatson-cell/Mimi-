#!/bin/bash
# Deploy with Docker

echo "🐳 Building and running Claudebot with Docker..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "❌ Docker is not installed. Visit https://docker.com/products/docker-desktop"
  exit 1
fi

echo "✓ Docker found"
echo ""

# Build and run
echo "Building Docker image..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "✓ Services started!"
echo ""
echo "Initializing database..."
sleep 5
docker-compose exec -T app npm run db:push

echo ""
echo "✓ Database initialized!"
echo ""
echo "🎉 Claudebot is running at http://localhost:3000"
echo ""
echo "Commands:"
echo "  docker-compose logs          - View logs"
echo "  docker-compose logs -f app   - Follow app logs"
echo "  docker-compose down          - Stop services"
echo "  docker-compose down -v       - Stop and remove volumes"
