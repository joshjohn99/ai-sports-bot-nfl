#!/bin/bash
# Start the Next.js frontend

echo "🎨 Starting AI Sports Bot Frontend..."

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start Next.js development server
echo "🌐 Starting Next.js server on port 3000..."
npm run dev 