#!/bin/bash
# Multi-Vendor ContainerLab destroy script with cleanup verification
# shellcheck disable=SC2155

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TOPOLOGY_FILE="${1:-topology-multi-vendor.yml}"

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

# Function to verify cleanup
verify_cleanup() {
    local lab_name=$(grep "^name:" "$TOPOLOGY_FILE" | awk '{print $2}')
    local issues_found=0
    
    print_info "Verifying cleanup..."
    
    # Check for remaining containers
    local remaining_containers=$(docker ps -a --filter "name=clab-${lab_name}" --format "{{.Names}}" | wc -l)
    if [ "$remaining_containers" -gt 0 ]; then
        print_warning "Found $remaining_containers remaining containers:"
        docker ps -a --filter "name=clab-${lab_name}" --format "  - {{.Names}} ({{.Status}})"
        issues_found=$((issues_found + 1))
    else
        print_success "No remaining containers"
    fi
    
    # Check for remaining networks
    local remaining_networks=$(docker network ls --filter "name=clab-${lab_name}" --format "{{.Name}}" | wc -l)
    if [ "$remaining_networks" -gt 0 ]; then
        print_warning "Found $remaining_networks remaining networks:"
        docker network ls --filter "name=clab-${lab_name}" --format "  - {{.Name}}"
        issues_found=$((issues_found + 1))
    else
        print_success "No remaining networks"
    fi
    
    # Check for remaining volumes
    local remaining_volumes=$(docker volume ls --filter "name=clab-${lab_name}" --format "{{.Name}}" | wc -l)
    if [ "$remaining_volumes" -gt 0 ]; then
        print_warning "Found $remaining_volumes remaining volumes:"
        docker volume ls --filter "name=clab-${lab_name}" --format "  - {{.Name}}"
        issues_found=$((issues_found + 1))
    else
        print_success "No remaining volumes"
    fi
    
    echo ""
    
    if [ $issues_found -gt 0 ]; then
        print_warning "Cleanup verification found $issues_found issue(s)"
        print_info "To force cleanup, run:"
        echo "  docker rm -f \$(docker ps -aq --filter name=clab-${lab_name})"
        echo "  docker network rm \$(docker network ls --filter name=clab-${lab_name} -q)"
        echo "  docker volume rm \$(docker volume ls --filter name=clab-${lab_name} -q)"
        return 1
    else
        print_success "Cleanup verification passed - all resources removed"
        return 0
    fi
}

# Main destroy flow
main() {
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Multi-Vendor Network Lab Destruction         ║${NC}"
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
    
    # Get lab name for display
    local lab_name=$(grep "^name:" "$TOPOLOGY_FILE" | awk '{print $2}')
    print_info "Destroying lab: $lab_name"
    echo ""
    
    # Destroy topology
    print_info "Running ContainerLab destroy..."
    if containerlab destroy -t "$TOPOLOGY_FILE" --cleanup; then
        print_success "ContainerLab destroy completed"
    else
        print_error "ContainerLab destroy failed"
        exit 1
    fi
    echo ""
    
    # Verify cleanup
    if verify_cleanup; then
        echo ""
        print_success "Lab destroyed successfully!"
    else
        echo ""
        print_warning "Lab destroyed but cleanup verification found issues"
        exit 1
    fi
}

# Run main function
main
