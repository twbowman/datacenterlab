#!/bin/bash
# ContainerLab deployment script - Network lab only
#
# Usage:
#   ./scripts/deploy.sh                    # Deploy SR Linux (default)
#   ./scripts/deploy.sh srlinux            # Deploy SR Linux
#   ./scripts/deploy.sh sonic              # Deploy SONiC
#   ./scripts/deploy.sh --validate         # Deploy SR Linux + validate
#   ./scripts/deploy.sh sonic --validate   # Deploy SONiC + validate

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse arguments
RUN_VALIDATE=0
VENDOR="srlinux"
for arg in "$@"; do
    case "$arg" in
        srlinux)
            VENDOR="srlinux"
            ;;
        sonic)
            VENDOR="sonic"
            ;;
        --validate)
            RUN_VALIDATE=1
            ;;
        --help|-h)
            echo "Usage: $0 [VENDOR] [OPTIONS]"
            echo ""
            echo "Vendors:"
            echo "  srlinux      Deploy SR Linux CLOS topology (default)"
            echo "  sonic        Deploy SONiC CLOS topology"
            echo ""
            echo "Options:"
            echo "  --validate   Run configuration validation after deployment"
            echo "  --help, -h   Show this help message"
            exit 0
            ;;
    esac
done

TOPOLOGY_FILE="../topology-${VENDOR}.yml"

if [ ! -f "$TOPOLOGY_FILE" ]; then
    echo -e "${RED}Topology file not found: ${TOPOLOGY_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}Deploying ${VENDOR} CLOS network topology...${NC}"

# Deploy topology
containerlab deploy -t "$TOPOLOGY_FILE"

echo -e "${YELLOW}Waiting for routers to boot (30 seconds)...${NC}"
sleep 30

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Access routers via gNMI:"
echo "  spine1: 172.20.20.10:57400"
echo "  spine2: 172.20.20.11:57400"
echo "  leaf1:  172.20.20.21:57400"
echo "  leaf2:  172.20.20.22:57400"
echo "  leaf3:  172.20.20.23:57400"
echo "  leaf4:  172.20.20.24:57400"
echo ""
echo "Access clients:"
echo "  docker exec -it clab-gnmi-clos-client1 sh"
echo "  docker exec -it clab-gnmi-clos-client2 sh"
echo ""

# Generate dynamic inventory with OS detection
echo -e "${YELLOW}Generating dynamic inventory with OS detection...${NC}"
if [ -f "ansible/plugins/inventory/dynamic_inventory.py" ]; then
    chmod +x ansible/plugins/inventory/dynamic_inventory.py
    if python3 ansible/plugins/inventory/dynamic_inventory.py -t "topology-${VENDOR}.yml" -o ansible/inventory-dynamic.yml 2>&1; then
        echo -e "${GREEN}Dynamic inventory generated: ansible/inventory-dynamic.yml${NC}"
        echo ""
        echo "Configure network with Ansible (using dynamic inventory):"
        echo "  ansible-playbook -i ansible/inventory-dynamic.yml ansible/site.yml"
    else
        echo -e "${YELLOW}Warning: Failed to generate dynamic inventory${NC}"
        echo "Configure network with Ansible (using static inventory):"
        echo "  ansible-playbook -i ansible/inventory.yml ansible/site.yml"
    fi
else
    echo "Configure network with Ansible:"
    echo "  ansible-playbook -i ansible/inventory.yml ansible/site.yml"
fi

echo ""
echo "Deploy monitoring stack separately:"
echo "  ./deploy-monitoring.sh"
echo ""
echo "View topology:"
echo "  containerlab inspect -t topology-${VENDOR}.yml"

# ─────────────────────────────────────────────────────────────
# Optional: Run validation after deployment
# ─────────────────────────────────────────────────────────────
if [ "$RUN_VALIDATE" -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Running post-deployment validation...${NC}"
    echo ""

    # Determine which inventory to use
    VALIDATE_INVENTORY="ansible/inventory.yml"
    if [ -f "ansible/inventory-dynamic.yml" ]; then
        VALIDATE_INVENTORY="ansible/inventory-dynamic.yml"
    fi

    if [ -f "ansible/playbooks/validate.yml" ]; then
        if ANSIBLE_CALLBACK_PLUGINS=ansible/callback_plugins \
           ANSIBLE_CALLBACKS_ENABLED=validation_report \
           ansible-playbook -i "$VALIDATE_INVENTORY" ansible/playbooks/validate.yml; then
            echo ""
            echo -e "${GREEN}✔ Post-deployment validation passed${NC}"
        else
            echo ""
            echo -e "${RED}✘ Post-deployment validation failed - critical checks did not pass${NC}"
            echo -e "${RED}  Review validation-report.json for details${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ ansible/playbooks/validate.yml not found, skipping validation${NC}"
    fi
fi
