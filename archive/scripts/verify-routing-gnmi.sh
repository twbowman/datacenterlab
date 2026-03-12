#!/bin/bash

# Script to verify routing using gNMI protocol
# Requires: gnmic tool (https://gnmic.openconfig.net/)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gnmic is installed
if ! command -v gnmic &> /dev/null; then
    echo -e "${RED}Error: gnmic is not installed${NC}"
    echo "Install with: bash -c \"\$(curl -sL https://get-gnmic.openconfig.net)\""
    exit 1
fi

# SR Linux switches
SWITCHES=("spine1" "spine2" "leaf1" "leaf2" "leaf3" "leaf4")
MGMT_IPS=("172.20.20.10" "172.20.20.11" "172.20.20.21" "172.20.20.22" "172.20.20.23" "172.20.20.24")

# Default credentials for SR Linux
USERNAME="admin"
PASSWORD="NokiaSrl1!"
GNMI_PORT="57400"  # Using default mgmt port with TLS

echo "=========================================="
echo "gNMI Routing Verification Script"
echo "=========================================="
echo ""

# Function to check interface status via gNMI
check_interfaces() {
    local switch=$1
    local ip=$2
    
    echo -e "${BLUE}[${switch}] Checking interface status...${NC}"
    
    gnmic -a ${ip}:${GNMI_PORT} \
        --username ${USERNAME} \
        --password ${PASSWORD} \
        --skip-verify \
        --encoding json_ietf \
        get --path /interface[name=ethernet-*]/oper-state \
        --format flat 2>/dev/null | grep -v "^$" || echo -e "${RED}Failed to get interfaces${NC}"
    
    echo ""
}

# Function to check BGP neighbors via gNMI
check_bgp_neighbors() {
    local switch=$1
    local ip=$2
    
    echo -e "${BLUE}[${switch}] Checking BGP neighbors...${NC}"
    
    gnmic -a ${ip}:${GNMI_PORT} \
        --username ${USERNAME} \
        --password ${PASSWORD} \
        --skip-verify \
        --encoding json_ietf \
        get --path /network-instance[name=default]/protocols/bgp/neighbor \
        --format flat 2>/dev/null | grep -E "(peer-address|session-state|peer-as)" || echo -e "${RED}No BGP neighbors found${NC}"
    
    echo ""
}

# Function to check routing table via gNMI
check_routing_table() {
    local switch=$1
    local ip=$2
    
    echo -e "${BLUE}[${switch}] Checking IPv4 routing table...${NC}"
    
    gnmic -a ${ip}:${GNMI_PORT} \
        --username ${USERNAME} \
        --password ${PASSWORD} \
        --skip-verify \
        --encoding json_ietf \
        get --path /network-instance[name=default]/route-table/ipv4-unicast/route \
        --format flat 2>/dev/null | head -20 || echo -e "${RED}Failed to get routing table${NC}"
    
    echo ""
}

# Function to check loopback interfaces
check_loopbacks() {
    local switch=$1
    local ip=$2
    
    echo -e "${BLUE}[${switch}] Checking loopback interfaces...${NC}"
    
    gnmic -a ${ip}:${GNMI_PORT} \
        --username ${USERNAME} \
        --password ${PASSWORD} \
        --skip-verify \
        --encoding json_ietf \
        get --path /interface[name=system0]/subinterface[index=0]/ipv4/address \
        --format flat 2>/dev/null | grep -v "^$" || echo -e "${RED}No loopback addresses found${NC}"
    
    echo ""
}

# Function to get BGP summary
check_bgp_summary() {
    local switch=$1
    local ip=$2
    
    echo -e "${BLUE}[${switch}] BGP Summary...${NC}"
    
    gnmic -a ${ip}:${GNMI_PORT} \
        --username ${USERNAME} \
        --password ${PASSWORD} \
        --skip-verify \
        --encoding json_ietf \
        get --path /network-instance[name=default]/protocols/bgp/statistics \
        --format flat 2>/dev/null | grep -v "^$" || echo -e "${RED}Failed to get BGP statistics${NC}"
    
    echo ""
}

# Main verification loop
for i in "${!SWITCHES[@]}"; do
    switch="${SWITCHES[$i]}"
    ip="${MGMT_IPS[$i]}"
    
    echo "=========================================="
    echo -e "${GREEN}Verifying ${switch} (${ip})${NC}"
    echo "=========================================="
    
    # Check if switch is reachable via gNMI
    if ! gnmic -a ${ip}:${GNMI_PORT} --username ${USERNAME} --password ${PASSWORD} --skip-verify --encoding json_ietf \
         get --path /system/information/version --format flat &>/dev/null; then
        echo -e "${RED}Switch ${switch} is not reachable via gNMI${NC}"
        echo ""
        continue
    fi
    
    # Run checks
    check_interfaces "${switch}" "${ip}"
    check_loopbacks "${switch}" "${ip}"
    check_bgp_neighbors "${switch}" "${ip}"
    check_bgp_summary "${switch}" "${ip}"
    check_routing_table "${switch}" "${ip}"
    
    echo ""
done

echo "=========================================="
echo -e "${GREEN}Verification Complete${NC}"
echo "=========================================="
