#!/usr/bin/env python3
"""
AI Sports Bot NFL - Main Entry Point
Run this script to start the interactive sports bot.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main sports agent
from sports_bot.core.sports_agents import main

if __name__ == "__main__":
    print("🏈 Starting AI Sports Bot NFL...")
    print("Type 'exit' or 'quit' to stop the bot")
    print("-" * 50)
    
    # Run the main function from sports_agents
    main() 