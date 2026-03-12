#!/bin/bash
#
# Arista EOS Metric Normalization Validation Script
#
# Purpose: Validate that Arista metrics are properly normalized in gNMIc and Prometheus
# Requirements: 4.1, 4.2, 4.3
#
# Usage:
#   ./validate-arista-normalization.sh
#
# Prerequisites:
#   - gNMIc container running and collecting from Arista devices
#   - Prometheus container running and scraping gNMIc
#   - Arista devices configured with gNMI and OpenConfig enabled
#   - jq installed for JSON parsing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GNMIC_METRICS_URL="${GNMIC_METRICS_URL:-http://localhost:9273/metrics}"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST $TESTS_TOTAL: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO: $1${NC}"
}

# Test 1: Check gNMIc is running and exposing metrics
test_gnmic_running() {
    ((TESTS_TOTAL++))
    print_test "Verify gNMIc is running and exposing metrics"
    
    if curl -s -f "$GNMIC_METRICS_URL" > /dev/null 2>&1; then
        print_pass "gNMIc metrics endpoint is accessible at $GNMIC_METRICS_URL"
        return 0
    else
        print_fail "gNMIc metrics endpoint is not accessible at $GNMIC_METRICS_URL"
        return 1
    fi
}

# Test 2: Check Prometheus is running
test_prometheus_running() {
    ((TESTS_TOTAL++))
    print_test "Verify Prometheus is running"
    
    if curl -s -f "$PROMETHEUS_URL/api/v1/status/config" > /dev/null 2>&1; then
        print_pass "Prometheus is accessible at $PROMETHEUS_URL"
        return 0
    else
        print_fail "Prometheus is not accessible at $PROMETHEUS_URL"
        return 1
    fi
}

# Test 3: Check for Arista interface metrics
test_arista_interface_metrics() {
    ((TESTS_TOTAL++))
    print_test "Verify Arista interface metrics are normalized"
    
    # Query for normalized interface metrics from Arista
    QUERY='network_interface_in_octets{vendor="arista"}'
    RESULT=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result | length')
    
    if [ "$RESULT" -gt 0 ]; then
        print_pass "Found $RESULT normalized Arista interface metrics"
        
        # Show sample metric
        SAMPLE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[0].metric | to_entries | map("\(.key)=\(.value)") | join(", ")')
        print_info "Sample metric: $SAMPLE"
        return 0
    else
        print_fail "No normalized Arista interface metrics found"
        print_info "Check that Arista devices are added to gNMIc targets"
        return 1
    fi
}

# Test 4: Check interface name normalization
test_interface_name_normalization() {
    ((TESTS_TOTAL++))
    print_test "Verify Arista interface names are normalized (Ethernet1/1 -> eth1_1)"
    
    # Query for interface metrics and check label format
    QUERY='network_interface_in_octets{vendor="arista"}'
    INTERFACES=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[].metric.interface' | head -5)
    
    if [ -z "$INTERFACES" ]; then
        print_fail "No interface labels found in Arista metrics"
        return 1
    fi
    
    # Check if interfaces match normalized format (eth\d+_\d+)
    NORMALIZED_COUNT=0
    NON_NORMALIZED_COUNT=0
    
    while IFS= read -r interface; do
        if [[ "$interface" =~ ^eth[0-9]+_[0-9]+$ ]]; then
            ((NORMALIZED_COUNT++))
        else
            ((NON_NORMALIZED_COUNT++))
            print_info "Non-normalized interface found: $interface"
        fi
    done <<< "$INTERFACES"
    
    if [ "$NORMALIZED_COUNT" -gt 0 ] && [ "$NON_NORMALIZED_COUNT" -eq 0 ]; then
        print_pass "All $NORMALIZED_COUNT interface names are normalized (eth\d+_\d+)"
        print_info "Sample interfaces: $(echo "$INTERFACES" | head -3 | tr '\n' ', ' | sed 's/,$//')"
        return 0
    elif [ "$NORMALIZED_COUNT" -gt 0 ]; then
        print_fail "$NON_NORMALIZED_COUNT interface names are not normalized (expected: eth\d+_\d+)"
        return 1
    else
        print_fail "No normalized interface names found"
        return 1
    fi
}

# Test 5: Check BGP metrics normalization
test_bgp_metrics_normalization() {
    ((TESTS_TOTAL++))
    print_test "Verify Arista BGP metrics are normalized"
    
    # Query for normalized BGP metrics from Arista
    QUERY='network_bgp_session_state{vendor="arista"}'
    RESULT=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result | length')
    
    if [ "$RESULT" -gt 0 ]; then
        print_pass "Found $RESULT normalized Arista BGP session metrics"
        
        # Show BGP states
        STATES=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[].metric.state' | sort | uniq)
        print_info "BGP states found: $(echo "$STATES" | tr '\n' ', ' | sed 's/,$//')"
        return 0
    else
        print_fail "No normalized Arista BGP metrics found"
        print_info "Check that BGP is configured on Arista devices"
        return 1
    fi
}

# Test 6: Check BGP state value normalization
test_bgp_state_normalization() {
    ((TESTS_TOTAL++))
    print_test "Verify BGP state values are normalized to uppercase"
    
    # Query for BGP states
    QUERY='network_bgp_session_state{vendor="arista"}'
    STATES=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[].metric.state' | sort | uniq)
    
    if [ -z "$STATES" ]; then
        print_fail "No BGP state labels found"
        return 1
    fi
    
    # Check if all states are uppercase
    UPPERCASE_COUNT=0
    LOWERCASE_COUNT=0
    
    while IFS= read -r state; do
        if [[ "$state" =~ ^[A-Z]+$ ]]; then
            ((UPPERCASE_COUNT++))
        else
            ((LOWERCASE_COUNT++))
            print_info "Non-uppercase state found: $state"
        fi
    done <<< "$STATES"
    
    if [ "$UPPERCASE_COUNT" -gt 0 ] && [ "$LOWERCASE_COUNT" -eq 0 ]; then
        print_pass "All BGP state values are uppercase"
        return 0
    else
        print_fail "Some BGP state values are not uppercase"
        return 1
    fi
}

# Test 7: Check vendor tags are applied
test_vendor_tags() {
    ((TESTS_TOTAL++))
    print_test "Verify vendor tags are applied to Arista metrics"
    
    # Query for metrics with vendor=arista tag
    QUERY='network_interface_in_octets{vendor="arista"}'
    RESULT=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result | length')
    
    if [ "$RESULT" -gt 0 ]; then
        print_pass "Vendor tag 'arista' is applied to $RESULT metrics"
        
        # Check for os tag
        OS_TAG=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[0].metric.os')
        if [ "$OS_TAG" = "eos" ]; then
            print_pass "OS tag 'eos' is correctly applied"
        else
            print_fail "OS tag is not 'eos', found: $OS_TAG"
        fi
        return 0
    else
        print_fail "No metrics with vendor=arista tag found"
        return 1
    fi
}

# Test 8: Check universal_metric tag
test_universal_metric_tag() {
    ((TESTS_TOTAL++))
    print_test "Verify universal_metric tag is applied to normalized metrics"
    
    # Query for normalized metrics with universal_metric tag
    QUERY='network_interface_in_octets{vendor="arista",universal_metric="true"}'
    RESULT=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result | length')
    
    if [ "$RESULT" -gt 0 ]; then
        print_pass "Universal_metric tag is applied to $RESULT normalized metrics"
        return 0
    else
        print_fail "No metrics with universal_metric=true tag found"
        return 1
    fi
}

# Test 9: Test cross-vendor query compatibility
test_cross_vendor_query() {
    ((TESTS_TOTAL++))
    print_test "Verify cross-vendor queries work (SR Linux + Arista)"
    
    # Query for interface metrics from both vendors
    QUERY='network_interface_in_octets{interface="eth1_1"}'
    VENDORS=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[].metric.vendor' | sort | uniq)
    VENDOR_COUNT=$(echo "$VENDORS" | wc -l)
    
    if [ "$VENDOR_COUNT" -ge 2 ]; then
        print_pass "Cross-vendor query returns metrics from $VENDOR_COUNT vendors"
        print_info "Vendors: $(echo "$VENDORS" | tr '\n' ', ' | sed 's/,$//')"
        return 0
    elif [ "$VENDOR_COUNT" -eq 1 ]; then
        VENDOR=$(echo "$VENDORS" | head -1)
        print_fail "Cross-vendor query only returns metrics from 1 vendor: $VENDOR"
        print_info "Add more vendors to test cross-vendor compatibility"
        return 1
    else
        print_fail "Cross-vendor query returns no metrics"
        return 1
    fi
}

# Test 10: Check metric value preservation
test_metric_value_preservation() {
    ((TESTS_TOTAL++))
    print_test "Verify metric values are preserved during normalization"
    
    # Query for a specific metric and check it has a value
    QUERY='network_interface_in_octets{vendor="arista"}'
    VALUES=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$QUERY" | jq -r '.data.result[].value[1]' | head -5)
    
    if [ -z "$VALUES" ]; then
        print_fail "No metric values found"
        return 1
    fi
    
    # Check if values are numeric
    NUMERIC_COUNT=0
    NON_NUMERIC_COUNT=0
    
    while IFS= read -r value; do
        if [[ "$value" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
            ((NUMERIC_COUNT++))
        else
            ((NON_NUMERIC_COUNT++))
        fi
    done <<< "$VALUES"
    
    if [ "$NUMERIC_COUNT" -gt 0 ] && [ "$NON_NUMERIC_COUNT" -eq 0 ]; then
        print_pass "All metric values are numeric (preserved correctly)"
        return 0
    else
        print_fail "Some metric values are not numeric"
        return 1
    fi
}

# Main execution
main() {
    print_header "Arista EOS Metric Normalization Validation"
    
    echo "Configuration:"
    echo "  Prometheus URL: $PROMETHEUS_URL"
    echo "  gNMIc Metrics URL: $GNMIC_METRICS_URL"
    echo ""
    
    # Run all tests
    test_gnmic_running
    test_prometheus_running
    test_arista_interface_metrics
    test_interface_name_normalization
    test_bgp_metrics_normalization
    test_bgp_state_normalization
    test_vendor_tags
    test_universal_metric_tag
    test_cross_vendor_query
    test_metric_value_preservation
    
    # Print summary
    print_header "Test Summary"
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "\n${GREEN}✓ All tests passed! Arista normalization is working correctly.${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ Some tests failed. Review the output above for details.${NC}\n"
        exit 1
    fi
}

# Run main function
main
