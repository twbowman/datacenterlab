#!/bin/bash
# ContainerLab destroy script
#
# Usage:
#   ./scripts/destroy.sh            # Destroy SR Linux (default)
#   ./scripts/destroy.sh srlinux    # Destroy SR Linux
#   ./scripts/destroy.sh sonic      # Destroy SONiC

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

VENDOR="${1:-srlinux}"

case "$VENDOR" in
    srlinux|sonic)
        ;;
    --help|-h)
        echo "Usage: $0 [VENDOR]"
        echo ""
        echo "Vendors:"
        echo "  srlinux    Destroy SR Linux topology (default)"
        echo "  sonic      Destroy SONiC topology"
        exit 0
        ;;
    *)
        echo -e "${RED}Unknown vendor: ${VENDOR}. Use 'srlinux' or 'sonic'.${NC}"
        exit 1
        ;;
esac

TOPOLOGY_FILE="../topology-${VENDOR}.yml"

if [ ! -f "$TOPOLOGY_FILE" ]; then
    echo -e "${RED}Topology file not found: ${TOPOLOGY_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}Destroying ${VENDOR} topology...${NC}"
containerlab destroy -t "$TOPOLOGY_FILE" --cleanup

echo -e "${GREEN}${VENDOR} topology destroyed!${NC}"
