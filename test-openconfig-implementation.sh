#!/bin/bash
# Test OpenConfig telemetry implementation
# Run this where containerlab is installed

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "OpenConfig Telemetry Implementation Test"
echo -e "==========================================${NC}"
echo ""

# Check if containerlab is available
if ! command -v containerlab &> /dev/null; then
    echo -e "${RED}Error: containerlab not found${NC}"
    echo "Please install containerlab or run this where containerlab is available"
    exit 1
fi

# Step 1: Check if lab is running
echo -e "${BLUE}Step 1: Checking lab status...${NC}"
if docker ps --filter "name=clab-gnmi-clos-spine1" --format "{{.Names}}" | grep -q "spine1"; then
    echo -e "${GREEN}✓ Lab is running${NC}"
else
    echo -e "${YELLOW}Lab not running. Starting lab...${NC}"
    ./deploy.sh
    echo "Waiting 120 seconds for devices to boot..."
    sleep 120
fi
echo ""

# Step 2: Restart gNMIc with new OpenConfig config
echo -e "${BLUE}Step 2: Restarting gNMIc with OpenConfig configuration...${NC}"
docker restart clab-gnmi-clos-gnmic
echo "Waiting 10 seconds for gNMIc to start..."
sleep 10
echo -e "${GREEN}✓ gNMIc restarted${NC}"
echo ""

# Step 3: Test OpenConfig paths on SR Linux
echo -e "${BLUE}Step 3: Testing OpenConfig paths on SR Linux devices...${NC}"
echo ""

test_openconfig_path() {
    local device=$1
    local path=$2
    local description=$3
    
    echo -n "  Testing $description on $device... "
    
    if timeout 5 docker exec clab-gnmi-clos-gnmic gnmic -a "$device:57400" \
        -u admin -p NokiaSrl1! --insecure \
        get --path "$path" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Test spine1
echo -e "${YELLOW}Testing spine1:${NC}"
test_openconfig_path "clab-gnmi-clos-spine1" \
    "/interfaces/interface[name=ethernet-1/1]/state/counters" \
    "Interface counters"

test_openconfig_path "clab-gnmi-clos-spine1" \
    "/interfaces/interface[name=ethernet-1/1]/state/oper-status" \
    "Interface oper-status"

test_openconfig_path "clab-gnmi-clos-spine1" \
    "/interfaces/interface[name=ethernet-1/1]/state/admin-status" \
    "Interface admin-status"

test_openconfig_path "clab-gnmi-clos-spine1" \
    "/lldp/interfaces" \
    "LLDP interfaces"

echo ""

# Test leaf1
echo -e "${YELLOW}Testing leaf1:${NC}"
test_openconfig_path "clab-gnmi-clos-leaf1" \
    "/interfaces/interface[name=ethernet-1/1]/state/counters" \
    "Interface counters"

test_openconfig_path "clab-gnmi-clos-leaf1" \
    "/interfaces/interface[name=ethernet-1/1]/state/oper-status" \
    "Interface oper-status"

echo ""

# Step 4: Test OpenConfig subscriptions
echo -e "${BLUE}Step 4: Testing OpenConfig subscriptions (streaming telemetry)...${NC}"
echo ""

test_subscription() {
    local device=$1
    local path=$2
    local description=$3
    
    echo -n "  Testing subscription: $description on $device... "
    
    if timeout 10 docker exec clab-gnmi-clos-gnmic gnmic -a "$device:57400" \
        -u admin -p NokiaSrl1! --insecure \
        subscribe --path "$path" --mode stream --stream-mode sample \
        --sample-interval 5s --count 1 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

test_subscription "clab-gnmi-clos-spine1" \
    "/interfaces/interface/state/counters" \
    "Interface counters stream"

test_subscription "clab-gnmi-clos-spine1" \
    "/lldp/interfaces/interface/neighbors" \
    "LLDP neighbors stream"

echo ""

# Step 5: Check gNMIc is collecting metrics
echo -e "${BLUE}Step 5: Checking gNMIc Prometheus metrics...${NC}"
echo ""

check_metric() {
    local metric_pattern=$1
    local description=$2
    
    echo -n "  Checking $description... "
    
    if docker exec clab-gnmi-clos-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
        grep -q "$metric_pattern"; then
        echo -e "${GREEN}✓ FOUND${NC}"
        return 0
    else
        echo -e "${RED}✗ NOT FOUND${NC}"
        return 1
    fi
}

check_metric "gnmic_interfaces_interface_state_counters" "OpenConfig interface counters"
check_metric "gnmic_interfaces_interface_state_oper_status" "OpenConfig interface status"
check_metric "gnmic_lldp_interfaces" "OpenConfig LLDP metrics"

echo ""

# Step 6: Compare OpenConfig vs Native paths
echo -e "${BLUE}Step 6: Comparing OpenConfig vs SR Linux native paths...${NC}"
echo ""

echo -e "${YELLOW}OpenConfig interface counters:${NC}"
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
    -u admin -p NokiaSrl1! --insecure \
    get --path "/interfaces/interface[name=ethernet-1/1]/state/counters/in-octets" 2>/dev/null | \
    grep -A 2 "in-octets" || echo "  (no data yet)"

echo ""
echo -e "${YELLOW}SR Linux native interface statistics:${NC}"
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
    -u admin -p NokiaSrl1! --insecure \
    get --path "/interface[name=ethernet-1/1]/statistics/in-octets" 2>/dev/null | \
    grep -A 2 "in-octets" || echo "  (no data yet)"

echo ""

# Step 7: Check Prometheus has OpenConfig metrics
echo -e "${BLUE}Step 7: Verifying metrics in Prometheus...${NC}"
echo ""

echo -n "  Querying Prometheus for OpenConfig metrics... "
if docker exec clab-gnmi-clos-prometheus wget -q -O - \
    'http://localhost:9090/api/v1/query?query=gnmic_interfaces_interface_state_counters_in_octets' 2>/dev/null | \
    grep -q "success"; then
    echo -e "${GREEN}✓ SUCCESS${NC}"
else
    echo -e "${YELLOW}⚠ No data yet (may need more time)${NC}"
fi

echo ""

# Step 8: Show sample OpenConfig data
echo -e "${BLUE}Step 8: Sample OpenConfig telemetry data...${NC}"
echo ""

echo -e "${YELLOW}Interface operational status (OpenConfig):${NC}"
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
    -u admin -p NokiaSrl1! --insecure \
    get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status" 2>/dev/null | \
    grep -A 5 "oper-status" || echo "  (no data)"

echo ""
echo -e "${YELLOW}LLDP neighbors (OpenConfig):${NC}"
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
    -u admin -p NokiaSrl1! --insecure \
    get --path "/lldp/interfaces/interface[name=ethernet-1/1]/neighbors" 2>/dev/null | \
    head -20 || echo "  (no neighbors yet)"

echo ""

# Step 9: Check gNMIc logs for errors
echo -e "${BLUE}Step 9: Checking gNMIc logs for errors...${NC}"
echo ""

echo -e "${YELLOW}Recent gNMIc log entries:${NC}"
docker logs clab-gnmi-clos-gnmic 2>&1 | tail -10

echo ""

# Summary
echo -e "${BLUE}=========================================="
echo "Test Summary"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ OpenConfig paths tested on SR Linux${NC}"
echo -e "${GREEN}✓ Streaming subscriptions validated${NC}"
echo -e "${GREEN}✓ Metrics available in Prometheus format${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. View metrics: docker exec clab-gnmi-clos-gnmic wget -q -O - http://localhost:9273/metrics | grep gnmic_interfaces"
echo "2. Check Prometheus: curl 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interfaces_interface_state_counters_in_octets'"
echo "3. View Grafana: http://localhost:3000 (admin/admin)"
echo "4. Run detailed test: ./monitoring/test-openconfig-telemetry.sh"
echo ""
echo -e "${BLUE}Configuration files:${NC}"
echo "- gNMIc config: monitoring/gnmic/gnmic-config.yml"
echo "- OpenConfig guide: monitoring/OPENCONFIG-TELEMETRY-GUIDE.md"
echo "- Multi-vendor summary: monitoring/TELEMETRY-MULTI-VENDOR-SUMMARY.md"
echo ""
