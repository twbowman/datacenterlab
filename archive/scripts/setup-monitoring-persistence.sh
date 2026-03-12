#!/bin/bash
# Setup persistent storage for monitoring tools

set -e

echo "Setting up monitoring data persistence..."

# Create directories for persistent data
mkdir -p monitoring/grafana/data
mkdir -p monitoring/prometheus/data

# Set proper permissions
# Grafana runs as user 472
echo "Setting Grafana permissions (user 472)..."
sudo chown -R 472:472 monitoring/grafana/data

# Prometheus runs as user 65534 (nobody)
echo "Setting Prometheus permissions (user 65534)..."
sudo chown -R 65534:65534 monitoring/prometheus/data

echo ""
echo "✅ Monitoring persistence directories created:"
echo "   - monitoring/grafana/data"
echo "   - monitoring/prometheus/data"
echo ""
echo "Next steps:"
echo "1. Update topology.yml to add these binds:"
echo ""
echo "   grafana:"
echo "     binds:"
echo "       - ./monitoring/grafana/data:/var/lib/grafana"
echo ""
echo "   prometheus:"
echo "     binds:"
echo "       - ./monitoring/prometheus/data:/prometheus"
echo ""
echo "2. Redeploy the lab: ./destroy.sh && ./deploy.sh"
echo ""
echo "Your monitoring data will now persist across lab reboots!"
