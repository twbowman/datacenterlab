#!/bin/bash
#
# Integration Test Runner
#
# This script runs integration tests for the production network testing lab.
# It checks prerequisites and provides helpful output.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Production Network Testing Lab - Integration Tests"
echo "================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check if remote server is available (for macOS ARM)
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} remote server is installed"
else
    echo -e "${YELLOW}⚠${NC} remote server not found (required for macOS ARM)"
fi

# Check if containerlab is available
if sudo containerlab version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Containerlab is available"
else
    echo -e "${YELLOW}⚠${NC} Containerlab not available in remote server"
fi

# Check if Python dependencies are installed
if python3 -c "import pytest, requests, yaml" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${RED}✗${NC} Python dependencies missing"
    echo "  Install with: pip install -r requirements.txt"
    exit 1
fi

echo ""

# Check if lab is deployed
echo "Checking lab status..."
LAB_RUNNING=$(docker ps --filter name=clab-gnmi-clos --format '{{.Names}}' | wc -l)

if [ "$LAB_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Lab is running ($LAB_RUNNING containers)"
else
    echo -e "${YELLOW}⚠${NC} Lab is not running"
    echo "  Deploy with: sudo containerlab deploy -t topology.yml"
    echo "  Tests will attempt to deploy automatically"
fi

# Check if monitoring is deployed
MONITORING_RUNNING=$(docker ps --filter name=clab-monitoring --format '{{.Names}}' | wc -l)

if [ "$MONITORING_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Monitoring stack is running ($MONITORING_RUNNING containers)"
else
    echo -e "${YELLOW}⚠${NC} Monitoring stack is not running"
    echo "  Deploy with: sudo containerlab deploy -t topology-monitoring.yml"
    echo "  Tests will attempt to deploy automatically"
fi

echo ""
echo "================================================"
echo "Running Integration Tests"
echo "================================================"
echo ""

# Parse command line arguments
TEST_FILE=""
TEST_CLASS=""
TEST_METHOD=""
VERBOSE="-v -s"

if [ $# -gt 0 ]; then
    case "$1" in
        end-to-end)
            TEST_FILE="tests/integration/test_end_to_end.py"
            echo "Running end-to-end workflow tests..."
            ;;
        multi-vendor)
            TEST_FILE="tests/integration/test_multi_vendor.py"
            echo "Running multi-vendor integration tests..."
            ;;
        monitoring)
            TEST_FILE="tests/integration/test_monitoring_stack.py"
            echo "Running monitoring stack tests..."
            ;;
        all)
            TEST_FILE="tests/integration/"
            echo "Running all integration tests..."
            ;;
        *)
            echo "Usage: $0 [end-to-end|multi-vendor|monitoring|all]"
            echo ""
            echo "Options:"
            echo "  end-to-end   - Run end-to-end workflow tests"
            echo "  multi-vendor - Run multi-vendor integration tests"
            echo "  monitoring   - Run monitoring stack tests"
            echo "  all          - Run all integration tests (default)"
            echo ""
            exit 1
            ;;
    esac
else
    TEST_FILE="tests/integration/"
    echo "Running all integration tests..."
fi

echo ""

# Run tests
python3 -m pytest $TEST_FILE $VERBOSE

# Capture exit code
EXIT_CODE=$?

echo ""
echo "================================================"
echo "Test Results"
echo "================================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check lab status: docker ps"
    echo "  - Check device logs: docker logs clab-gnmi-clos-spine1"
    echo "  - Check monitoring logs: docker logs clab-monitoring-prometheus"
    echo "  - Review test output above for specific failures"
fi

exit $EXIT_CODE
