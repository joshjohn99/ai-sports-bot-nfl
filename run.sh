#!/bin/bash
# run.sh - A simple script to correctly run the AI Sports Bot

echo "--- Setting up AI Sports Bot Environment ---"

# Navigate to the directory where this script is located
cd "$(dirname "$0")"

# Activate the virtual environment
VENV_DIR="venv"
if [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please create it in the ai-sports-bot-nfl directory by running: python3 -m venv venv"
    exit 1
fi

# Ensure the project is installed in editable mode.
# The --quiet flag supresses output if already installed.
echo "Verifying project installation..."
pip install -e . --quiet

# Add the src directory to the python path to ensure modules are found
export PYTHONPATH="$PWD/src"

# Run the main application
echo "--- Starting the AI Sports Bot ---"
python main.py 