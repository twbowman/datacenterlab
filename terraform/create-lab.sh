#!/bin/bash
# Spin up the Hetzner lab server and generate .env.
# Usage: ./create-lab.sh [vendor]
#   vendor: srlinux (default), sonic

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR="${1:-srlinux}"

# Grab HCLOUD_TOKEN from hcloud CLI config if not already set
if [ -z "${HCLOUD_TOKEN:-}" ]; then
    HCLOUD_CONFIG="$HOME/.config/hcloud/cli.toml"
    if [ -f "$HCLOUD_CONFIG" ]; then
        HCLOUD_TOKEN=$(grep -m1 'token' "$HCLOUD_CONFIG" | sed 's/.*= *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | tr -d ' ')
        export HCLOUD_TOKEN
        echo "Using token from $HCLOUD_CONFIG"
    else
        echo "Error: HCLOUD_TOKEN not set and $HCLOUD_CONFIG not found."
        echo "Either export HCLOUD_TOKEN or run 'hcloud context create' first."
        exit 1
    fi
fi

cd "$SCRIPT_DIR"

terraform init -input=false
terraform apply -auto-approve

echo ""
./generate-env.sh "$VENDOR"

echo ""
echo "Lab server is ready. Run: ./scripts/lab setup && ./scripts/lab deploy"
