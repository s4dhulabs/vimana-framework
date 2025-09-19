#!/bin/bash

echo "🧹 Cleaning up Framework Test Lab..."

# Stop and remove containers
echo "🛑 Stopping containers..."
docker-compose -f docker-compose.yml down

# Remove any dangling images
echo "🗑️  Cleaning up images..."
docker image prune -f

echo "✅ Framework Test Lab cleaned up!" 