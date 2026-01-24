#!/bin/bash
# Quick activation script for the virtual environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: make install-dev"
    exit 1
fi

echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Virtual environment activated: $VIRTUAL_ENV"
echo ""
echo "Deactivate with: deactivate"
