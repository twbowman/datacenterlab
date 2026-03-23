# Integration Tests

This directory contains integration tests for the production network testing lab. These tests validate end-to-end workflows, multi-vendor integration, and the monitoring stack.

## Overview

Integration tests verify that all components work together correctly in a real lab environment. Unlike unit tests that test individual components in isolation, integration tests:

- Deploy actual lab topologies
- Configure real network devices
- Collect and validate telemetry
- Test complete workflows from deployment to monitoring

## Test Structure

### Test Files

- **`test_end_to_end.py`**: Complete workflow tests (deploy → configure → validate → monitor)
- **`test_multi_vendor.py`**: Multi-vendor integration and interoperability tests
- **`test_monitoring_stack.py`**: Monitoring pipeline tests (gNMIc → Prometheus → Grafana)

### Test Categories

#### End-to-End Workflow Tests (Task 42.1)
Tests complete workflows with each vendor:
- Deployment verification
- Configuration with Ansible
- Validation checks
- Telemetry collection monitoring
- Configuration idempotency
- Error handling and rollback
- Performance benchmarks

**Validates: Requirements 15.1**

#### Multi-Vendor Integration Tests (Task 42.2)
Tests all vendor combinations and interoperability:
- Multi-vendor topology deployment
- OS detection for all vendors
- BGP sessions between different vendors
- LLDP discovery across vendors
- Telemetry collection from mixed vendors
- Metric normalization consistency
- Configuration dispatcher routing

**Validates: Requirements 15.6**

#### Monitoring Stack Integration Tests (Task 42.3)
Tests the complete monitoring pipeline:
- gNMIc collector operation
- Prometheus scraping and storage
- Grafana dashboard queries
- Metric flow from devices to dashboards
- Universal queries across vendors
- Metric persistence
- Health checks and reliability

**Validates: Requirements 15.1**

## Prerequisites

### Required Services

Integration tests require the following services to be running:

1. **Lab Topology**: Deployed via containerlab
   ```bash
   sudo containerlab deploy -t topology-srlinux.yml
   ```

2. **Monitoring Stack**: Deployed via containerlab
   ```bash
   sudo containerlab deploy -t topology-monitoring.yml
   ```

### Dependencies

- Python 3.8+
- pytest
- requests
- pyyaml
- remote server (for macOS ARM)
- Containerlab
- Docker

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Integration Tests

```bash
# From project root
pytest tests/integration/ -v -s
```

### Run Specific Test Files

```bash
# End-to-end workflow tests
pytest tests/integration/test_end_to_end.py -v -s

# Multi-vendor integration tests
pytest tests/integration/test_multi_vendor.py -v -s

# Monitoring stack tests
pytest tests/integration/test_monitoring_stack.py -v -s
```

### Run Specific Test Classes

```bash
# Test only end-to-end workflow
pytest tests/integration/test_end_to_end.py::TestEndToEndWorkflow -v -s

# Test only multi-vendor telemetry
pytest tests/integration/test_multi_vendor.py::TestMultiVendorTelemetry -v -s

# Test only monitoring pipeline
pytest tests/integration/test_monitoring_stack.py::TestEndToEndPipeline -v -s
```

### Run Specific Tests

```bash
# Test configuration idempotency
pytest tests/integration/test_end_to_end.py::TestEndToEndWorkflow::test_configuration_idempotency -v -s

# Test metric normalization
pytest tests/integration/test_multi_vendor.py::TestMultiVendorTelemetry::test_metric_normalization_across_vendors -v -s
```

## Test Fixtures

### Session-Scoped Fixtures

These fixtures are created once per test session and shared across all tests:

- **`lab_deployed`**: Deploys the lab topology (or uses existing deployment)
- **`monitoring_deployed`**: Deploys the monitoring stack (or uses existing deployment)

### Function-Scoped Fixtures

These fixtures are available to individual tests:

- **`lab_cmd`**: Returns commands run on remote server for command execution
- **`topology_config`**: Loads topology configuration
- **`device_list`**: Extracts list of devices from topology
- **`prometheus_url`**: Prometheus URL (http://localhost:9090)
- **`grafana_url`**: Grafana URL (http://localhost:3000)
- **`gnmic_url`**: gNMIc metrics endpoint URL (http://localhost:9273)
- **`wait_for_prometheus`**: Waits for Prometheus to be ready
- **`wait_for_grafana`**: Waits for Grafana to be ready

## Test Execution Flow

### Automatic Setup

1. Tests check if lab is already running
2. If not running, deploy lab topology
3. Wait for devices to be ready (30 seconds)
4. Deploy monitoring stack if needed
5. Wait for monitoring services (20 seconds)
6. Run tests

### Automatic Teardown

By default, the lab and monitoring stack are **NOT** destroyed after tests to allow inspection. To enable automatic cleanup, uncomment the teardown code in `conftest.py`.

### Manual Cleanup

```bash
# Destroy lab
sudo containerlab destroy -t topology.yml

# Destroy monitoring
sudo containerlab destroy -t topology-monitoring.yml
```

## Test Output

Tests use verbose output (`-s` flag) to show:
- Step-by-step progress
- Verification results (✓ for success, ⚠ for warnings)
- Metric counts and data
- Error messages and diagnostics

Example output:
```
=== Step 1: Verify Deployment ===
✓ Deployed devices: ['clab-gnmi-clos-spine1', 'clab-gnmi-clos-spine2', ...]

=== Step 2: Configure Devices ===
✓ Configuration playbook executed (return code: 0)

=== Step 3: Validate Configuration ===
✓ Device leaf1 is reachable and responding
✓ Device leaf2 is reachable and responding

=== Step 4: Monitor Telemetry Collection ===
✓ Found 24 interface metrics in Prometheus
✓ Collecting metrics from devices: {'spine1', 'spine2', 'leaf1', 'leaf2'}
```

## Troubleshooting

### Lab Not Deploying

If lab deployment fails:
1. Check Docker is running: `docker ps`
2. Check containerlab is installed: `sudo containerlab version`
3. Check for port conflicts: `sudo lsof -i :57400`
4. Review deployment logs

### Tests Timing Out

If tests timeout:
1. Increase wait times in `conftest.py`
2. Check device boot times: `docker logs clab-gnmi-clos-spine1`
3. Verify network connectivity
4. Check resource availability (CPU, memory)

### Metrics Not Available

If metrics are not available:
1. Check gNMIc is running: `docker ps | grep gnmic`
2. Check gNMIc logs: `docker logs <gnmic-container>`
3. Verify Prometheus is scraping: http://localhost:9090/targets
4. Check device gNMI service: `docker exec clab-gnmi-clos-spine1 sr_cli "show system gnmi-server"`

### Authentication Errors

If Grafana authentication fails:
- Default credentials: admin/admin
- Update credentials in test if changed
- Check Grafana logs: `docker logs clab-monitoring-grafana`

## Performance Considerations

### Test Duration

- Full integration test suite: ~5-10 minutes
- End-to-end tests: ~2-3 minutes
- Multi-vendor tests: ~2-3 minutes
- Monitoring stack tests: ~2-3 minutes

### Resource Usage

Integration tests require:
- CPU: 4+ cores recommended
- Memory: 8GB+ recommended
- Disk: 10GB+ for containers and metrics
- Network: Low latency for gNMI connections

### Optimization Tips

1. **Reuse Deployments**: Keep lab running between test runs
2. **Parallel Execution**: Use pytest-xdist for parallel tests
3. **Selective Testing**: Run only changed test files
4. **Reduce Wait Times**: Adjust timeouts based on your hardware

## CI/CD Integration

### GitHub Actions

Example workflow:
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Install containerlab
        run: |
          # Install containerlab
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v --tb=short
```

## Best Practices

### Writing Integration Tests

1. **Test Real Workflows**: Test actual user workflows, not just API calls
2. **Use Fixtures**: Leverage session-scoped fixtures for expensive setup
3. **Wait for Readiness**: Always wait for services to be ready before testing
4. **Check Multiple Aspects**: Verify functionality, performance, and error handling
5. **Provide Context**: Use descriptive print statements for debugging
6. **Handle Failures Gracefully**: Tests should not leave lab in broken state

### Test Organization

1. **Group Related Tests**: Use test classes to group related functionality
2. **Clear Test Names**: Use descriptive test method names
3. **Document Requirements**: Link tests to requirements with comments
4. **Independent Tests**: Tests should not depend on execution order
5. **Cleanup Resources**: Clean up any temporary resources created

## Requirements Validation

These integration tests validate the following requirements:

- **15.1**: Automated tests for deployment workflows
- **15.6**: Support running tests against specific vendors or all vendors
- **7.6**: Validation completes within 60 seconds
- **8.6**: Telemetry collection latency below 10 seconds
- **14.1**: Metrics persist across restarts
- **14.3**: Health checks for monitoring components
- **5.1, 5.5**: Universal queries work across vendors

## Future Enhancements

Potential improvements for integration tests:

1. **Multi-Vendor Deployment**: Test with actual multi-vendor lab
2. **EVPN/VXLAN Testing**: Validate EVPN fabric functionality
3. **Performance Benchmarks**: Measure and track performance metrics
4. **Chaos Testing**: Test resilience to failures
5. **Scale Testing**: Test with larger topologies
6. **Security Testing**: Validate authentication and authorization
7. **Upgrade Testing**: Test version upgrades and migrations

## Contributing

When adding new integration tests:

1. Follow existing test structure and naming conventions
2. Add tests to appropriate test file (end-to-end, multi-vendor, or monitoring)
3. Document requirements being validated
4. Update this README with new test descriptions
5. Ensure tests pass locally before submitting PR
6. Add appropriate fixtures if needed

## Support

For issues or questions about integration tests:

1. Check test output for specific error messages
2. Review troubleshooting section above
3. Check lab deployment status
4. Review monitoring stack logs
5. Consult main project documentation
