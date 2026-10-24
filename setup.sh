#!/bin/bash
# Setup script for LLM Router development

set -e

echo "=========================================="
echo "LLM Router - Development Setup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed"

# Check for API key
echo ""
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠ GROQ_API_KEY not set"
    echo ""
    echo "To get started:"
    echo "  1. Get API key from: https://console.groq.com/keys"
    echo "  2. Set environment variable:"
    echo "     export GROQ_API_KEY=your_key_here"
    echo ""
    echo "  3. Add to ~/.bashrc or ~/.zshrc to persist:"
    echo "     echo 'export GROQ_API_KEY=your_key_here' >> ~/.bashrc"
else
    echo "✓ GROQ_API_KEY is set"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Generate dataset:"
echo "     cd datasets && python sample_datasets.py"
echo ""
echo "  2. Run pilot evaluation (20 prompts):"
echo "     cd evaluation && python runner.py --model groq-20b --limit 20"
echo ""
echo "  3. Run full evaluation:"
echo "     python runner.py --model groq-20b"
echo "     python runner.py --model groq-120b"
echo ""
echo "See README.md for full documentation."
echo ""
