#!/bin/bash
# Test OpenConfig telemetry support across multiple vendors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test configuration
TIMEOUT=5

echo "=========================================="
echo "OpenConfig Telemetry Support Test"
echo "=========================================="
echo ""

# Function to test a path
test_path() {
    local device=$1
    local address=$2
    local username=$3
    local password=$4
    local path=$5
    local description=$6
    
    echo -n "Testing $description on $device... "
    
    if timeout $TIMEOUT gnmic -a "$address" -u "$username" -p "$password" --insecure \
        get --path "$path" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Function to test subscription
test_subscription() {
    local device=$1
    local address=$2
    local username=$3
    local password=$4
    local path=$5
    local description=$6
    
    echo -n "Testing subscription $description on $device... "
    
    if timeout $TIMEOUT gnmic -a "$address" -u "$username" -p "$password" --insecure \
        subscribe --path "$path" --mode stream --stream-mode sample --sample-interval 5s \
        --count 1 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# SR Linux Tests
echo "=========================================="
echo "Testing SR Linux (spine1)"
echo "=========================================="
DEVICE="spine1"
ADDRESS="clab-gnmi-clos-spine1:57400"
USERNAME="admin"
PASSWORD="NokiaSrl1!"

test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
    "/interfaces/interface[name=ethernet-1/1]/state/counters" \
    "OpenConfig Interface Counters"

test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
    "/interfaces/interface[name=ethernet-1/1]/state/oper-status" \
    "OpenConfig Interface Status"

test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
    "/lldp/interfaces" \
    "OpenConfig LLDP"

test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
    "/system/state" \
    "OpenConfig System State"

test_subscription "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
    "/interfaces/interface/state/counters" \
    "Interface Counters Stream"

echo ""

# Arista Tests (if available)
if [ -n "$TEST_ARISTA" ]; then
    echo "=========================================="
    echo "Testing Arista EOS (spine2)"
    echo "=========================================="
    DEVICE="spine2"
    ADDRESS="172.20.20.11:6030"
    USERNAME="admin"
    PASSWORD="admin"

    test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/interfaces/interface[name=Ethernet1]/state/counters" \
        "OpenConfig Interface Counters"

    test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/interfaces/interface[name=Ethernet1]/state/oper-status" \
        "OpenConfig Interface Status"

    test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/lldp/interfaces" \
        "OpenConfig LLDP"

    test_subscription "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/interfaces/interface/state/counters" \
        "Interface Counters Stream"

    echo ""
fi

# SONiC Tests (if available)
if [ -n "$TEST_SONIC" ]; then
    echo "=========================================="
    echo "Testing SONiC (leaf3)"
    echo "=========================================="
    DEVICE="leaf3"
    ADDRESS="172.20.20.23:8080"
    USERNAME="admin"
    PASSWORD="admin"

    test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/interfaces/interface[name=Ethernet0]/state/counters" \
        "OpenConfig Interface Counters"

    test_path "$DEVICE" "$ADDRESS" "$USERNAME" "$PASSWORD" \
        "/interfaces/interface[name=Ethernet0]/state/oper-status" \
        "OpenConfig Interface Status"

    echo ""
fi

# Detailed capability check
echo "=========================================="
echo "Checking OpenConfig Model Support"
echo "=========================================="

check_capabilities() {
    local device=$1
    local address=$2
    local username=$3
    local password=$4
    
    echo ""
    echo "Device: $device"
    echo "----------------------------------------"
    
    gnmic -a "$address" -u "$username" -p "$password" --insecure capabilities 2>/dev/null | \
        grep -i "openconfig" || echo "No OpenConfig models found"
}

check_capabilities "spine1" "clab-gnmi-clos-spine1:57400" "admin" "NokiaSrl1!"

if [ -n "$TEST_ARISTA" ]; then
    check_capabilities "spine2" "172.20.20.11:6030" "admin" "admin"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "To test Arista devices: TEST_ARISTA=1 $0"
echo "To test SONiC devices: TEST_SONIC=1 $0"
echo ""
