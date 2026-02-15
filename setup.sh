#!/bin/bash
# NEURO-TRIAGE SETUP WIZARD
# Quick setup script for getting started

set -e

echo "=========================================="
echo "  NEURO-TRIAGE SETUP WIZARD"
echo "=========================================="
echo ""

# Check prerequisites
echo "[1/5] Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✓ Docker found"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
echo "✓ Python 3 found"

# Setup environment
echo ""
echo "[2/5] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo "   Then run this script again."
    exit 0
else
    echo "✓ .env file exists"
fi

# Install dependencies
echo ""
echo "[3/5] Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Start Docker services
echo ""
echo "[4/5] Starting Docker services..."
docker-compose up -d
echo "✓ Docker services started"
echo "   Waiting for services to be healthy (30 seconds)..."
sleep 30

# Initialize system
echo ""
echo "[5/5] Initializing system..."
python scripts/init_system.py
echo "✓ System initialized"

echo ""
echo "=========================================="
echo "  ✨ SETUP COMPLETE! ✨"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend API:"
echo "   python -m src.api.main"
echo ""
echo "2. In another terminal, start the UI:"
echo "   streamlit run src/ui/app.py"
echo ""
echo "3. Open your browser:"
echo "   http://localhost:8501"
echo ""
echo "For more information, see:"
echo "   - README.md (full documentation)"
echo "   - QUICKSTART.md (quick reference)"
echo ""
