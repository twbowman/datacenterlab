# Unit Tests Lab Dependency Bugfix Design

## Overview

The unit tests currently require a deployed containerlab environment with actual network devices, preventing them from running in CI/CD environments like GitHub Actions. This design addresses the bug by introducing comprehensive mocking and stubbing strategies to eliminate external dependencies while preserving test coverage and correctness validation.

The fix involves replacing file I/O operations, subprocess calls, and network device interactions with mock objects and test doubles. This will enable unit tests to run in any environment without requiring containerlab deployments, actual network devices, or external infrastructure.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when unit tests are executed in an environment without a deployed containerlab lab
- **Property (P)**: The desired behavior when unit tests run - they should execute successfully using mocks/stubs instead of real infrastructure
- **Preservation**: Existing test logic, assertions, and coverage that must remain unchanged by the fix
- **TopologyValidator**: The class in `scripts/validate-topology.py` that validates topology YAML files
- **Mock Object**: A test double that simulates the behavior of real objects without external dependencies
- **Test Double**: Generic term for any object used in place of a real object for testing purposes (mocks, stubs, fakes)
- **File I/O**: Operations that read from or write to the filesystem (YAML/JSON file loading)
- **Subprocess Call**: Execution of external commands (containerlab CLI, docker commands)

## Bug Details

### Bug Condition

The bug manifests when unit tests are executed in any environment that does not have a deployed containerlab lab with running network devices. The tests either fail with file not found errors, connection errors, or attempt to make actual system calls that are inappropriate for unit tests.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type TestExecutionEnvironment
  OUTPUT: boolean
  
  RETURN (NOT labDeployed(input.environment))
         OR (input.environment.type IN ['ci_cd', 'github_actions', 'clean_dev_machine'])
         AND testType(input.test) == 'unit'
         AND testRequiresExternalDependency(input.test)
END FUNCTION
```

### Examples

- **test_deployment.py**: Tests create temporary topology files and call `TopologyValidator` which attempts to load YAML files from disk. When the validator's `_load_topology()` method runs, it performs actual file I/O operations.

- **test_configuration.py**: Tests import filter modules that may have dependencies on Ansible libraries or external configuration files. The tests validate configuration structures but currently use real file operations.

- **test_validation.py**: Tests validate BGP sessions, EVPN routes, and LLDP neighbors. While currently using mock data structures, they may attempt to import modules that have network device dependencies.

- **test_telemetry.py**: Tests validate gNMI subscriptions and metric normalization. These tests work with data structures but may import modules that attempt to establish gRPC connections.

- **test_state_management.py**: Tests export/restore state functionality. While using in-memory data, they may call functions that attempt to write to filesystem or interact with containerlab.

- **Edge case**: When running in GitHub Actions CI/CD pipeline, tests fail because containerlab cannot be deployed, Docker is not available, or network device images cannot be pulled.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All test assertions and validation logic must continue to verify the same correctness properties
- Test coverage for business logic, data transformations, and algorithms must remain comprehensive
- Configuration generation, metric normalization, and validation logic tests must continue to verify correct outputs
- Property-based tests must continue to run without lab dependencies (they already work correctly)
- Integration tests must continue to require a deployed lab and test against actual devices

**Scope:**
All test execution that does NOT involve unit tests should be completely unaffected by this fix. This includes:
- Integration tests that require actual lab deployment
- Property-based tests that already run without lab dependencies
- Manual testing workflows that use deployed labs
- Production deployment and operation of the lab environment

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Direct File I/O in Tests**: Tests use `tmp_path` fixtures to create real files and then call validators that perform actual file I/O operations. The `TopologyValidator._load_topology()` method uses `yaml.safe_load()` on real file handles.

2. **Missing Mock Layer**: There is no mocking infrastructure in place. The `conftest.py` provides data fixtures but does not mock external dependencies like file operations, subprocess calls, or network connections.

3. **Tight Coupling to Implementation**: Tests directly instantiate classes like `TopologyValidator` that have hard dependencies on filesystem operations. There's no dependency injection or abstraction layer.

4. **Import-Time Side Effects**: Some imported modules may have side effects at import time (checking for files, establishing connections, loading configurations) that fail in environments without lab infrastructure.

## Correctness Properties

Property 1: Bug Condition - Unit Tests Run Without Lab

_For any_ test execution environment where a containerlab lab is not deployed (CI/CD, GitHub Actions, clean development machine), the unit tests SHALL execute successfully using mocked file I/O, mocked subprocess calls, and mocked network operations, producing the same test results (pass/fail) as they would with real dependencies.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Test Logic and Assertions

_For any_ unit test that currently validates business logic, data transformations, or algorithms, the fixed tests SHALL preserve exactly the same assertions and validation logic, ensuring that the test coverage and correctness verification remain unchanged.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `tests/unit/conftest.py`

**Function**: Add new fixtures for mocking

**Specific Changes**:
1. **Add Mock File Operations**: Create fixtures that mock `open()`, `Path.read_text()`, and `yaml.safe_load()` to return test data without actual file I/O
   - `mock_topology_file`: Returns sample topology YAML content
   - `mock_yaml_load`: Mocks `yaml.safe_load()` to return parsed topology data
   - `mock_file_operations`: Patches file operations globally for tests

2. **Add Mock Subprocess Operations**: Create fixtures that mock subprocess calls
   - `mock_subprocess`: Mocks `subprocess.run()` and `subprocess.Popen()`
   - `mock_containerlab_cli`: Mocks containerlab CLI commands
   - `mock_docker_commands`: Mocks docker CLI commands

3. **Add Mock Network Operations**: Create fixtures that mock network connections
   - `mock_gnmi_connection`: Mocks gRPC/gNMI connections
   - `mock_ssh_connection`: Mocks SSH connections to devices
   - `mock_netconf_connection`: Mocks NETCONF connections

4. **Add Mock Device State**: Create fixtures that return device state data
   - `mock_device_bgp_state`: Returns sample BGP neighbor state
   - `mock_device_interface_state`: Returns sample interface state
   - `mock_device_lldp_state`: Returns sample LLDP neighbor data

5. **Add Pytest Plugins**: Configure pytest to automatically apply mocks
   - Use `pytest-mock` plugin for easier mocking
   - Use `monkeypatch` fixture for patching imports

**File**: `tests/unit/test_deployment.py`

**Function**: Modify tests to use mocks instead of real file I/O

**Specific Changes**:
1. **Replace tmp_path with mock_topology_file**: Instead of creating real files with `tmp_path.write_text()`, use mocked file operations that return test data
   - Patch `Path.exists()` to return True for test topology files
   - Patch `open()` to return StringIO with test YAML content
   - Patch `yaml.safe_load()` to return parsed topology dictionaries

2. **Mock TopologyValidator File Operations**: Patch the `_load_topology()` method to use mocked data
   - Use `monkeypatch` to replace file operations in the validator
   - Ensure validator receives test data without touching filesystem

3. **Mock Subprocess Calls**: If any tests invoke containerlab or docker commands, mock those calls
   - Patch `subprocess.run()` to return success/failure as needed
   - Return mock stdout/stderr for command output validation

**File**: `tests/unit/test_configuration.py`

**Function**: Ensure filter plugins work without external dependencies

**Specific Changes**:
1. **Mock Ansible Dependencies**: If filter plugins import Ansible libraries, mock those imports
   - Use `sys.modules` patching to provide mock Ansible modules
   - Ensure filter functions work with pure Python logic

2. **Isolate Filter Logic**: Tests already work with pure data structures, ensure no hidden file I/O

**File**: `tests/unit/test_validation.py`

**Function**: Use mock device state instead of real device queries

**Specific Changes**:
1. **Mock Device State Queries**: If validation logic queries device state, mock those queries
   - Patch any functions that would connect to devices
   - Return mock BGP state, interface state, LLDP state from fixtures

2. **Preserve Validation Logic**: Keep all assertion logic unchanged, only mock data sources

**File**: `tests/unit/test_telemetry.py`

**Function**: Mock gNMI connections and metric collection

**Specific Changes**:
1. **Mock gRPC/gNMI**: If tests import gNMI libraries, mock connection establishment
   - Patch gRPC channel creation to return mock channel
   - Mock subscription responses with test metric data

2. **Isolate Normalization Logic**: Tests already work with data structures, ensure no network calls

**File**: `tests/unit/test_state_management.py`

**Function**: Mock state export/restore file operations

**Specific Changes**:
1. **Mock File Export**: If state export writes to files, mock those operations
   - Patch `open()` for write operations to capture output in memory
   - Use StringIO to simulate file writes

2. **Mock File Import**: If state restore reads from files, mock those operations
   - Patch `open()` for read operations to return test data
   - Use StringIO to simulate file reads

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code by running tests in a CI/CD environment without a lab, then verify the fix works correctly by ensuring tests pass with mocks and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Run the existing unit tests in a GitHub Actions CI/CD environment without deploying a containerlab lab. Observe which tests fail and what error messages they produce. This will confirm the root causes (file I/O, subprocess calls, network operations).

**Test Cases**:
1. **CI/CD Execution Test**: Run `pytest tests/unit/` in GitHub Actions without lab deployment (will fail on unfixed code)
2. **File I/O Dependency Test**: Run `test_deployment.py::TestTopologyValidation::test_valid_srlinux_topology` and observe file I/O errors (will fail on unfixed code)
3. **Import Dependency Test**: Import test modules and check for import-time errors related to missing dependencies (may fail on unfixed code)
4. **Subprocess Dependency Test**: Run tests that might invoke containerlab/docker commands and observe subprocess errors (may fail on unfixed code)

**Expected Counterexamples**:
- Tests fail with `FileNotFoundError` when trying to load topology files
- Tests fail with `ModuleNotFoundError` if dependencies are missing
- Tests fail with `subprocess.CalledProcessError` if trying to run containerlab commands
- Tests timeout or hang if trying to establish network connections
- Possible causes: direct file I/O, missing mock layer, tight coupling to implementation, import-time side effects

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (no lab deployed), the fixed unit tests execute successfully using mocks.

**Pseudocode:**
```
FOR ALL environment WHERE isBugCondition(environment) DO
  result := run_unit_tests_with_mocks(environment)
  ASSERT result.all_tests_passed OR result.failures_are_legitimate
  ASSERT result.execution_time < 60_seconds
  ASSERT result.no_external_dependencies_used
END FOR
```

**Test Plan**: After implementing mocks, run unit tests in multiple environments (GitHub Actions, local machine without lab, Docker container without containerlab) and verify they all pass.

**Test Cases**:
1. **GitHub Actions CI Test**: Run unit tests in GitHub Actions workflow and verify all pass
2. **Clean Environment Test**: Run unit tests on a machine without containerlab installed and verify all pass
3. **Execution Time Test**: Verify unit test suite completes in < 60 seconds
4. **No External Calls Test**: Use monitoring/instrumentation to verify no actual file I/O, subprocess calls, or network connections occur

### Preservation Checking

**Goal**: Verify that for all test logic and assertions, the fixed tests produce the same validation results as the original tests.

**Pseudocode:**
```
FOR ALL test WHERE test.type == 'unit' DO
  original_assertions := extract_assertions(test.original_code)
  fixed_assertions := extract_assertions(test.fixed_code)
  ASSERT original_assertions == fixed_assertions
  
  original_coverage := measure_coverage(test.original_code)
  fixed_coverage := measure_coverage(test.fixed_code)
  ASSERT fixed_coverage >= original_coverage
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all test scenarios

**Test Plan**: Compare test assertions before and after fix. Run tests with both real dependencies (in a lab environment) and mocked dependencies, verify same pass/fail results.

**Test Cases**:
1. **Assertion Preservation**: Verify all test assertions remain unchanged after adding mocks
2. **Coverage Preservation**: Run coverage analysis before and after fix, verify coverage percentage is maintained or improved
3. **Integration Test Preservation**: Verify integration tests still require lab and work with real devices
4. **Property Test Preservation**: Verify property-based tests continue to work without changes

### Unit Tests

- Test that mock fixtures provide correct data structures
- Test that mocked file operations return expected content
- Test that mocked subprocess calls return expected results
- Test that TopologyValidator works with mocked file I/O
- Test that all unit tests pass without external dependencies
- Test that test execution time is < 60 seconds

### Property-Based Tests

- Generate random topology configurations and verify validation logic works with mocked file I/O
- Generate random BGP configurations and verify tests work with mocked device state
- Generate random test execution environments and verify unit tests pass in all environments without lab
- Test that mocking layer correctly simulates all file I/O operations across many scenarios

### Integration Tests

- Verify integration tests still require deployed lab after fix
- Verify integration tests still test against actual network devices
- Verify integration tests can be skipped in CI/CD while unit tests run
- Test full CI/CD pipeline with unit tests passing and integration tests skipped
