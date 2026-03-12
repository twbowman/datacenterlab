#!/bin/bash
# Comprehensive verification script for CLOS network lab

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print section header
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to print test result
check_test() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $2"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to print info
print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header "ContainerLab CLOS Network Verification"

# Check 1: ContainerLab Installation
print_header "1. Prerequisites Check"
if command -v containerlab &> /dev/null; then
    VERSION=$(containerlab version | head -1)
    check_test 0 "ContainerLab installed: $VERSION"
else
    check_test 1 "ContainerLab not found"
fi

if command -v docker &> /dev/null; then
    VERSION=$(docker --version)
    check_test 0 "Docker installed: $VERSION"
else
    check_test 1 "Docker not found"
fi

# Check 2: Lab Deployment Status
print_header "2. Lab Deployment Status"

LAB_RUNNING=$(sudo containerlab inspect -t topology.yml 2>/dev/null | grep -c "gnmi-clos" || echo "0")
if [ "$LAB_RUNNING" -gt 0 ]; then
    check_test 0 "Lab is deployed"
else
    check_test 1 "Lab is not deployed (run ./deploy.sh)"
    echo ""
    echo -e "${RED}Lab not running. Exiting verification.${NC}"
    exit 1
fi

# Check 3: Container Status
print_header "3. Container Status"

CONTAINERS=("monitoring" "spine1" "spine2" "leaf1" "leaf2" "leaf3" "leaf4" "client1" "client2" "client3" "client4" "client5" "client6" "client7" "client8")

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "clab-gnmi-clos-$container"; then
        STATUS=$(docker inspect -f '{{.State.Status}}' "clab-gnmi-clos-$container" 2>/dev/null)
        if [ "$STATUS" = "running" ]; then
            check_test 0 "Container $container is running"
        else
            check_test 1 "Container $container status: $STATUS"
        fi
    else
        check_test 1 "Container $container not found"
    fi
done

# Check 4: Network Connectivity (Management)
print_header "4. Management Network Connectivity"

MGMT_IPS=("172.20.20.10:spine1" "172.20.20.11:spine2" "172.20.20.21:leaf1" "172.20.20.22:leaf2" "172.20.20.23:leaf3" "172.20.20.24:leaf4")

for entry in "${MGMT_IPS[@]}"; do
    IP="${entry%%:*}"
    NAME="${entry##*:}"
    if docker exec clab-gnmi-clos-monitoring ping -c 1 -W 2 "$IP" > /dev/null 2>&1; then
        check_test 0 "Ping to $NAME ($IP) successful"
    else
        check_test 1 "Ping to $NAME ($IP) failed"
    fi
done

# Check 5: SSH Connectivity
print_header "5. SSH Connectivity"

for entry in "${MGMT_IPS[@]}"; do
    IP="${entry%%:*}"
    NAME="${entry##*:}"
    if timeout 5 docker exec clab-gnmi-clos-monitoring sshpass -p admin ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 root@"$IP" "hostname" > /dev/null 2>&1; then
        check_test 0 "SSH to $NAME ($IP) successful"
    else
        print_warning "SSH to $NAME ($IP) failed (sshpass may not be installed)"
    fi
done

# Check 6: FRR Status
print_header "6. FRR Routing Daemon Status"

ROUTERS=("spine1" "spine2" "leaf1" "leaf2" "leaf3" "leaf4")

for router in "${ROUTERS[@]}"; do
    if docker exec "clab-gnmi-clos-$router" vtysh -c "show version" > /dev/null 2>&1; then
        check_test 0 "FRR running on $router"
    else
        check_test 1 "FRR not responding on $router"
    fi
done

# Check 7: BGP Status
print_header "7. BGP Neighbor Status"

# Check spine1 BGP neighbors
SPINE1_NEIGHBORS=$(docker exec clab-gnmi-clos-spine1 vtysh -c "show ip bgp summary json" 2>/dev/null | grep -c "Established" || echo "0")
if [ "$SPINE1_NEIGHBORS" -ge 4 ]; then
    check_test 0 "spine1 has $SPINE1_NEIGHBORS BGP neighbors established (expected: 4)"
else
    check_test 1 "spine1 has $SPINE1_NEIGHBORS BGP neighbors established (expected: 4)"
fi

# Check spine2 BGP neighbors
SPINE2_NEIGHBORS=$(docker exec clab-gnmi-clos-spine2 vtysh -c "show ip bgp summary json" 2>/dev/null | grep -c "Established" || echo "0")
if [ "$SPINE2_NEIGHBORS" -ge 4 ]; then
    check_test 0 "spine2 has $SPINE2_NEIGHBORS BGP neighbors established (expected: 4)"
else
    check_test 1 "spine2 has $SPINE2_NEIGHBORS BGP neighbors established (expected: 4)"
fi

# Check leaf BGP neighbors (each should have 2)
for leaf in leaf1 leaf2 leaf3 leaf4; do
    LEAF_NEIGHBORS=$(docker exec "clab-gnmi-clos-$leaf" vtysh -c "show ip bgp summary json" 2>/dev/null | grep -c "Established" || echo "0")
    if [ "$LEAF_NEIGHBORS" -ge 2 ]; then
        check_test 0 "$leaf has $LEAF_NEIGHBORS BGP neighbors established (expected: 2)"
    else
        check_test 1 "$leaf has $LEAF_NEIGHBORS BGP neighbors established (expected: 2)"
    fi
done

# Check 8: BGP Routes
print_header "8. BGP Route Propagation"

# Check if spine1 has routes from all leafs
SPINE1_ROUTES=$(docker exec clab-gnmi-clos-spine1 vtysh -c "show ip bgp" 2>/dev/null | grep -c "10.10" || echo "0")
if [ "$SPINE1_ROUTES" -ge 4 ]; then
    check_test 0 "spine1 has $SPINE1_ROUTES client routes (expected: ≥4)"
else
    check_test 1 "spine1 has $SPINE1_ROUTES client routes (expected: ≥4)"
fi

# Check if leaf1 has routes from other leafs
LEAF1_ROUTES=$(docker exec clab-gnmi-clos-leaf1 vtysh -c "show ip bgp" 2>/dev/null | grep -c "10.10" || echo "0")
if [ "$LEAF1_ROUTES" -ge 4 ]; then
    check_test 0 "leaf1 has $LEAF1_ROUTES routes (expected: ≥4)"
else
    check_test 1 "leaf1 has $LEAF1_ROUTES routes (expected: ≥4)"
fi

# Check 9: Interface Status
print_header "9. Interface Status"

for router in "${ROUTERS[@]}"; do
    INTERFACES_UP=$(docker exec "clab-gnmi-clos-$router" vtysh -c "show interface brief" 2>/dev/null | grep -c " up " || echo "0")
    if [ "$INTERFACES_UP" -ge 2 ]; then
        check_test 0 "$router has $INTERFACES_UP interfaces up"
    else
        check_test 1 "$router has $INTERFACES_UP interfaces up (expected: ≥2)"
    fi
done

# Check 10: Client Connectivity
print_header "10. Client-to-Client Connectivity"

# Test connectivity from client1 to clients in other racks
TEST_TARGETS=("10.10.2.10:client3" "10.10.3.10:client5" "10.10.4.10:client7")

for target in "${TEST_TARGETS[@]}"; do
    IP="${target%%:*}"
    NAME="${target##*:}"
    if docker exec clab-gnmi-clos-client1 ping -c 1 -W 2 "$IP" > /dev/null 2>&1; then
        check_test 0 "client1 can ping $NAME ($IP)"
    else
        check_test 1 "client1 cannot ping $NAME ($IP)"
    fi
done

# Check 11: Monitoring Stack
print_header "11. Monitoring Stack Status"

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    check_test 0 "Grafana is accessible on port 3000"
else
    check_test 1 "Grafana is not accessible on port 3000"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    check_test 0 "Prometheus is accessible on port 9090"
else
    check_test 1 "Prometheus is not accessible on port 9090"
fi

# Check InfluxDB
if curl -s http://localhost:8086/health > /dev/null 2>&1; then
    check_test 0 "InfluxDB is accessible on port 8086"
else
    check_test 1 "InfluxDB is not accessible on port 8086"
fi

# Check Telegraf
if docker exec clab-gnmi-clos-monitoring pgrep telegraf > /dev/null 2>&1; then
    check_test 0 "Telegraf is running"
else
    check_test 1 "Telegraf is not running"
fi

# Check 12: gNMI Connectivity
print_header "12. gNMI Telemetry Status"

# Check if gNMI ports are listening
for entry in "${MGMT_IPS[@]}"; do
    IP="${entry%%:*}"
    NAME="${entry##*:}"
    if docker exec clab-gnmi-clos-monitoring nc -zv "$IP" 9339 2>&1 | grep -q "succeeded"; then
        check_test 0 "gNMI port accessible on $NAME ($IP:9339)"
    else
        print_warning "gNMI port check failed on $NAME (may need gnmic installed)"
    fi
done

# Summary
print_header "Verification Summary"

PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo -e "Total Checks:  ${CYAN}$TOTAL_CHECKS${NC}"
echo -e "Passed:        ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed:        ${RED}$FAILED_CHECKS${NC}"
echo -e "Success Rate:  ${CYAN}${PASS_RATE}%${NC}"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${CYAN}Lab is fully operational!${NC}"
    echo ""
    echo "Next steps:"
    echo "  • Access Grafana: http://localhost:3000 (admin/admin)"
    echo "  • View BGP status: docker exec -it clab-gnmi-clos-spine1 vtysh -c 'show ip bgp summary'"
    echo "  • Test bandwidth: docker exec -it clab-gnmi-clos-client1 iperf3 -s"
    exit 0
else
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}⚠ Some checks failed${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "  • Check container logs: docker logs clab-gnmi-clos-<container>"
    echo "  • Verify BGP: docker exec -it clab-gnmi-clos-spine1 vtysh -c 'show ip bgp summary'"
    echo "  • Check interfaces: docker exec -it clab-gnmi-clos-leaf1 vtysh -c 'show interface brief'"
    echo "  • Review README.md troubleshooting section"
    exit 1
fi
