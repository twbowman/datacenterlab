#!/bin/bash
# Configure LLDP on all SR Linux devices via CLI

set -e

configure_lldp() {
    local node=$1
    shift
    local interfaces=("$@")
    
    echo "Configuring LLDP on $node..."
    
    # Build the configuration commands
    {
        echo "enter candidate"
        echo "set / system lldp admin-state enable"
        for intf in "${interfaces[@]}"; do
            echo "set / interface $intf admin-state enable"
            echo "set / system lldp interface $intf admin-state enable"
        done
        echo "commit now"
    } | docker exec -i $node sr_cli
}

# Configure spine switches
configure_lldp "clab-gnmi-clos-spine1" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3" "ethernet-1/4"
configure_lldp "clab-gnmi-clos-spine2" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3" "ethernet-1/4"

# Configure leaf switches
configure_lldp "clab-gnmi-clos-leaf1" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3"
configure_lldp "clab-gnmi-clos-leaf2" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3"
configure_lldp "clab-gnmi-clos-leaf3" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3"
configure_lldp "clab-gnmi-clos-leaf4" "ethernet-1/1" "ethernet-1/2" "ethernet-1/3"

echo ""
echo "Waiting 10 seconds for LLDP neighbors to be discovered..."
sleep 10

echo ""
echo "=== LLDP Neighbors on spine1 ==="
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"

echo ""
echo "=== LLDP Neighbors on leaf1 ==="
docker exec clab-gnmi-clos-leaf1 sr_cli "show system lldp neighbor"

echo ""
echo "LLDP configuration complete!"


echo ""
echo "Waiting 10 seconds for LLDP neighbors to be discovered..."
sleep 10

echo ""
echo "=== LLDP Neighbors on spine1 ==="
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"

echo ""
echo "=== LLDP Neighbors on leaf1 ==="
docker exec clab-gnmi-clos-leaf1 sr_cli "show system lldp neighbor"

echo ""
echo "LLDP configuration complete!"
