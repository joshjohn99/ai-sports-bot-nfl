#!/bin/bash

# AI Sports Bot NFL - Development Setup Script
# This script sets up the development environment for new contributors

set -e  # Exit on any error

echo "🏈 AI Sports Bot NFL - Development Setup"
echo "========================================"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "📝 Please edit .env file with your API keys"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "🗄️ Initializing database..."
if [ -f "scripts/init_database.py" ]; then
    python scripts/init_database.py
    echo "✅ Database initialized"
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
python -m pytest tests/ -v --tb=short || echo "⚠️ Some tests failed - this might be expected if API keys are not configured"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys (RAPIDAPI_KEY, OPENAI_API_KEY)"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'python examples/hybrid_main.py' to test the system"
echo "4. Run 'python test_integration_final.py' for full integration test"
echo ""
echo "📚 Documentation:"
echo "- README.md - Project overview"
echo "- CONTRIBUTING.md - Contribution guidelines" 
echo "- docs/PROJECT_STRUCTURE.md - Project structure"
echo ""
echo "Happy coding! 🚀" 