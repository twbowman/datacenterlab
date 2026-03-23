#!/bin/bash
# Manual OS detection script
# Can be run after deployment if automatic detection fails

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Configuration
TOPOLOGY_FILE="${1:-topology-srlinux.yml}"
OUTPUT_FILE="${2:-ansible/inventory-dynamic.yml}"
INVENTORY_SCRIPT="ansible/plugins/inventory/dynamic_inventory.py"

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Network Device OS Detection                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if topology file exists
if [ ! -f "$TOPOLOGY_FILE" ]; then
    print_error "Topology file not found: $TOPOLOGY_FILE"
    echo "Usage: $0 [topology-file.yml] [output-file.yml]"
    exit 1
fi

# Check if inventory script exists
if [ ! -f "$INVENTORY_SCRIPT" ]; then
    print_error "Dynamic inventory script not found: $INVENTORY_SCRIPT"
    exit 1
fi

print_info "Using topology file: $TOPOLOGY_FILE"
print_info "Output file: $OUTPUT_FILE"
echo ""

# Make script executable
chmod +x "$INVENTORY_SCRIPT"

# Run OS detection
print_info "Detecting device operating systems..."
echo ""

if python3 "$INVENTORY_SCRIPT" -t "$TOPOLOGY_FILE" -o "$OUTPUT_FILE" 2>&1 | while read -r line; do
    echo "  $line"
done; then
    echo ""
    print_success "OS detection complete!"
    echo ""
    
    # Display summary
    print_info "Detection summary:"
    
    if [ -f "$OUTPUT_FILE" ]; then
        # Count devices by OS
        for os in srlinux eos sonic junos unknown; do
            count=$(grep -c "ansible_network_os: $os" "$OUTPUT_FILE" 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                echo "  - $os: $count device(s)"
            fi
        done
        
        echo ""
        print_info "Inventory file: $OUTPUT_FILE"
        echo ""
        echo "Next steps:"
        echo "  1. Review the generated inventory:"
        echo "     cat $OUTPUT_FILE"
        echo ""
        echo "  2. Configure devices with Ansible:"
        echo "     ansible-playbook -i $OUTPUT_FILE ansible/site-multi-vendor.yml"
    fi
else
    echo ""
    print_error "OS detection failed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure devices are running and reachable"
    echo "  2. Check device management IPs in topology file"
    echo "  3. Verify gNMI is enabled on devices (port 57400)"
    echo "  4. Check if gnmic is installed: gnmic version"
    echo ""
    exit 1
fi
