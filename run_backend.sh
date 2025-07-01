#!/bin/bash
# Start the FastAPI backend server

echo "🚀 Starting AI Sports Bot Backend Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install dependencies if needed
if [ ! -f ".dependencies_installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    touch .dependencies_installed
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on port 8000..."
python fastapi_server.py 