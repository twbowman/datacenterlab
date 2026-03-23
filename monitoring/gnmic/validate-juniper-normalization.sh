#!/bin/bash

# Juniper Metric Normalization Validation Script
# Task 15.4: Configure Juniper metric normalization
# Requirements: 4.1, 4.2, 4.3

set -e

echo "========================================="
echo "Juniper Metric Normalization Validation"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
}

info() {
    echo -e "ℹ INFO: $1"
}

# Check if Prometheus is accessible
echo "1. Checking Prometheus connectivity..."
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    pass "Prometheus is accessible at http://localhost:9090"
else
    fail "Prometheus is not accessible at http://localhost:9090"
    echo "   Make sure Prometheus is running: docker ps | grep prometheus"
    exit 1
fi
echo ""

# Check if gNMIc metrics endpoint is accessible
echo "2. Checking gNMIc metrics endpoint..."
if curl -s http://localhost:9273/metrics > /dev/null 2>&1; then
    pass "gNMIc metrics endpoint is accessible at http://localhost:9273"
else
    fail "gNMIc metrics endpoint is not accessible at http://localhost:9273"
    echo "   Make sure gNMIc is running: docker ps | grep gnmic"
    exit 1
fi
echo ""

# Check for normalized interface metrics from Juniper
echo "3. Checking normalized interface metrics (network_interface_*)..."
INTERFACE_METRICS=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="juniper"}' | jq -r '.data.result | length')
if [ "$INTERFACE_METRICS" -gt 0 ]; then
    pass "Found $INTERFACE_METRICS normalized interface metrics from Juniper devices"
    info "Sample query: network_interface_in_octets{vendor=\"juniper\"}"
else
    warn "No normalized interface metrics found from Juniper devices"
    info "This is expected if no Juniper devices are deployed yet"
    info "Deploy Juniper devices to test: sudo containerlab deploy -t topology-srlinux.yml"
fi
echo ""

# Check for normalized BGP metrics from Juniper
echo "4. Checking normalized BGP metrics (network_bgp_*)..."
BGP_METRICS=$(curl -s 'http://localhost:9090/api/v1/query?query=network_bgp_session_state{vendor="juniper"}' | jq -r '.data.result | length')
if [ "$BGP_METRICS" -gt 0 ]; then
    pass "Found $BGP_METRICS normalized BGP metrics from Juniper devices"
    info "Sample query: network_bgp_session_state{vendor=\"juniper\"}"
else
    warn "No normalized BGP metrics found from Juniper devices"
    info "This is expected if no Juniper devices are deployed or BGP is not configured"
fi
echo ""

# Check interface name normalization (ge-0/0/0 -> eth0_0_0)
echo "5. Checking interface name normalization..."
RAW_JUNIPER_INTERFACES=$(curl -s http://localhost:9273/metrics | grep 'network_interface_in_octets.*juniper' | grep -c 'interface="ge-' || true)
NORMALIZED_JUNIPER_INTERFACES=$(curl -s http://localhost:9273/metrics | grep 'network_interface_in_octets.*juniper' | grep -c 'interface="eth' || true)

if [ "$RAW_JUNIPER_INTERFACES" -gt 0 ]; then
    fail "Found $RAW_JUNIPER_INTERFACES Juniper interfaces with non-normalized names (ge-0/0/0)"
    info "Interface names should be normalized to eth0_0_0 format"
elif [ "$NORMALIZED_JUNIPER_INTERFACES" -gt 0 ]; then
    pass "Found $NORMALIZED_JUNIPER_INTERFACES Juniper interfaces with normalized names (eth0_0_0)"
    info "Example: ge-0/0/0 -> eth0_0_0, ge-0/0/47 -> eth0_0_47"
else
    warn "No Juniper interface metrics found to validate normalization"
    info "Deploy Juniper devices to test interface name normalization"
fi
echo ""

# Check vendor tags
echo "6. Checking vendor tags (vendor=juniper, os=junos)..."
VENDOR_TAG_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="juniper"}' | jq -r '.data.result | length')
OS_TAG_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{os="junos"}' | jq -r '.data.result | length')

if [ "$VENDOR_TAG_COUNT" -gt 0 ] && [ "$OS_TAG_COUNT" -gt 0 ]; then
    pass "Vendor tags present: vendor=juniper ($VENDOR_TAG_COUNT metrics), os=junos ($OS_TAG_COUNT metrics)"
else
    warn "Vendor tags not found on Juniper metrics"
    info "This is expected if no Juniper devices are deployed"
fi
echo ""

# Check universal metric tag
echo "7. Checking universal_metric tag..."
UNIVERSAL_TAG_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="juniper",universal_metric="true"}' | jq -r '.data.result | length')
if [ "$UNIVERSAL_TAG_COUNT" -gt 0 ]; then
    pass "Universal metric tag present on $UNIVERSAL_TAG_COUNT Juniper metrics"
else
    warn "Universal metric tag not found on Juniper metrics"
    info "This is expected if no Juniper devices are deployed"
fi
echo ""

# Check cross-vendor consistency
echo "8. Checking cross-vendor metric consistency..."
NOKIA_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="nokia"}' | jq -r '.data.result | length')
ARISTA_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="arista"}' | jq -r '.data.result | length')
SONIC_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="dellemc"}' | jq -r '.data.result | length')
JUNIPER_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="juniper"}' | jq -r '.data.result | length')

info "Metrics by vendor:"
info "  - Nokia (SR Linux): $NOKIA_COUNT metrics"
info "  - Arista (EOS): $ARISTA_COUNT metrics"
info "  - Dell EMC (SONiC): $SONIC_COUNT metrics"
info "  - Juniper (Junos): $JUNIPER_COUNT metrics"

TOTAL_VENDORS=0
[ "$NOKIA_COUNT" -gt 0 ] && ((TOTAL_VENDORS++))
[ "$ARISTA_COUNT" -gt 0 ] && ((TOTAL_VENDORS++))
[ "$SONIC_COUNT" -gt 0 ] && ((TOTAL_VENDORS++))
[ "$JUNIPER_COUNT" -gt 0 ] && ((TOTAL_VENDORS++))

if [ "$TOTAL_VENDORS" -ge 2 ]; then
    pass "Multi-vendor normalization working ($TOTAL_VENDORS vendors reporting metrics)"
    info "Universal query works across all vendors: network_interface_in_octets"
else
    warn "Only $TOTAL_VENDORS vendor(s) reporting metrics"
    info "Deploy devices from multiple vendors to test cross-vendor consistency"
fi
echo ""

# Check that native Juniper paths are transformed
echo "9. Checking native Juniper path transformation..."
NATIVE_JUNIPER_PATHS=$(curl -s http://localhost:9273/metrics | grep -c '/junos/system/linecard/interface' || true)
if [ "$NATIVE_JUNIPER_PATHS" -gt 0 ]; then
    fail "Found $NATIVE_JUNIPER_PATHS metrics with non-transformed Juniper native paths"
    info "Native paths should be transformed to network_* format"
else
    pass "No untransformed Juniper native paths found"
    info "All Juniper paths are properly normalized"
fi
echo ""

# Check gNMIc processor configuration
echo "10. Checking gNMIc processor configuration..."
if grep -q "ge-(\\\\d+)/(\\\\d+)/(\\\\d+)" monitoring/gnmic/gnmic-config.yml; then
    pass "Juniper interface name normalization regex found in gnmic-config.yml"
else
    fail "Juniper interface name normalization regex NOT found in gnmic-config.yml"
    info "Expected regex: ^ge-(\\d+)/(\\d+)/(\\d+)$ -> eth\${1}_\${2}_\${3}"
fi

if grep -q "/junos/routing/bgp/neighbor" monitoring/gnmic/gnmic-config.yml; then
    pass "Juniper BGP path transformations found in gnmic-config.yml"
else
    fail "Juniper BGP path transformations NOT found in gnmic-config.yml"
    info "Expected paths: /junos/routing/bgp/neighbor/*"
fi

if grep -q 'contains(source, "juniper")' monitoring/gnmic/gnmic-config.yml; then
    pass "Juniper vendor detection found in gnmic-config.yml"
else
    fail "Juniper vendor detection NOT found in gnmic-config.yml"
    info "Expected condition: contains(source, \"juniper\") || contains(source, \"junos\")"
fi
echo ""

# Test universal query
echo "11. Testing universal query across all vendors..."
UNIVERSAL_QUERY_RESULT=$(curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets' | jq -r '.data.result | length')
if [ "$UNIVERSAL_QUERY_RESULT" -gt 0 ]; then
    pass "Universal query returns $UNIVERSAL_QUERY_RESULT metrics across all vendors"
    info "Query: network_interface_in_octets"
    info "This query works identically for Nokia, Arista, SONiC, and Juniper"
else
    warn "Universal query returned no results"
    info "Deploy devices to test universal queries"
fi
echo ""

# Summary
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Juniper metric normalization is properly configured."
    echo ""
    echo "Next steps:"
    echo "  1. Deploy Juniper devices to test normalization"
    echo "  2. Verify metrics appear in Prometheus"
    echo "  3. Test universal Grafana queries"
    echo "  4. Create cross-vendor dashboards"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please review the failures above and fix the configuration."
    echo "See monitoring/gnmic/JUNIPER-NORMALIZATION.md for troubleshooting."
    exit 1
fi
