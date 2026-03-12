#!/bin/bash
# Validation script for Prometheus vendor-specific relabeling rules
# Tests that vendor labels, device roles, and topology labels are correctly applied

set -e

echo "=========================================="
echo "Prometheus Vendor-Specific Relabeling Validation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prometheus endpoint
PROM_URL="http://localhost:9090"

# Function to check if Prometheus is running
check_prometheus() {
    echo "Checking Prometheus availability..."
    if curl -s "${PROM_URL}/-/healthy" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Prometheus is running"
        return 0
    else
        echo -e "${RED}✗${NC} Prometheus is not accessible at ${PROM_URL}"
        echo "Please ensure Prometheus is running"
        return 1
    fi
}

# Function to query Prometheus
query_prometheus() {
    local query="$1"
    curl -s -G "${PROM_URL}/api/v1/query" --data-urlencode "query=${query}" | jq -r '.data.result'
}

# Function to check if a label exists on metrics
check_label_exists() {
    local metric_name="$1"
    local label_name="$2"
    local expected_values="$3"
    
    echo ""
    echo "Checking label '${label_name}' on metric '${metric_name}'..."
    
    # Query for metrics with the label
    local result=$(query_prometheus "${metric_name}")
    
    if [ -z "$result" ] || [ "$result" == "[]" ]; then
        echo -e "${YELLOW}⚠${NC} No metrics found for ${metric_name}"
        return 1
    fi
    
    # Extract unique label values
    local label_values=$(echo "$result" | jq -r ".[].metric.${label_name}" | sort -u | grep -v "^null$" || true)
    
    if [ -z "$label_values" ]; then
        echo -e "${RED}✗${NC} Label '${label_name}' not found on ${metric_name}"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} Label '${label_name}' found with values:"
    echo "$label_values" | sed 's/^/  - /'
    
    # Check if expected values are present (if provided)
    if [ -n "$expected_values" ]; then
        for expected in $expected_values; do
            if echo "$label_values" | grep -q "^${expected}$"; then
                echo -e "${GREEN}✓${NC} Expected value '${expected}' found"
            else
                echo -e "${RED}✗${NC} Expected value '${expected}' NOT found"
                return 1
            fi
        done
    fi
    
    return 0
}

# Function to validate device role labels
validate_role_labels() {
    echo ""
    echo "=========================================="
    echo "Validating Device Role Labels"
    echo "=========================================="
    
    # Check for spine role
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "role" "spine leaf"
    
    # Verify spine devices have spine role
    echo ""
    echo "Verifying spine devices have 'spine' role..."
    local spine_result=$(query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source=~"spine.*"}')
    local spine_roles=$(echo "$spine_result" | jq -r '.[].metric.role' | sort -u)
    
    if echo "$spine_roles" | grep -q "^spine$"; then
        echo -e "${GREEN}✓${NC} Spine devices correctly labeled with role=spine"
    else
        echo -e "${RED}✗${NC} Spine devices not correctly labeled"
        return 1
    fi
    
    # Verify leaf devices have leaf role
    echo ""
    echo "Verifying leaf devices have 'leaf' role..."
    local leaf_result=$(query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source=~"leaf.*"}')
    local leaf_roles=$(echo "$leaf_result" | jq -r '.[].metric.role' | sort -u)
    
    if echo "$leaf_roles" | grep -q "^leaf$"; then
        echo -e "${GREEN}✓${NC} Leaf devices correctly labeled with role=leaf"
    else
        echo -e "${RED}✗${NC} Leaf devices not correctly labeled"
        return 1
    fi
}

# Function to validate vendor labels
validate_vendor_labels() {
    echo ""
    echo "=========================================="
    echo "Validating Vendor Labels"
    echo "=========================================="
    
    # Check for vendor label (preserved from gNMIc)
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "vendor" ""
    
    # Check for os label (preserved from gNMIc)
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "os" ""
}

# Function to validate topology labels
validate_topology_labels() {
    echo ""
    echo "=========================================="
    echo "Validating Topology Labels"
    echo "=========================================="
    
    # Check for topology label
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "topology" "gnmi-clos"
    
    # Check for fabric_type label
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "fabric_type" "clos"
    
    # Check for layer label
    check_label_exists "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets" "layer" "layer3 layer2_layer3"
}

# Function to validate label combinations
validate_label_combinations() {
    echo ""
    echo "=========================================="
    echo "Validating Label Combinations"
    echo "=========================================="
    
    # Check that spine devices have layer3 label
    echo ""
    echo "Checking spine devices have layer=layer3..."
    local spine_layer=$(query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role="spine"}')
    local spine_layer_values=$(echo "$spine_layer" | jq -r '.[].metric.layer' | sort -u)
    
    if echo "$spine_layer_values" | grep -q "^layer3$"; then
        echo -e "${GREEN}✓${NC} Spine devices correctly labeled with layer=layer3"
    else
        echo -e "${RED}✗${NC} Spine devices not correctly labeled with layer=layer3"
        return 1
    fi
    
    # Check that leaf devices have layer2_layer3 label
    echo ""
    echo "Checking leaf devices have layer=layer2_layer3..."
    local leaf_layer=$(query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role="leaf"}')
    local leaf_layer_values=$(echo "$leaf_layer" | jq -r '.[].metric.layer' | sort -u)
    
    if echo "$leaf_layer_values" | grep -q "^layer2_layer3$"; then
        echo -e "${GREEN}✓${NC} Leaf devices correctly labeled with layer=layer2_layer3"
    else
        echo -e "${RED}✗${NC} Leaf devices not correctly labeled with layer=layer2_layer3"
        return 1
    fi
    
    # Check that all devices with role have fabric_type=clos
    echo ""
    echo "Checking all devices with role have fabric_type=clos..."
    local fabric_result=$(query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role=~"spine|leaf"}')
    local fabric_types=$(echo "$fabric_result" | jq -r '.[].metric.fabric_type' | sort -u)
    
    if echo "$fabric_types" | grep -q "^clos$"; then
        echo -e "${GREEN}✓${NC} All devices correctly labeled with fabric_type=clos"
    else
        echo -e "${RED}✗${NC} Not all devices labeled with fabric_type=clos"
        return 1
    fi
}

# Function to display sample metrics with all labels
display_sample_metrics() {
    echo ""
    echo "=========================================="
    echo "Sample Metrics with All Labels"
    echo "=========================================="
    
    echo ""
    echo "Sample spine metric:"
    query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="spine1"}' | jq -r '.[0].metric' | jq '.'
    
    echo ""
    echo "Sample leaf metric:"
    query_prometheus 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="leaf1"}' | jq -r '.[0].metric' | jq '.'
}

# Main execution
main() {
    if ! check_prometheus; then
        exit 1
    fi
    
    local failed=0
    
    validate_vendor_labels || failed=1
    validate_role_labels || failed=1
    validate_topology_labels || failed=1
    validate_label_combinations || failed=1
    display_sample_metrics
    
    echo ""
    echo "=========================================="
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✓ All vendor-specific relabeling validations passed${NC}"
        echo "=========================================="
        exit 0
    else
        echo -e "${RED}✗ Some validations failed${NC}"
        echo "=========================================="
        exit 1
    fi
}

# Run main function
main
