# Setup script for LLM Router development (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "LLM Router - Development Setup"
Write-Host "=========================================="
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..."
pip install -r requirements.txt

Write-Host ""
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Check for API key
Write-Host ""
if (-not $env:GROQ_API_KEY) {
    Write-Host "⚠ GROQ_API_KEY not set" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To get started:"
    Write-Host "  1. Get API key from: https://console.groq.com/keys"
    Write-Host "  2. Set environment variable (current session):"
    Write-Host "     `$env:GROQ_API_KEY = 'your_key_here'"
    Write-Host ""
    Write-Host "  3. To persist across sessions, add to PowerShell profile:"
    Write-Host "     Add-Content `$PROFILE '`$env:GROQ_API_KEY = \"your_key_here\"'"
} else {
    Write-Host "✓ GROQ_API_KEY is set" -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Setup Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host ""
Write-Host "  1. Generate dataset:"
Write-Host "     cd datasets; python sample_datasets.py"
Write-Host ""
Write-Host "  2. Run pilot evaluation (20 prompts):"
Write-Host "     cd evaluation; python runner.py --model groq-20b --limit 20"
Write-Host ""
Write-Host "  3. Run full evaluation:"
Write-Host "     python runner.py --model groq-20b"
Write-Host "     python runner.py --model groq-120b"
Write-Host ""
Write-Host "See README.md for full documentation."
Write-Host ""
