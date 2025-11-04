#!/bin/bash
# Start script to run both A2A agent server and Simple Agent Build UI

set -e

echo "=========================================="
echo "🚀 Starting A2A LangGraph Services"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Running setup..."
    uv run python setup.py
    echo ""
fi

# Check environment
echo "🔍 Checking environment..."
uv run python check_env.py
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $A2A_PID $UI_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start A2A Agent Server (port 10000)
echo -e "${BLUE}📡 Starting A2A Agent Server on port 10000...${NC}"
uv run python -m app --host localhost --port 10000 > a2a_server.log 2>&1 &
A2A_PID=$!
echo "   A2A Server PID: $A2A_PID"
echo "   Logs: a2a_server.log"
echo ""

# Wait for A2A server to start
echo "⏳ Waiting for A2A server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:10000/.well-known/agent.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ A2A Server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  A2A Server may not be ready yet, but continuing...${NC}"
    fi
    sleep 1
done
echo ""

# Start Simple Agent Build UI (port 8000)
echo -e "${BLUE}🌐 Starting Simple Agent Build UI on port 8000...${NC}"
uv run python simple_agent_build/app.py > ui_server.log 2>&1 &
UI_PID=$!
echo "   UI Server PID: $UI_PID"
echo "   Logs: ui_server.log"
echo ""

# Wait for UI server to start
echo "⏳ Waiting for UI server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UI Server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  UI Server may not be ready yet, but continuing...${NC}"
    fi
    sleep 1
done
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Both services are running!${NC}"
echo "=========================================="
echo ""
echo "📡 A2A Agent Server:  http://localhost:10000"
echo "🌐 Simple Agent UI:  http://localhost:8000"
echo ""
echo "📋 Logs:"
echo "   A2A Server: tail -f a2a_server.log"
echo "   UI Server:  tail -f ui_server.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Keep script running
wait

