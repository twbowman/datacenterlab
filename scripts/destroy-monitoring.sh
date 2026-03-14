#!/bin/bash
# Destroy monitoring stack
# Run with: orb -m clab ./destroy-monitoring.sh

set -e

echo "=== Destroying Monitoring Stack ==="
containerlab destroy -t topology-monitoring.yml

echo ""
echo "Monitoring stack destroyed."
echo "Network lab (topology.yml) is unaffected."
