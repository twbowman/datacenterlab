#!/bin/bash
# Multi-Vendor ContainerLab deployment script
# Supports SR Linux, Arista cEOS, SONiC, and Juniper devices

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TOPOLOGY_FILE="${1:-topology-multi-vendor.yml}"
VALIDATION_SCRIPT="scripts/validate-topology.py"

# Vendor-specific boot times (seconds)
BOOT_TIME_SRLINUX=60
BOOT_TIME_ARISTA=90
BOOT_TIME_SONIC=120
BOOT_TIME_JUNIPER=90
BOOT_TIME_LINUX=10

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to validate topology before deployment
validate_topology() {
    print_info "Validating topology definition..."
    
    if [ ! -f "$VALIDATION_SCRIPT" ]; then
        print_warning "Validation script not found, skipping validation"
        return 0
    fi
    
    if python3 "$VALIDATION_SCRIPT" "$TOPOLOGY_FILE"; then
        print_success "Topology validation passed"
        return 0
    else
        print_error "Topology validation failed"
        return 1
    fi
}

# Function to detect vendors in topology
detect_vendors() {
    print_info "Detecting vendors in topology..."
    
    local vendors=$(grep -E "kind: (nokia_srlinux|arista_ceos|sonic-vs|juniper_crpd)" "$TOPOLOGY_FILE" | \
                   sed -E 's/.*kind: (.*)/\1/' | sort -u)
    
    echo "$vendors"
}

# Function to calculate maximum boot time
calculate_boot_time() {
    local vendors="$1"
    local max_boot_time=0
    
    while IFS= read -r vendor; do
        case "$vendor" in
            nokia_srlinux)
                [ $BOOT_TIME_SRLINUX -gt $max_boot_time ] && max_boot_time=$BOOT_TIME_SRLINUX
                ;;
            arista_ceos)
                [ $BOOT_TIME_ARISTA -gt $max_boot_time ] && max_boot_time=$BOOT_TIME_ARISTA
                ;;
            sonic-vs)
                [ $BOOT_TIME_SONIC -gt $max_boot_time ] && max_boot_time=$BOOT_TIME_SONIC
                ;;
            juniper_crpd)
                [ $BOOT_TIME_JUNIPER -gt $max_boot_time ] && max_boot_time=$BOOT_TIME_JUNIPER
                ;;
        esac
    done <<< "$vendors"
    
    echo $max_boot_time
}

# Function to check if device is reachable via gNMI
check_gnmi_reachable() {
    local host=$1
    local port=${2:-57400}
    local timeout=5
    
    # Simple TCP connection check
    timeout $timeout bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null
    return $?
}

# Function to perform health checks on all devices
health_check_devices() {
    print_info "Performing health checks on deployed devices..."
    
    local lab_name=$(grep "^name:" "$TOPOLOGY_FILE" | awk '{print $2}')
    local failed_devices=()
    local checked_count=0
    local success_count=0
    
    # Get list of network devices (exclude linux clients)
    local devices=$(docker ps --filter "label=clab-node-kind" --filter "name=clab-${lab_name}" \
                   --format "{{.Names}}" | grep -v "client")
    
    for device in $devices; do
        checked_count=$((checked_count + 1))
        local device_name=$(echo "$device" | sed "s/clab-${lab_name}-//")
        
        # Get management IP
        local mgmt_ip=$(docker inspect "$device" | \
                       jq -r '.[0].NetworkSettings.Networks | to_entries[0].value.IPAddress')
        
        if [ -z "$mgmt_ip" ] || [ "$mgmt_ip" = "null" ]; then
            print_warning "Could not determine IP for $device_name"
            failed_devices+=("$device_name:no_ip")
            continue
        fi
        
        # Check if device is reachable
        if check_gnmi_reachable "$mgmt_ip" 57400; then
            print_success "$device_name ($mgmt_ip) is reachable"
            success_count=$((success_count + 1))
        else
            print_warning "$device_name ($mgmt_ip) is not yet reachable"
            failed_devices+=("$device_name:$mgmt_ip")
        fi
    done
    
    echo ""
    print_info "Health check summary: $success_count/$checked_count devices reachable"
    
    if [ ${#failed_devices[@]} -gt 0 ]; then
        print_warning "Some devices are not yet reachable (may still be booting):"
        for device in "${failed_devices[@]}"; do
            echo "  - $device"
        done
        return 1
    fi
    
    return 0
}

# Function to generate dynamic inventory with OS detection
generate_dynamic_inventory() {
    print_info "Generating dynamic inventory with OS detection..."
    
    local inventory_script="ansible/plugins/inventory/dynamic_inventory.py"
    local output_file="ansible/inventory-dynamic.yml"
    
    if [ ! -f "$inventory_script" ]; then
        print_error "Dynamic inventory script not found: $inventory_script"
        return 1
    fi
    
    # Make script executable
    chmod +x "$inventory_script"
    
    # Generate inventory
    if python3 "$inventory_script" -t "$TOPOLOGY_FILE" -o "$output_file" 2>&1 | while read line; do
        echo "  $line"
    done; then
        print_success "Dynamic inventory generated: $output_file"
        return 0
    else
        print_error "Failed to generate dynamic inventory"
        return 1
    fi
}

# Function to verify OS detection
verify_os_detection() {
    print_info "Verifying OS detection for all devices..."
    
    local inventory_file="ansible/inventory-dynamic.yml"
    
    if [ ! -f "$inventory_file" ]; then
        print_warning "Dynamic inventory not found, skipping verification"
        return 1
    fi
    
    # Count devices with detected OS
    local total_devices=$(grep -c "ansible_network_os:" "$inventory_file" || echo "0")
    local unknown_devices=$(grep -c "ansible_network_os: unknown" "$inventory_file" || echo "0")
    local detected_devices=$((total_devices - unknown_devices))
    
    if [ $total_devices -eq 0 ]; then
        print_warning "No devices found in dynamic inventory"
        return 1
    fi
    
    if [ $unknown_devices -gt 0 ]; then
        print_warning "OS detection incomplete: $detected_devices/$total_devices devices detected"
        print_warning "Devices with unknown OS may need manual configuration"
        return 1
    else
        print_success "OS detection complete: $detected_devices/$total_devices devices detected"
        return 0
    fi
}

# Function to display deployment summary
display_summary() {
    local lab_name=$(grep "^name:" "$TOPOLOGY_FILE" | awk '{print $2}')
    
    echo ""
    print_success "Deployment complete!"
    echo ""
    echo "Lab Name: $lab_name"
    echo ""
    echo "Access devices via gNMI (port 57400):"
    
    # List all network devices with their IPs
    docker ps --filter "label=clab-node-kind" --filter "name=clab-${lab_name}" \
              --format "{{.Names}}" | while read container; do
        local device_name=$(echo "$container" | sed "s/clab-${lab_name}-//")
        local mgmt_ip=$(docker inspect "$container" | \
                       jq -r '.[0].NetworkSettings.Networks | to_entries[0].value.IPAddress')
        local kind=$(docker inspect "$container" | jq -r '.[0].Config.Labels["clab-node-kind"]')
        
        printf "  %-20s %s:57400 (%s)\n" "$device_name" "$mgmt_ip" "$kind"
    done
    
    echo ""
    echo "Dynamic Inventory: ansible/inventory-dynamic.yml"
    echo ""
    echo "Next steps:"
    echo "  1. Configure devices with Ansible (using dynamic inventory):"
    echo "     ansible-playbook -i ansible/inventory-dynamic.yml ansible/site-multi-vendor.yml"
    echo ""
    echo "  2. View topology:"
    echo "     containerlab inspect -t $TOPOLOGY_FILE"
    echo ""
    echo "  3. Access device CLI:"
    echo "     docker exec -it clab-${lab_name}-<device-name> <cli-command>"
    echo ""
}

# Main deployment flow
main() {
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Multi-Vendor Network Lab Deployment          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check if topology file exists
    if [ ! -f "$TOPOLOGY_FILE" ]; then
        print_error "Topology file not found: $TOPOLOGY_FILE"
        echo "Usage: $0 [topology-file.yml]"
        exit 1
    fi
    
    print_info "Using topology file: $TOPOLOGY_FILE"
    echo ""
    
    # Step 1: Validate topology
    if ! validate_topology; then
        print_error "Deployment aborted due to validation errors"
        exit 1
    fi
    echo ""
    
    # Step 2: Detect vendors and calculate boot time
    vendors=$(detect_vendors)
    if [ -n "$vendors" ]; then
        print_info "Detected vendors:"
        echo "$vendors" | while read vendor; do
            echo "  - $vendor"
        done
        echo ""
    fi
    
    boot_time=$(calculate_boot_time "$vendors")
    print_info "Estimated boot time: ${boot_time}s"
    echo ""
    
    # Step 3: Deploy topology
    print_info "Deploying topology with ContainerLab..."
    if containerlab deploy -t "$TOPOLOGY_FILE"; then
        print_success "ContainerLab deployment successful"
    else
        print_error "ContainerLab deployment failed"
        exit 1
    fi
    echo ""
    
    # Step 4: Wait for devices to boot
    print_info "Waiting for devices to boot (${boot_time}s)..."
    for ((i=1; i<=boot_time; i++)); do
        printf "\r  Progress: [%-50s] %d%%" \
               $(printf '#%.0s' $(seq 1 $((i*50/boot_time)))) \
               $((i*100/boot_time))
        sleep 1
    done
    echo ""
    echo ""
    
    # Step 5: Health check devices
    if health_check_devices; then
        print_success "All devices passed health checks"
    else
        print_warning "Some devices failed health checks"
        print_info "Devices may still be booting. You can retry health checks with:"
        echo "  docker ps --filter label=clab-node-kind"
    fi
    echo ""
    
    # Step 6: Generate dynamic inventory with OS detection
    if generate_dynamic_inventory; then
        # Step 7: Verify OS detection
        verify_os_detection
    else
        print_error "Failed to generate dynamic inventory"
        print_info "You can manually generate it later with:"
        echo "  python3 ansible/plugins/inventory/dynamic_inventory.py -t $TOPOLOGY_FILE -o ansible/inventory-dynamic.yml"
    fi
    
    # Step 8: Display summary
    display_summary
}

# Run main function
main
