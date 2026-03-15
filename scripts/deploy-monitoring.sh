#!/bin/bash
# Deploy monitoring stack
# Run with: orb -m clab ./deploy-monitoring.sh

set -e

echo "=== Deploying Monitoring Stack ==="
echo ""

# Deploy monitoring topology
containerlab deploy -t ../topology-monitoring.yml

echo ""
echo "=== Monitoring Stack Deployed ==="
echo ""
echo "Access URLs:"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo "  Prometheus: http://localhost:9090"
echo "  gNMIc:      http://localhost:9273/metrics"
echo ""
echo "The monitoring stack will collect data from network devices at:"
echo "  spine1: 172.20.20.10:57400"
echo "  spine2: 172.20.20.11:57400"
echo "  leaf1:  172.20.20.21:57400"
echo "  leaf2:  172.20.20.22:57400"
echo "  leaf3:  172.20.20.23:57400"
echo "  leaf4:  172.20.20.24:57400"
echo ""
echo "Note: Network devices must be running for data collection to work."
