#!/bin/bash
# Simple network verification script

echo "=========================================="
echo "Network Verification"
echo "=========================================="
echo ""

echo "Checking BGP neighbors on spine1..."
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor" | grep -E "peer-address|session-state"

echo ""
echo "Checking BGP neighbors on leaf1..."
docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor" | grep -E "peer-address|session-state"

echo ""
echo "Checking LLDP neighbors on spine1..."
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor" | grep -E "Interface|System Name"

echo ""
echo "Checking interface status on spine1..."
docker exec clab-gnmi-clos-spine1 sr_cli "show interface ethernet-1/1 brief"

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
