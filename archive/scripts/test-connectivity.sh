#!/bin/bash
# Test connectivity between clients in the CLOS network

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CLOS Network Connectivity Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Ping from client1 to all other clients
echo -e "${YELLOW}Test 1: Ping from client1 to all clients${NC}"
for i in 2 3 4 5 6 7 8; do
    if [ $i -le 2 ]; then
        TARGET="10.10.1.$((i*10))"
    elif [ $i -le 4 ]; then
        TARGET="10.10.2.$(((i-2)*10))"
    elif [ $i -le 6 ]; then
        TARGET="10.10.3.$(((i-4)*10))"
    else
        TARGET="10.10.4.$(((i-6)*10))"
    fi
    echo -n "  client1 -> client$i ($TARGET): "
    if docker exec clab-gnmi-clos-client1 ping -c 1 -W 2 $TARGET > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
done
echo ""

# Test 2: Ping from client5 to all other clients
echo -e "${YELLOW}Test 2: Ping from client5 to all clients${NC}"
for i in 1 2 3 4 6 7 8; do
    if [ $i -le 2 ]; then
        TARGET="10.10.1.$((i*10))"
    elif [ $i -le 4 ]; then
        TARGET="10.10.2.$(((i-2)*10))"
    elif [ $i -le 6 ]; then
        TARGET="10.10.3.$(((i-4)*10))"
    else
        TARGET="10.10.4.$(((i-6)*10))"
    fi
    echo -n "  client5 -> client$i ($TARGET): "
    if docker exec clab-gnmi-clos-client5 ping -c 1 -W 2 $TARGET > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
done
echo ""

# Test 3: Check BGP routes on spines
echo -e "${YELLOW}Test 3: BGP routes on spines${NC}"
echo "  Checking spine1 BGP summary..."
docker exec clab-gnmi-clos-spine1 vtysh -c 'show ip bgp summary' | grep -E "leaf|Neighbor"
echo ""
echo "  Checking spine2 BGP summary..."
docker exec clab-gnmi-clos-spine2 vtysh -c 'show ip bgp summary' | grep -E "leaf|Neighbor"
echo ""

# Test 4: Check routes on clients
echo -e "${YELLOW}Test 4: Routes on clients${NC}"
echo "  client1 routing table:"
docker exec clab-gnmi-clos-client1 ip route | grep -E "10.10"
echo ""

# Test 5: Traceroute
echo -e "${YELLOW}Test 5: Traceroute from client1 to client8${NC}"
docker exec clab-gnmi-clos-client1 traceroute -n -m 5 10.10.4.10 2>/dev/null || echo "  (traceroute may not show all hops)"
echo ""

# Test 6: Interface status on leafs
echo -e "${YELLOW}Test 6: Interface status on leaf routers${NC}"
echo "  leaf1 interfaces:"
docker exec clab-gnmi-clos-leaf1 vtysh -c 'show interface brief' | grep -E "eth|Interface"
echo ""
echo "  leaf4 interfaces:"
docker exec clab-gnmi-clos-leaf4 vtysh -c 'show interface brief' | grep -E "eth|Interface"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Connectivity tests complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}To run bandwidth tests:${NC}"
echo "  # Terminal 1 - Start iperf3 server"
echo "  docker exec -it clab-gnmi-clos-client1 iperf3 -s"
echo ""
echo "  # Terminal 2 - Run iperf3 client"
echo "  docker exec -it clab-gnmi-clos-client8 iperf3 -c 10.10.1.10 -t 30"
echo ""
