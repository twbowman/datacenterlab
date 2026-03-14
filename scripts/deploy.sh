#!/bin/bash
# ContainerLab deployment script - Network lab only

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Deploying SR Linux CLOS network topology...${NC}"

# Deploy topology
containerlab deploy -t topology.yml

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
    if python3 ansible/plugins/inventory/dynamic_inventory.py -t topology.yml -o ansible/inventory-dynamic.yml 2>&1; then
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
echo "  containerlab inspect -t topology.yml"

