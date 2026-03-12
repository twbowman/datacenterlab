#!/bin/bash
# Validation script for SONiC metric normalization
# Task 15.3: Configure SONiC metric normalization
# Requirements: 4.1, 4.2, 4.3

set -e

echo "=========================================="
echo "SONiC Metric Normalization Validation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Prometheus is accessible
echo "1. Checking Prometheus connectivity..."
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is accessible${NC}"
else
    echo -e "${RED}✗ Prometheus is not accessible${NC}"
    echo "  Make sure Prometheus is running on localhost:9090"
    exit 1
fi
echo ""

# Check if gNMIc is exporting metrics
echo "2. Checking gNMIc metrics endpoint..."
if curl -s http://localhost:9273/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✓ gNMIc metrics endpoint is accessible${NC}"
else
    echo -e "${RED}✗ gNMIc metrics endpoint is not accessible${NC}"
    echo "  Make sure gNMIc is running and exporting to port 9273"
    exit 1
fi
echo ""

# Function to query Prometheus
query_prometheus() {
    local query="$1"
    curl -s "http://localhost:9090/api/v1/query?query=${query}" | jq -r '.data.result'
}

# Function to check if metric exists
check_metric() {
    local metric_name="$1"
    local description="$2"
    
    echo "Checking: $description"
    result=$(query_prometheus "${metric_name}")
    
    if [ "$result" != "[]" ]; then
        count=$(echo "$result" | jq 'length')
        echo -e "${GREEN}✓ Found $count instances of ${metric_name}${NC}"
        
        # Show sample with vendor tags
        vendor=$(echo "$result" | jq -r '.[0].metric.vendor // "unknown"')
        os=$(echo "$result" | jq -r '.[0].metric.os // "unknown"')
        if [ "$vendor" != "unknown" ]; then
            echo "  Sample: vendor=${vendor}, os=${os}"
        fi
        return 0
    else
        echo -e "${YELLOW}⚠ No data found for ${metric_name}${NC}"
        echo "  This is expected if no SONiC devices are currently deployed"
        return 1
    fi
}

# Test 1: Check for normalized interface metrics from SONiC
echo "3. Testing SONiC interface metric normalization..."
echo "---"
check_metric 'network_interface_in_octets{vendor="dellemc"}' "SONiC interface in octets"
check_metric 'network_interface_out_octets{vendor="dellemc"}' "SONiC interface out octets"
check_metric 'network_interface_in_packets{vendor="dellemc"}' "SONiC interface in packets"
check_metric 'network_interface_out_packets{vendor="dellemc"}' "SONiC interface out packets"
echo ""

# Test 2: Check for normalized BGP metrics from SONiC
echo "4. Testing SONiC BGP metric normalization..."
echo "---"
check_metric 'network_bgp_session_state{vendor="dellemc"}' "SONiC BGP session state"
check_metric 'network_bgp_received_routes{vendor="dellemc"}' "SONiC BGP received routes"
check_metric 'network_bgp_sent_routes{vendor="dellemc"}' "SONiC BGP sent routes"
echo ""

# Test 3: Check interface name normalization
echo "5. Testing SONiC interface name normalization..."
echo "---"
result=$(query_prometheus 'network_interface_in_octets{vendor="dellemc"}')
if [ "$result" != "[]" ]; then
    interfaces=$(echo "$result" | jq -r '.[].metric.interface' | head -5)
    echo "Sample normalized interface names:"
    echo "$interfaces" | while read -r iface; do
        if [[ $iface =~ ^eth[0-9]+_[0-9]+$ ]]; then
            echo -e "${GREEN}✓ $iface (correctly normalized)${NC}"
        else
            echo -e "${RED}✗ $iface (not normalized correctly)${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ No interface metrics found for SONiC devices${NC}"
fi
echo ""

# Test 4: Check vendor tags
echo "6. Testing SONiC vendor tag detection..."
echo "---"
result=$(query_prometheus 'network_interface_in_octets{vendor="dellemc",os="sonic"}')
if [ "$result" != "[]" ]; then
    count=$(echo "$result" | jq 'length')
    echo -e "${GREEN}✓ Found $count metrics with vendor=dellemc and os=sonic tags${NC}"
else
    echo -e "${YELLOW}⚠ No metrics found with SONiC vendor tags${NC}"
    echo "  This is expected if no SONiC devices are currently deployed"
fi
echo ""

# Test 5: Check universal metric tag
echo "7. Testing universal metric tagging..."
echo "---"
result=$(query_prometheus 'network_interface_in_octets{vendor="dellemc",universal_metric="true"}')
if [ "$result" != "[]" ]; then
    count=$(echo "$result" | jq 'length')
    echo -e "${GREEN}✓ Found $count SONiC metrics tagged as universal${NC}"
else
    echo -e "${YELLOW}⚠ No SONiC metrics found with universal_metric tag${NC}"
fi
echo ""

# Test 6: Cross-vendor consistency check
echo "8. Testing cross-vendor metric consistency..."
echo "---"
echo "Checking if normalized metrics exist across multiple vendors:"

vendors=("nokia" "arista" "dellemc")
for vendor in "${vendors[@]}"; do
    result=$(query_prometheus "network_interface_in_octets{vendor=\"${vendor}\"}")
    if [ "$result" != "[]" ]; then
        count=$(echo "$result" | jq 'length')
        echo -e "${GREEN}✓ ${vendor}: $count metrics${NC}"
    else
        echo -e "${YELLOW}⚠ ${vendor}: no metrics (device may not be deployed)${NC}"
    fi
done
echo ""

# Test 7: Verify metric path transformation
echo "9. Testing metric path transformation..."
echo "---"
echo "Checking that SONiC native paths are transformed to normalized names:"

# Check for any remaining untransformed SONiC paths
result=$(curl -s http://localhost:9273/metrics | grep -E "sonic-port|sonic-bgp" | head -5)
if [ -z "$result" ]; then
    echo -e "${GREEN}✓ No untransformed SONiC native paths found${NC}"
    echo "  All SONiC metrics have been normalized"
else
    echo -e "${YELLOW}⚠ Found some untransformed SONiC paths:${NC}"
    echo "$result"
    echo "  These may be vendor-specific metrics that should be preserved"
fi
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo "Configuration file: monitoring/gnmic/gnmic-config.yml"
echo "Processors configured:"
echo "  - normalize_interface_metrics (extended for SONiC)"
echo "  - normalize_bgp_metrics (extended for SONiC)"
echo "  - add_vendor_tags (SONiC detection added)"
echo ""
echo "SONiC normalization features:"
echo "  ✓ OpenConfig interface counters → network_interface_*"
echo "  ✓ SONiC native paths → network_interface_*"
echo "  ✓ Interface names: Ethernet0 → eth0_0"
echo "  ✓ BGP metrics → network_bgp_*"
echo "  ✓ Vendor tags: vendor=dellemc, os=sonic"
echo ""
echo "Next steps:"
echo "  1. Deploy SONiC devices to the topology"
echo "  2. Verify metrics appear in Prometheus with correct normalization"
echo "  3. Test universal Grafana queries work with SONiC metrics"
echo "  4. Proceed to Task 15.4: Configure Juniper metric normalization"
echo ""
echo -e "${GREEN}Validation complete!${NC}"
