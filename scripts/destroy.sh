#!/bin/bash
# ContainerLab destroy script

set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Destroying topology...${NC}"
containerlab destroy -t ../topology.yml --cleanup

echo -e "${GREEN}Topology destroyed!${NC}"
