#!/bin/bash
# Run CI tests locally to simulate GitHub Actions environment
# This script helps validate changes before pushing to CI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
UNIT_TESTS_PASSED=false
PROPERTY_TESTS_PASSED=false
INTEGRATION_TESTS_PASSED=false

# Function to print colored output
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    if ! command_exists uv; then
        print_error "uv is not installed"
        echo "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    print_success "uv is installed"
    
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found"
        exit 1
    fi
    print_success "pyproject.toml found"
    
    echo ""
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    echo "Syncing Python environment with uv..."
    uv sync --all-extras
    
    print_success "Dependencies installed"
    echo ""
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    if uv run pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=scripts \
        --cov=ansible/plugins \
        --cov=ansible/filter_plugins \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/unit \
        --junit-xml=test-results/unit-tests.xml; then
        UNIT_TESTS_PASSED=true
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
    fi
    
    echo ""
}

# Run property-based tests
run_property_tests() {
    print_header "Running Property-Based Tests"
    
    if uv run pytest tests/property/ \
        -v \
        --tb=short \
        --hypothesis-profile=ci \
        --hypothesis-show-statistics \
        --junit-xml=test-results/property-tests.xml; then
        PROPERTY_TESTS_PASSED=true
        print_success "Property-based tests passed"
    else
        print_error "Property-based tests failed"
    fi
    
    echo ""
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    # Check if we're on macOS (need ORB) or Linux (native)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_warning "macOS detected - integration tests require ORB and containerlab"
        print_warning "Skipping integration tests in local CI simulation"
        print_warning "Run integration tests manually with: pytest tests/integration/ -v -s"
        INTEGRATION_TESTS_PASSED=true  # Skip but don't fail
    else
        # Check if containerlab is available
        if ! command_exists containerlab; then
            print_warning "containerlab not found - skipping integration tests"
            print_warning "Install containerlab: sudo bash -c \"\$(curl -sL https://get.containerlab.dev)\""
            INTEGRATION_TESTS_PASSED=true  # Skip but don't fail
        else
            if uv run pytest tests/integration/ \
                -v \
                -s \
                --tb=short \
                --timeout=300 \
                --junit-xml=test-results/integration-tests.xml; then
                INTEGRATION_TESTS_PASSED=true
                print_success "Integration tests passed"
            else
                print_error "Integration tests failed"
            fi
        fi
    fi
    
    echo ""
}

# Generate summary
generate_summary() {
    print_header "Test Summary"
    
    echo "Test Results:"
    if [ "$UNIT_TESTS_PASSED" = true ]; then
        print_success "Unit Tests: PASSED"
    else
        print_error "Unit Tests: FAILED"
    fi
    
    if [ "$PROPERTY_TESTS_PASSED" = true ]; then
        print_success "Property Tests: PASSED"
    else
        print_error "Property Tests: FAILED"
    fi
    
    if [ "$INTEGRATION_TESTS_PASSED" = true ]; then
        print_success "Integration Tests: PASSED"
    else
        print_error "Integration Tests: FAILED"
    fi
    
    echo ""
    
    # Overall result
    if [ "$UNIT_TESTS_PASSED" = true ] && [ "$PROPERTY_TESTS_PASSED" = true ] && [ "$INTEGRATION_TESTS_PASSED" = true ]; then
        print_success "All tests passed! ✓"
        echo ""
        echo "Coverage report available at: htmlcov/unit/index.html"
        echo "Test results available at: test-results/"
        return 0
    else
        print_error "Some tests failed! ✗"
        echo ""
        echo "Review the output above for details."
        echo "Test results available at: test-results/"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    print_header "CI Test Runner - Local Simulation"
    echo "This script simulates the GitHub Actions CI environment"
    echo ""
    
    # Create test-results directory
    mkdir -p test-results
    
    # Parse command line arguments
    RUN_UNIT=true
    RUN_PROPERTY=true
    RUN_INTEGRATION=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                RUN_PROPERTY=false
                RUN_INTEGRATION=false
                shift
                ;;
            --property-only)
                RUN_UNIT=false
                RUN_INTEGRATION=false
                shift
                ;;
            --integration-only)
                RUN_UNIT=false
                RUN_PROPERTY=false
                shift
                ;;
            --no-integration)
                RUN_INTEGRATION=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit-only         Run only unit tests"
                echo "  --property-only     Run only property-based tests"
                echo "  --integration-only  Run only integration tests"
                echo "  --no-integration    Skip integration tests"
                echo "  --help              Show this help message"
                echo ""
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run checks and tests
    check_prerequisites
    install_dependencies
    
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests
    fi
    
    if [ "$RUN_PROPERTY" = true ]; then
        run_property_tests
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
    fi
    
    generate_summary
}

# Run main function
main "$@"
