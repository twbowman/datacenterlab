#!/bin/bash
# First-time setup for a remote Linux lab server (Ubuntu/Debian).
# Installs: Docker, containerlab, gnmic, Ansible, Python deps.
#
# Run via: ./lab setup
# Or manually: scp this to the server and run it.

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Remote Lab Server Setup ===${NC}"
echo ""

# ─────────────────────────────────────────────────────────────
# 1. System packages
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Updating system packages...${NC}"
apt-get update -qq
apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release \
    git jq python3 python3-pip python3-venv \
    rsync htop

# ─────────────────────────────────────────────────────────────
# 2. Docker
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/6] Installing Docker...${NC}"
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
else
    echo "Docker already installed: $(docker --version)"
fi

# ─────────────────────────────────────────────────────────────
# 3. Containerlab
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/6] Installing containerlab...${NC}"
if ! command -v containerlab &>/dev/null; then
    bash -c "$(curl -sL https://get.containerlab.dev)"
else
    echo "containerlab already installed: $(containerlab version | head -1)"
fi

# ─────────────────────────────────────────────────────────────
# 4. gNMIc
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/6] Installing gNMIc...${NC}"
if ! command -v gnmic &>/dev/null; then
    bash -c "$(curl -sL https://get-gnmic.openconfig.net)"
else
    echo "gNMIc already installed: $(gnmic version)"
fi

# ─────────────────────────────────────────────────────────────
# 5. Ansible + Python dependencies
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/6] Installing Ansible and Python dependencies...${NC}"
pip3 install --quiet \
    ansible \
    pygnmi \
    dictdiffer \
    jmespath \
    netaddr

# Install Ansible Galaxy collections used by the project
ansible-galaxy collection install nokia.srlinux --force-with-deps 2>/dev/null || true
ansible-galaxy collection install arista.eos --force-with-deps 2>/dev/null || true
ansible-galaxy collection install junipernetworks.junos --force-with-deps 2>/dev/null || true

# ─────────────────────────────────────────────────────────────
# 6. Working directory + verification
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[6/6] Creating working directory and verifying...${NC}"
mkdir -p /opt/containerlab

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Installed versions:"
echo "  Docker:       $(docker --version 2>/dev/null || echo 'not found')"
echo "  Containerlab: $(containerlab version 2>/dev/null | head -1 || echo 'not found')"
echo "  gNMIc:        $(gnmic version 2>/dev/null | head -1 || echo 'not found')"
echo "  Ansible:      $(ansible --version 2>/dev/null | head -1 || echo 'not found')"
echo "  Python:       $(python3 --version 2>/dev/null || echo 'not found')"
echo ""
echo -e "${GREEN}Server is ready. Run './lab deploy' from your local machine.${NC}"
