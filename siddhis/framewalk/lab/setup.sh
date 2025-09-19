#!/bin/bash

echo "🚀 Setting up Framework Test Lab for Framewalk..."

# Build and start all containers
echo "📦 Building and starting containers..."
docker-compose -f docker-compose.yml up --build -d

# Wait for containers to be ready
echo "⏳ Waiting for containers to be ready..."
sleep 10

# Check if containers are running
echo "🔍 Checking container status..."
docker ps --filter "name=test-app" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Framework Test Lab is ready!"
echo ""
echo "🌐 Available endpoints:"
echo "   Web2py:    http://localhost:8081"
echo "   Sanic:     http://localhost:8082"
echo "   Tornado:   http://localhost:8083"
echo "   Starlette: http://localhost:8084"
echo "   CherryPy:  http://localhost:8085"
echo ""
echo "🧪 Test with Framewalk:"
echo "   vimana run framewalk --url http://localhost:8081"
echo "   vimana run framewalk --url http://localhost:8082"
echo "   vimana run framewalk --url http://localhost:8083"
echo "   vimana run framewalk --url http://localhost:8084"
echo "   vimana run framewalk --url http://localhost:8085"
echo ""
echo "🔗 Or test all at once:"
echo "   vimana run framewalk --url \"http://localhost:8081,http://localhost:8082,http://localhost:8083,http://localhost:8084,http://localhost:8085\" --verbose"
echo ""
echo "🛑 To stop the lab:"
echo "   docker-compose -f docker-compose.yml down" 