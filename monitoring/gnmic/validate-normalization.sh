#!/bin/bash
#
# Validation script for SR Linux metric normalization
#
# This script validates that the gNMIc processors are correctly configured
# to normalize SR Linux metrics to universal OpenConfig-based names.
#
# Requirements: 4.1, 4.2, 4.3
#
# Usage:
#   ./validate-normalization.sh
#
# Prerequisites:
#   - gNMIc container must be running
#   - SR Linux devices must be streaming telemetry
#   - Prometheus must be scraping gNMIc

set -e

GNMIC_METRICS_URL="${GNMIC_METRICS_URL:-http://localhost:9273/metrics}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

echo "==================================================================="
echo "SR Linux Metric Normalization Validation"
echo "==================================================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check if a metric exists
check_metric_exists() {
    local metric_name=$1
    local description=$2
    
    echo -n "Testing: $description... "
    
    if curl -s "$GNMIC_METRICS_URL" | grep -q "^$metric_name"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected metric: $metric_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check if a label exists on a metric
check_metric_label() {
    local metric_name=$1
    local label_name=$2
    local label_value=$3
    local description=$4
    
    echo -n "Testing: $description... "
    
    if curl -s "$GNMIC_METRICS_URL" | grep "^$metric_name" | grep -q "$label_name=\"$label_value\""; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $metric_name{$label_name=\"$label_value\"}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check if old metric name is NOT present
check_metric_not_exists() {
    local metric_pattern=$1
    local description=$2
    
    echo -n "Testing: $description... "
    
    if curl -s "$GNMIC_METRICS_URL" | grep -q "$metric_pattern"; then
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Metric should not exist: $metric_pattern"
        ((TESTS_FAILED++))
        return 1
    else
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    fi
}

echo "-------------------------------------------------------------------"
echo "1. Interface Metric Normalization Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 1: Check normalized interface metrics exist
check_metric_exists "gnmic_oc_interface_stats_network_interface_in_octets" \
    "Interface in-octets normalized to network_interface_in_octets"

check_metric_exists "gnmic_oc_interface_stats_network_interface_out_octets" \
    "Interface out-octets normalized to network_interface_out_octets"

check_metric_exists "gnmic_oc_interface_stats_network_interface_in_packets" \
    "Interface in-packets normalized to network_interface_in_packets"

check_metric_exists "gnmic_oc_interface_stats_network_interface_out_packets" \
    "Interface out-packets normalized to network_interface_out_packets"

check_metric_exists "gnmic_oc_interface_stats_network_interface_in_errors" \
    "Interface in-errors normalized to network_interface_in_errors"

check_metric_exists "gnmic_oc_interface_stats_network_interface_out_errors" \
    "Interface out-errors normalized to network_interface_out_errors"

echo ""
echo "-------------------------------------------------------------------"
echo "2. Interface Label Normalization Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 2: Check interface name normalization (ethernet-1/1 -> eth1_1)
check_metric_label "gnmic_oc_interface_stats_network_interface_in_octets" \
    "interface" "eth1_1" \
    "Interface name normalized (ethernet-1/1 -> eth1_1)"

# Test 3: Check that old interface names are NOT present
echo -n "Testing: Old interface names removed (ethernet-X/Y format)... "
if curl -s "$GNMIC_METRICS_URL" | grep "gnmic_oc_interface_stats_network_interface" | grep -q 'interface="ethernet-'; then
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Found un-normalized interface names (ethernet-X/Y)"
    ((TESTS_FAILED++))
else
    echo -e "${GREEN}✓ PASS${NC}"
    ((TESTS_PASSED++))
fi

echo ""
echo "-------------------------------------------------------------------"
echo "3. BGP Metric Normalization Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 4: Check normalized BGP metrics exist
check_metric_exists "gnmic_srl_bgp_detailed_network_bgp_session_state" \
    "BGP session-state normalized to network_bgp_session_state"

check_metric_exists "gnmic_srl_bgp_detailed_network_bgp_peer_as" \
    "BGP peer-as normalized to network_bgp_peer_as"

echo ""
echo "-------------------------------------------------------------------"
echo "4. Vendor Label Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 5: Check vendor labels are added
check_metric_label "gnmic_oc_interface_stats_network_interface_in_octets" \
    "vendor" "nokia" \
    "Vendor label added (vendor=nokia)"

check_metric_label "gnmic_oc_interface_stats_network_interface_in_octets" \
    "os" "srlinux" \
    "OS label added (os=srlinux)"

echo ""
echo "-------------------------------------------------------------------"
echo "5. Universal Metric Label Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 6: Check universal_metric label
check_metric_label "gnmic_oc_interface_stats_network_interface_in_octets" \
    "universal_metric" "true" \
    "Universal metric label added (universal_metric=true)"

echo ""
echo "-------------------------------------------------------------------"
echo "6. Old Metric Name Removal Tests"
echo "-------------------------------------------------------------------"
echo ""

# Test 7: Verify old metric names are NOT present
check_metric_not_exists "/interface/statistics/in-octets" \
    "Old path /interface/statistics/in-octets removed"

check_metric_not_exists "/interface/statistics/out-octets" \
    "Old path /interface/statistics/out-octets removed"

check_metric_not_exists "/network-instance/protocols/bgp/neighbor/session-state" \
    "Old BGP path removed"

echo ""
echo "==================================================================="
echo "Validation Summary"
echo "==================================================================="
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation tests passed!${NC}"
    echo ""
    echo "SR Linux metric normalization is working correctly."
    echo "Metrics are being transformed to universal OpenConfig-based names."
    exit 0
else
    echo -e "${RED}✗ Some validation tests failed!${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check gNMIc logs: docker logs gnmic"
    echo "2. Verify processors are configured in gnmic-config.yml"
    echo "3. Restart gNMIc: docker restart gnmic"
    echo "4. Check raw metrics: curl $GNMIC_METRICS_URL"
    echo ""
    echo "See monitoring/METRIC-NORMALIZATION-GUIDE.md for more details."
    exit 1
fi
