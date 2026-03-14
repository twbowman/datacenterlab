#!/bin/bash
# Check monitoring stack status
# Run with: orb -m clab ./check-monitoring.sh

echo "=== Checking Monitoring Stack ==="
echo ""

echo "Grafana:"
docker ps --filter "name=clab-gnmi-clos-grafana" --format "  Status: {{.Status}}"
docker ps --filter "name=clab-gnmi-clos-grafana" --format "  Ports: {{.Ports}}"
echo ""

echo "Prometheus:"
docker ps --filter "name=clab-gnmi-clos-prometheus" --format "  Status: {{.Status}}"
docker ps --filter "name=clab-gnmi-clos-prometheus" --format "  Ports: {{.Ports}}"
echo ""

echo "gNMIc:"
docker ps --filter "name=clab-gnmi-clos-gnmic" --format "  Status: {{.Status}}"
docker ps --filter "name=clab-gnmi-clos-gnmic" --format "  Ports: {{.Ports}}"
echo ""

echo "=== Access URLs ==="
echo "Grafana:    http://172.20.20.2:3000 (admin/admin)"
echo "Prometheus: http://172.20.20.3:9090"
echo "gNMIc metrics: http://172.20.20.5:9273/metrics"
echo ""

echo "=== Testing gNMIc Metrics ==="
curl -s http://172.20.20.5:9273/metrics | head -20 || echo "gNMIc metrics not available"
