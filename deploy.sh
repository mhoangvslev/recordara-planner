#!/bin/bash

# Local deployment script for testing GitHub Pages setup

echo "🚀 Starting local deployment test..."

# Run backend to generate data
echo "📊 Running Python backend..."
cd backend
if command -v poetry &> /dev/null; then
    poetry run planner
else
    echo "⚠️  Poetry not found, trying to run with python directly..."
    python -m planner.main
fi
cd ..

# Data is served via API endpoints, no need to copy to public directory
echo "📁 Data will be served via API endpoints..."

# Build frontend
echo "🏗️  Building frontend..."
cd frontend
NODE_ENV=production npm run generate
cd ..

echo "✅ Deployment test complete!"
echo "📂 Static files generated in: frontend/dist/"
echo "🌐 You can preview with: cd frontend && npm run preview"
