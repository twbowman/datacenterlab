# Unit Tests

This directory contains unit tests for all major components of the production network testing lab.

## Test Coverage

### test_deployment.py
Tests topology validation, error conditions, and health checks.

**Coverage:**
- Valid topology configurations (single vendor, multi-vendor)
- Missing topology files and invalid YAML syntax
- Missing required fields (name, topology, kind, image)
- Unsupported device kinds
- Invalid link formats and undefined node references
- Self-loop detection
- Group-based configuration
- Error message specificity and remediation suggestions

**Validates:** Requirements 15.1

### test_configuration.py
Tests configuration generation for each vendor, syntax validation, and rollback.

**Coverage:**
- Interface name translation between vendor formats (SR Linux, Arista, SONiC, Junos)
- Configuration structure validation (BGP, interfaces, OSPF)
- Syntax validation (IP addresses, ASN ranges, router IDs, interface names)
- Configuration rollback functionality
- Configuration idempotency
- Vendor-specific configuration formats (JSON, CLI)

**Validates:** Requirements 15.2

### test_telemetry.py
Tests gNMI subscription creation, metric normalization, and Prometheus export.

**Coverage:**
- gNMI subscription configuration (OpenConfig and native paths)
- Subscription modes (stream, sample, on_change)
- Metric normalization rules
- Metric value and timestamp preservation
- Vendor label addition
- Interface name normalization
- Native metric vendor prefixes
- Prometheus metric format and export
- Telemetry processors (event-convert, event-add-tag)
- Connection management and exponential backoff

**Validates:** Requirements 15.3

### test_validation.py
Tests validation checks, error detection, and report generation.

**Coverage:**
- BGP session validation (established, missing, unexpected neighbors)
- EVPN route validation (advertised, received, route targets)
- LLDP neighbor validation (topology matching, missing neighbors)
- Interface state validation (operational state, admin/oper mismatch, counters)
- Validation report structure and JSON format
- Validation summary statistics
- Remediation suggestions
- Validation performance requirements
- Configuration drift detection

**Validates:** Requirements 15.1

### test_state_management.py
Tests state export, restore, comparison, and incremental updates.

**Coverage:**
- State export (topology, configurations, metadata, metrics snapshot)
- State restore (validation, error handling)
- State comparison (topology changes, configuration diffs, metrics)
- Incremental updates (configuration-only, topology changes)
- Version control friendly formats (YAML, JSON)
- State snapshot metadata (timestamp, version, description)
- State round-trip preservation

**Validates:** Requirements 15.1

## Running Tests

### Run all unit tests:
```bash
pytest tests/unit/ -v
```

### Run specific test file:
```bash
pytest tests/unit/test_deployment.py -v
pytest tests/unit/test_configuration.py -v
pytest tests/unit/test_telemetry.py -v
pytest tests/unit/test_validation.py -v
pytest tests/unit/test_state_management.py -v
```

### Run specific test class:
```bash
pytest tests/unit/test_deployment.py::TestTopologyValidation -v
```

### Run specific test:
```bash
pytest tests/unit/test_deployment.py::TestTopologyValidation::test_valid_srlinux_topology -v
```

### Run with coverage:
```bash
pytest tests/unit/ --cov=scripts --cov=ansible/plugins --cov=ansible/filter_plugins -v
```

### Run with verbose output:
```bash
pytest tests/unit/ -vv
```

## Test Structure

Each test file follows this structure:

1. **Test Classes**: Group related tests together
2. **Test Methods**: Individual test cases with descriptive names
3. **Fixtures**: Reusable test data defined in `conftest.py`
4. **Assertions**: Clear assertions with meaningful error messages

## Test Naming Convention

- Test files: `test_<component>.py`
- Test classes: `Test<Functionality>`
- Test methods: `test_<specific_behavior>`

## Fixtures

Common fixtures are defined in `conftest.py`:
- `sample_topology`: Sample topology definition
- `sample_bgp_config`: Sample BGP configuration
- `sample_interface_config`: Sample interface configuration
- `sample_metric`: Sample telemetry metric
- `sample_validation_report`: Sample validation report
- `sample_lab_state`: Sample lab state snapshot

## Test Philosophy

These unit tests follow these principles:

1. **Fast**: Tests run quickly without external dependencies
2. **Isolated**: Each test is independent and can run in any order
3. **Focused**: Each test validates one specific behavior
4. **Clear**: Test names clearly describe what is being tested
5. **Comprehensive**: Tests cover normal cases, edge cases, and error conditions

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines:
- No external dependencies (containers, network devices)
- Fast execution (< 1 minute for full suite)
- Clear pass/fail status
- Detailed error messages for debugging

## Adding New Tests

When adding new functionality:

1. Create test file in `tests/unit/`
2. Import necessary modules
3. Create test classes for logical grouping
4. Write test methods with clear names
5. Use fixtures from `conftest.py` or create new ones
6. Add assertions with meaningful messages
7. Update this README with coverage information

## Requirements Traceability

Each test file includes a docstring indicating which requirements it validates:
- Requirements 15.1: Automated tests for deployment workflows
- Requirements 15.2: Automated tests for configuration management
- Requirements 15.3: Automated tests for telemetry collection

## Notes

- These are **unit tests** - they test individual components in isolation
- For end-to-end testing, see `tests/integration/`
- For property-based testing, see `tests/property/`
- Mock objects are used where necessary to avoid external dependencies
