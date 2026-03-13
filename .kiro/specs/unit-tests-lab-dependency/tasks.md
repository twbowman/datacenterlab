# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Unit Tests Fail Without Lab Deployment
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to CI/CD environments (GitHub Actions, clean dev machines) where no lab is deployed
  - Test that unit tests execute successfully in environments where `isBugCondition(environment)` is true (no lab deployed, CI/CD environment, clean dev machine)
  - The test assertions should verify: all unit tests pass, execution time < 60 seconds, no external dependencies used
  - Run test on UNFIXED code in GitHub Actions or clean environment
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found: FileNotFoundError, subprocess errors, connection timeouts, import errors
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Test Logic and Assertions Remain Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code: extract all test assertions, measure test coverage, verify integration tests require lab
  - Write property-based tests capturing observed behavior patterns:
    - For all unit tests, assertions remain unchanged after fix
    - For all unit tests, test coverage is maintained or improved
    - For all integration tests, lab requirement is preserved
    - For all property-based tests, they continue to work without changes
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix unit tests lab dependency

  - [x] 3.1 Add comprehensive mocking infrastructure to conftest.py
    - Add mock file operations fixtures (mock_topology_file, mock_yaml_load, mock_file_operations)
    - Add mock subprocess operations fixtures (mock_subprocess, mock_containerlab_cli, mock_docker_commands)
    - Add mock network operations fixtures (mock_gnmi_connection, mock_ssh_connection, mock_netconf_connection)
    - Add mock device state fixtures (mock_device_bgp_state, mock_device_interface_state, mock_device_lldp_state)
    - Configure pytest plugins (pytest-mock) for easier mocking
    - _Bug_Condition: isBugCondition(input) where NOT labDeployed(input.environment) OR input.environment.type IN ['ci_cd', 'github_actions', 'clean_dev_machine']_
    - _Expected_Behavior: Unit tests execute successfully using mocks without external dependencies_
    - _Preservation: Integration tests continue to require lab, property tests continue to work, test assertions remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Update test_deployment.py to use mocks
    - Replace tmp_path file creation with mock_topology_file fixture
    - Patch Path.exists() to return True for test topology files
    - Patch open() to return StringIO with test YAML content
    - Patch yaml.safe_load() to return parsed topology dictionaries
    - Mock TopologyValidator._load_topology() to use mocked data
    - Mock subprocess calls if tests invoke containerlab/docker commands
    - _Bug_Condition: Tests fail with FileNotFoundError or subprocess errors without lab_
    - _Expected_Behavior: Tests pass using mocked file I/O and subprocess calls_
    - _Preservation: All test assertions and validation logic remain unchanged_
    - _Requirements: 2.1, 2.2, 3.2, 3.3_

  - [x] 3.3 Update test_configuration.py to eliminate external dependencies
    - Mock Ansible dependencies if filter plugins import Ansible libraries
    - Use sys.modules patching to provide mock Ansible modules
    - Ensure filter functions work with pure Python logic
    - Verify no hidden file I/O operations occur
    - _Bug_Condition: Tests fail with ModuleNotFoundError or import errors without lab_
    - _Expected_Behavior: Tests pass with mocked dependencies_
    - _Preservation: Filter validation logic and assertions remain unchanged_
    - _Requirements: 2.1, 2.2, 3.2, 3.3_

  - [x] 3.4 Update test_validation.py to use mock device state
    - Mock device state queries (BGP, interface, LLDP state)
    - Patch functions that would connect to devices
    - Return mock state data from fixtures
    - Preserve all validation logic and assertions
    - _Bug_Condition: Tests fail with connection errors without lab_
    - _Expected_Behavior: Tests pass using mocked device state_
    - _Preservation: Validation logic and assertions remain unchanged_
    - _Requirements: 2.1, 2.2, 3.2, 3.3_

  - [x] 3.5 Update test_telemetry.py to mock gNMI connections
    - Mock gRPC/gNMI connection establishment
    - Patch gRPC channel creation to return mock channel
    - Mock subscription responses with test metric data
    - Ensure normalization logic works without network calls
    - _Bug_Condition: Tests fail with gRPC connection errors without lab_
    - _Expected_Behavior: Tests pass using mocked gNMI connections_
    - _Preservation: Metric normalization logic and assertions remain unchanged_
    - _Requirements: 2.1, 2.2, 3.2, 3.3_

  - [x] 3.6 Update test_state_management.py to mock file operations
    - Mock file export operations (patch open() for writes)
    - Use StringIO to capture output in memory
    - Mock file import operations (patch open() for reads)
    - Use StringIO to simulate file reads with test data
    - _Bug_Condition: Tests fail with file I/O errors without lab_
    - _Expected_Behavior: Tests pass using mocked file operations_
    - _Preservation: State management logic and assertions remain unchanged_
    - _Requirements: 2.1, 2.2, 3.2, 3.3_

  - [x] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Unit Tests Pass Without Lab Deployment
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1 in CI/CD environment
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify: all unit tests pass, execution time < 60 seconds, no external dependencies used
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Test Logic and Assertions Remain Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify: test assertions unchanged, coverage maintained, integration tests still require lab, property tests still work
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full unit test suite in CI/CD environment without lab
  - Verify execution time < 60 seconds
  - Verify no external dependencies are accessed
  - Run integration tests in lab environment to confirm they still work
  - Run property-based tests to confirm they still work
  - Ask the user if questions arise
