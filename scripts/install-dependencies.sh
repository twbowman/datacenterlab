#!/bin/bash
# Install Python dependencies for link analysis tool

set -e

echo "🔧 Installing Python dependencies..."
echo ""

# Check if running in orb VM
if [ ! -f /etc/containerlab-release ] && [ ! -f /.dockerenv ]; then
    echo "⚠️  Warning: This script should be run inside the orb VM"
    echo "Run: orb -m clab"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if requests is already installed
if python3 -c "import requests" 2>/dev/null; then
    echo "✅ Python requests library is already installed"
    python3 -c "import requests; print(f'   Version: {requests.__version__}')"
    exit 0
fi

echo "Installing python3-requests via apt..."
echo ""

# Update package list
sudo apt update

# Install python3-requests
sudo apt install -y python3-requests

# Verify installation
if python3 -c "import requests" 2>/dev/null; then
    echo ""
    echo "✅ Successfully installed Python dependencies"
    python3 -c "import requests; print(f'   requests version: {requests.__version__}')"
    echo ""
    echo "You can now run:"
    echo "  ./lab analyze-links"
    echo "  python3 analyze-link-utilization.py"
else
    echo ""
    echo "❌ Installation failed"
    echo ""
    echo "Try manual installation:"
    echo "  sudo apt install python3-requests"
    echo ""
    echo "Or use a virtual environment:"
    echo "  python3 -m venv ~/venv-lab"
    echo "  source ~/venv-lab/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi
