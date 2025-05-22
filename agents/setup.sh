#!/bin/bash

# Setup script for East Baton Rouge Zoning Code Multi-Agent System
echo "Setting up East Baton Rouge Zoning Code Multi-Agent System..."

# Check for Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Error: Python is required but not found"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Warning: OPENAI_API_KEY environment variable is not set."
    echo "You will need to set this before running the agents."
    echo "You can do this by running: export OPENAI_API_KEY=your_api_key_here"
fi

# Install dependencies
echo "Installing required dependencies..."
$PYTHON -m pip install -r requirements.txt

# Make scripts executable
chmod +x ebr_zoning_cli.py
chmod +x ebr_zoning_web.py

echo "Setup complete!"
echo ""
echo "To run the CLI interface:"
echo "  ./ebr_zoning_cli.py -i"
echo ""
echo "To run the web interface:"
echo "  ./ebr_zoning_web.py"
echo ""
echo "Remember to set your OpenAI API key if you haven't already:"
echo "  export OPENAI_API_KEY=your_api_key_here"