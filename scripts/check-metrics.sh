#!/bin/bash
# Check if monitoring metrics are available

set -e

echo "🔍 Checking monitoring stack and metrics..."
echo ""

# Check if Prometheus is running
if ! docker ps | grep -q "prometheus"; then
    echo "❌ Prometheus is not running"
    echo "Run: ./lab mon-start"
    exit 1
fi
echo "✅ Prometheus is running"

# Check if gNMIc is running
if ! docker ps | grep -q "gnmic"; then
    echo "❌ gNMIc is not running"
    echo "Run: ./lab mon-start"
    exit 1
fi
echo "✅ gNMIc is running"

# Check if gNMIc is exposing metrics
if ! curl -s http://172.20.20.5:9273/metrics > /dev/null 2>&1; then
    echo "❌ Cannot reach gNMIc metrics endpoint"
    echo "Check: curl http://172.20.20.5:9273/metrics"
    exit 1
fi
echo "✅ gNMIc metrics endpoint is accessible"

# Check if interface metrics exist
METRIC_COUNT=$(curl -s http://172.20.20.5:9273/metrics | grep -c "gnmic_interface_statistics_out_octets" || true)
if [ "$METRIC_COUNT" -eq 0 ]; then
    echo "⚠️  No interface metrics found yet"
    echo "Wait 1-2 minutes for gNMIc to collect data"
    echo "Or check if network lab is running: ./lab status"
    exit 1
fi
echo "✅ Interface metrics found ($METRIC_COUNT data points)"

# Check if Prometheus is scraping
PROM_TARGETS=$(curl -s 'http://172.20.20.3:9090/api/v1/targets' | grep -o '"health":"up"' | wc -l || true)
if [ "$PROM_TARGETS" -eq 0 ]; then
    echo "⚠️  Prometheus is not scraping any targets"
    echo "Check: http://172.20.20.3:9090/targets"
    exit 1
fi
echo "✅ Prometheus is scraping $PROM_TARGETS target(s)"

# Check if Prometheus has interface data
PROM_DATA=$(curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_statistics_out_octets' | grep -o '"result":\[' | wc -l || true)
if [ "$PROM_DATA" -eq 0 ]; then
    echo "⚠️  Prometheus has no interface data yet"
    echo "Wait 1-2 minutes for Prometheus to scrape gNMIc"
    exit 1
fi
echo "✅ Prometheus has interface data"

echo ""
echo "✅ All checks passed! Ready to analyze link utilization."
echo ""
echo "Run: ./lab analyze-links"
echo "Or:  python3 analyze-link-utilization.py"
