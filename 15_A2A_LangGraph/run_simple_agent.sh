#!/bin/bash
# Quick start script for Simple Agent Build

set -e

echo "=========================================="
echo "🚀 Simple Agent Build - Quick Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Running setup..."
    uv run python setup.py
    echo ""
fi

echo "This requires 2 terminal windows."
echo ""
echo "Terminal 1 (A2A Server):"
echo "  uv run python -m app"
echo ""
echo "Terminal 2 (Web UI - this script):"
echo "  uv run python simple_agent_build/app.py"
echo ""
echo "Then open: http://localhost:8000"
echo ""
echo "=========================================="
echo ""

read -p "Press Enter to start the Web UI (make sure A2A server is running in another terminal)..."

echo ""
echo "🌐 Starting Simple Agent Build Web UI..."
echo "   Open http://localhost:8000 in your browser"
echo ""

uv run python simple_agent_build/app.py

