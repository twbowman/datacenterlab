#!/bin/bash
# Convert the lab from eBGP to iBGP with route reflectors
# All devices will use AS 65000
# Spines will be route reflectors

set -e

echo "Converting lab to iBGP configuration..."
echo "========================================"
echo ""

# Function to configure a device
configure_device() {
    local device=$1
    local asn=$2
    local router_id=$3
    
    echo "Configuring $device (AS $asn, Router ID $router_id)..."
    
    # Update AS number
    printf "enter candidate\n/network-instance default protocols bgp autonomous-system $asn\ncommit now\n" | \
        orb -m clab docker exec -i clab-gnmi-clos-$device sr_cli
    
    echo "  ✓ Updated AS number to $asn"
}

# Function to update neighbor AS numbers
update_neighbors() {
    local device=$1
    shift
    local neighbors=("$@")
    
    echo "Updating neighbors on $device..."
    
    for neighbor in "${neighbors[@]}"; do
        printf "enter candidate\n/network-instance default protocols bgp neighbor $neighbor peer-as 65000\ncommit now\n" | \
            orb -m clab docker exec -i clab-gnmi-clos-$device sr_cli
        echo "  ✓ Updated neighbor $neighbor to AS 65000"
    done
}

# Function to configure route reflector
configure_route_reflector() {
    local device=$1
    local cluster_id=$2
    shift 2
    local clients=("$@")
    
    echo "Configuring $device as route reflector (cluster-id $cluster_id)..."
    
    # Configure cluster-id
    printf "enter candidate\n/network-instance default protocols bgp group ibgp route-reflector cluster-id $cluster_id\ncommit now\n" | \
        orb -m clab docker exec -i clab-gnmi-clos-$device sr_cli
    
    echo "  ✓ Set cluster-id to $cluster_id"
    
    # Configure each client
    for client in "${clients[@]}"; do
        printf "enter candidate\n/network-instance default protocols bgp neighbor $client route-reflector client true\ncommit now\n" | \
            orb -m clab docker exec -i clab-gnmi-clos-$device sr_cli
        echo "  ✓ Configured $client as route reflector client"
    done
}

# Function to rename BGP group from ebgp to ibgp
rename_bgp_group() {
    local device=$1
    
    echo "Renaming BGP group on $device from ebgp to ibgp..."
    
    # This is complex, so we'll do it via CLI with multiple commands
    printf "enter candidate\n/network-instance default protocols bgp group ibgp\ncommit now\n" | \
        orb -m clab docker exec -i clab-gnmi-clos-$device sr_cli
    
    echo "  ✓ Created ibgp group"
}

echo "Step 1: Update AS numbers on all devices"
echo "-----------------------------------------"
configure_device "spine1" "65000" "10.0.0.1"
configure_device "spine2" "65000" "10.0.0.2"
configure_device "leaf1" "65000" "10.0.1.1"
configure_device "leaf2" "65000" "10.0.1.2"
configure_device "leaf3" "65000" "10.0.1.3"
configure_device "leaf4" "65000" "10.0.1.4"
echo ""

echo "Step 2: Update neighbor AS numbers"
echo "-----------------------------------"
update_neighbors "spine1" "10.1.1.1" "10.1.2.1" "10.1.3.1" "10.1.4.1"
update_neighbors "spine2" "10.2.1.1" "10.2.2.1" "10.2.3.1" "10.2.4.1"
update_neighbors "leaf1" "10.1.1.0" "10.2.1.0"
update_neighbors "leaf2" "10.1.2.0" "10.2.2.0"
update_neighbors "leaf3" "10.1.3.0" "10.2.3.0"
update_neighbors "leaf4" "10.1.4.0" "10.2.4.0"
echo ""

echo "Step 3: Configure route reflectors on spines"
echo "---------------------------------------------"
configure_route_reflector "spine1" "10.0.0.1" "10.1.1.1" "10.1.2.1" "10.1.3.1" "10.1.4.1"
configure_route_reflector "spine2" "10.0.0.2" "10.2.1.1" "10.2.2.1" "10.2.3.1" "10.2.4.1"
echo ""

echo "Step 4: Verify BGP sessions"
echo "----------------------------"
echo "Checking leaf1 BGP neighbors..."
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor" | grep -E "established|Peer"
echo ""

echo "Step 5: Verify EVPN routes"
echo "---------------------------"
echo "Checking leaf1 EVPN instance..."
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1"
echo ""

echo "Step 6: Check EVPN route advertisement"
echo "---------------------------------------"
echo "Checking leaf1 advertised EVPN routes to spine1..."
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor 10.1.1.0 advertised-routes evpn" | head -20
echo ""

echo "========================================" 
echo "iBGP conversion complete!"
echo "========================================"
echo ""
echo "All devices are now in AS 65000"
echo "Spines are configured as route reflectors"
echo ""
echo "Next steps:"
echo "1. Verify BGP sessions are established"
echo "2. Check EVPN routes are being advertised"
echo "3. Test client connectivity"
