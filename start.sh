#!/bin/bash

# StructGuard-API Startup Script

echo "🔒 Starting StructGuard-API..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the server
echo ""
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo ""
echo "Interactive documentation available at:"
echo "  📚 Swagger UI: http://localhost:8000/docs"
echo "  📖 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
