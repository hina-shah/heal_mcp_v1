#!/bin/bash
# Script to run the HEAL MCP server

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting HEAL MCP Server...${NC}"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected."
    echo "Consider activating your virtualenv first."
    echo ""
fi

# Check if dependencies are installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "Error: fastmcp not installed."
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Run the server
echo "Server will be accessible at:"
echo "  - From host machine: http://localhost:8080/mcp"
echo "  - From container: http://0.0.0.0:8080/mcp"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m src.heal_mcp_server
