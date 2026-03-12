#!/bin/bash

# Deploy gnmic as part of the ContainerLab topology
# gnmic is now defined in topology.yml

echo "Redeploying lab with gnmic collector..."

cd "$(dirname "$0")"

# Redeploy the lab
sudo containerlab deploy -t topology.yml --reconfigure

echo ""
echo "✅ gnmic collector deployed as part of the lab"
echo "   - Container: clab-gnmi-clos-gnmic"
echo "   - IP: 172.20.20.5"
echo "   - Metrics: http://localhost:9273/metrics"
echo ""
echo "To view logs: docker logs -f clab-gnmi-clos-gnmic"
echo "To check status: docker ps --filter name=gnmic"
