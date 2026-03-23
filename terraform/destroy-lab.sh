#!/bin/bash
# Tear down the Hetzner lab server.
# Usage: ./destroy-lab.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

terraform destroy -auto-approve

echo ""
echo "Lab server destroyed."
