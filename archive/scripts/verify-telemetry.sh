#!/bin/bash

# Script to verify gNMI telemetry collection

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "gNMI Telemetry Verification"
echo "=========================================="
echo ""

# Check if gnmic container is running
echo -e "${BLUE}1. Checking gnmic container status...${NC}"
if docker ps --filter "name=clab-gnmi-clos-gnmic" --format "{{.Names}}" | grep -q gnmic; then
    echo -e "${GREEN}✓ gnmic container is running${NC}"
    CONTAINER_STATUS=$(docker ps --filter "name=clab-gnmi-clos-gnmic" --format "{{.Status}}")
    echo "  Status: $CONTAINER_STATUS"
else
    echo -e "${RED}✗ gnmic container is NOT running${NC}"
    echo "  Run: orb exec bash deploy-gnmic-collector.sh"
    exit 1
fi
echo ""

# Check gnmic logs for connection status
echo -e "${BLUE}2. Checking gnmic connection logs...${NC}"
LOGS=$(docker logs clab-gnmi-clos-gnmic 2>&1 | tail -20)

if echo "$LOGS" | grep -q "error\|failed\|Error"; then
    echo -e "${YELLOW}⚠ Found errors in logs:${NC}"
    echo "$LOGS" | grep -i "error\|failed" | tail -5
else
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
fi

if echo "$LOGS" | grep -q "subscription.*created\|connected"; then
    echo -e "${GREEN}✓ Subscriptions appear to be active${NC}"
fi
echo ""

# Check if gnmic is exposing metrics
echo -e "${BLUE}3. Checking gnmic Prometheus endpoint...${NC}"
METRICS=$(curl -s http://172.20.20.5:9273/metrics 2>/dev/null || echo "")

if [ -z "$METRICS" ]; then
    echo -e "${RED}✗ Cannot reach gnmic metrics endpoint${NC}"
    echo "  Trying localhost..."
    METRICS=$(curl -s http://localhost:9273/metrics 2>/dev/null || echo "")
fi

if [ -n "$METRICS" ]; then
    echo -e "${GREEN}✓ Metrics endpoint is accessible${NC}"
    
    # Count metrics
    TOTAL_METRICS=$(echo "$METRICS" | grep -c "^gnmi_" || echo "0")
    echo "  Total gnmi metrics: $TOTAL_METRICS"
    
    # Check for specific metric types
    if echo "$METRICS" | grep -q "gnmi_interface"; then
        INTERFACE_METRICS=$(echo "$METRICS" | grep -c "gnmi_interface" || echo "0")
        echo -e "  ${GREEN}✓ Interface metrics: $INTERFACE_METRICS${NC}"
    else
        echo -e "  ${YELLOW}⚠ No interface metrics found${NC}"
    fi
    
    if echo "$METRICS" | grep -q "gnmi.*bgp"; then
        BGP_METRICS=$(echo "$METRICS" | grep -c "gnmi.*bgp" || echo "0")
        echo -e "  ${GREEN}✓ BGP metrics: $BGP_METRICS${NC}"
    else
        echo -e "  ${YELLOW}⚠ No BGP metrics found${NC}"
    fi
    
    # Show sample metrics
    echo ""
    echo -e "${BLUE}Sample metrics:${NC}"
    echo "$METRICS" | grep "^gnmi_" | head -10
else
    echo -e "${RED}✗ No metrics available${NC}"
fi
echo ""

# Check if Prometheus is scraping gnmic
echo -e "${BLUE}4. Checking Prometheus scrape status...${NC}"
PROM_TARGETS=$(curl -s http://172.20.20.3:9090/api/v1/targets 2>/dev/null || curl -s http://localhost:9090/api/v1/targets 2>/dev/null || echo "")

if [ -n "$PROM_TARGETS" ]; then
    if echo "$PROM_TARGETS" | grep -q "gnmic"; then
        echo -e "${GREEN}✓ Prometheus is configured to scrape gnmic${NC}"
        
        # Check if target is up
        if echo "$PROM_TARGETS" | grep -q '"health":"up".*gnmic'; then
            echo -e "${GREEN}✓ gnmic target is UP in Prometheus${NC}"
        else
            echo -e "${YELLOW}⚠ gnmic target may be DOWN in Prometheus${NC}"
            echo "  Check: http://localhost:9090/targets"
        fi
    else
        echo -e "${YELLOW}⚠ Prometheus not configured to scrape gnmic${NC}"
        echo "  Update monitoring/prometheus/prometheus.yml"
    fi
else
    echo -e "${YELLOW}⚠ Cannot reach Prometheus API${NC}"
fi
echo ""

# Check for actual data in Prometheus
echo -e "${BLUE}5. Checking for telemetry data in Prometheus...${NC}"
QUERY_RESULT=$(curl -s "http://172.20.20.3:9090/api/v1/query?query=gnmi_interface_statistics_in_octets" 2>/dev/null || \
               curl -s "http://localhost:9090/api/v1/query?query=gnmi_interface_statistics_in_octets" 2>/dev/null || echo "")

if [ -n "$QUERY_RESULT" ]; then
    if echo "$QUERY_RESULT" | grep -q '"status":"success"'; then
        RESULT_COUNT=$(echo "$QUERY_RESULT" | grep -o '"result":\[' | wc -l)
        if [ "$RESULT_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ Telemetry data is available in Prometheus${NC}"
            
            # Extract sample data
            SAMPLE=$(echo "$QUERY_RESULT" | grep -o '"metric":{[^}]*}' | head -3)
            if [ -n "$SAMPLE" ]; then
                echo ""
                echo -e "${BLUE}Sample data points:${NC}"
                echo "$SAMPLE" | head -3
            fi
        else
            echo -e "${YELLOW}⚠ No data points found yet${NC}"
            echo "  Data may still be collecting. Wait 30 seconds and try again."
        fi
    else
        echo -e "${YELLOW}⚠ Query returned no results${NC}"
    fi
else
    echo -e "${RED}✗ Cannot query Prometheus${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Summary${NC}"
echo "=========================================="
echo ""
echo "To view live gnmic logs:"
echo "  docker logs -f clab-gnmi-clos-gnmic"
echo ""
echo "To view metrics directly:"
echo "  curl http://localhost:9273/metrics | grep gnmi"
echo ""
echo "To query in Prometheus:"
echo "  http://localhost:9090/graph"
echo "  Query: gnmi_interface_statistics_in_octets"
echo ""
echo "To view in Grafana:"
echo "  http://localhost:3000"
echo "  Username: admin / Password: admin"
echo ""
