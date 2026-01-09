#!/usr/bin/env bash
# Quick Start Script for brank-backend
# This script sets up and starts the backend in one command

set -e  # Exit on error

echo "🚀 brank-backend Quick Start"
echo "=============================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "CHATGPT_API_KEY=sk-..."
    echo "GEMINI_API_KEY=..."
    echo "GROK_API_KEY=..."
    echo "PERPLEXITY_API_KEY=..."
    echo "DATABASE_URL=postgresql://user:pass@localhost:5432/brank"
    echo ""
    echo "See SETUP.md for detailed instructions."
    exit 1
fi

echo "✓ Found .env file"

# Check if database exists
DB_NAME=$(grep DATABASE_URL .env | cut -d'/' -f4 | cut -d'?' -f1)
if ! psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "📊 Creating database: $DB_NAME"
    createdb "$DB_NAME" || echo "⚠️  Database might already exist"
fi

echo "✓ Database ready"

# Install dependencies if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    uv pip install -e ".[dev]"
fi

echo "✓ Dependencies installed"

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo "✓ Migrations complete"

# Start server
echo ""
echo "🎉 Starting brank-backend server..."
echo ""
echo "Server will be available at: http://localhost:5000"
echo "Test with: curl http://localhost:5000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py

