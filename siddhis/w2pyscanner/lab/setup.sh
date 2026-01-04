#!/bin/bash

# W2PyScanner Lab Setup Script
# This script sets up the vulnerable Web2py application for testing

set -e

echo "🚀 Setting up W2PyScanner Lab Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Build and start the lab
echo "📦 Building and starting the vulnerable Web2py application..."
docker-compose up --build -d

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:8086/ > /dev/null 2>&1; then
    echo "✅ W2PyScanner lab is running successfully!"
    echo ""
    echo "🌐 Lab URLs:"
    echo "   Main Application: http://localhost:8086"
    echo "   Admin Interface:  http://localhost:8086/admin/"
    echo "   About Page:       http://localhost:8086/about"
    echo "   Upload Page:      http://localhost:8086/upload"
    echo "   API Endpoint:     http://localhost:8086/api"
    echo "   Database Page:    http://localhost:8086/database"
    echo "   Session Test:     http://localhost:8086/session_test"
    echo "   CSRF Test:        http://localhost:8086/csrf_test"
    echo "   Error Page:       http://localhost:8086/error"
    echo ""
    echo "🔑 Admin Credentials:"
    echo "   Email:    admin@example.com"
    echo "   Password: admin123"
    echo ""
    echo "🧪 Test the scanner:"
    echo "   vimana run w2pyscanner --target-url http://localhost:8086 --verbose"
    echo ""
    echo "🛑 To stop the lab:"
    echo "   docker-compose down"
else
    echo "❌ Failed to start the lab. Check the logs:"
    docker-compose logs
    exit 1
fi 