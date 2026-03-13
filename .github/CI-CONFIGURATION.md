# CI/CD Configuration Guide

This document describes the continuous integration setup for the production network testing lab.

## Overview

The CI/CD pipeline uses **uv** for fast, reproducible Python environment management and runs three types of tests:
1. **Unit Tests**: Fast, isolated tests of individual components
2. **Property-Based Tests**: Hypothesis-driven tests validating universal properties
3. **Integration Tests**: End-to-end tests with containerlab deployment

## Python Environment Management

### UV Integration

The CI pipeline uses [uv](https://github.com/astral-sh/uv) for Python package management:

**Benefits:**
- 10-100x faster than pip
- Automatic virtual environment management
- Reproducible builds with lockfile
- No manual venv activation needed

**Setup in CI:**
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true

- name: Set up Python
  run: uv python install 3.9

- name: Install dependencies
  run: uv sync --all-extras
```

**Running tests:**
```yaml
- name: Run tests
  run: uv run pytest tests/unit/ -v
```

## Workflow Structure

### Trigger Events

The test workflow runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

### Jobs

#### 1. Unit Tests Job
- **Runtime**: ~5 minutes
- **Timeout**: 10 minutes
- **Parallelization**: Uses pytest-xdist for parallel execution
- **Coverage**: Generates coverage reports for scripts and Ansible plugins
- **Artifacts**: Test results (JUnit XML), coverage reports (XML)

**What it tests:**
- Topology validation
- Configuration generation
- Telemetry subscription creation
- Metric normalization
- Validation engine
- State management

#### 2. Property-Based Tests Job
- **Runtime**: ~10 minutes
- **Timeout**: 15 minutes
- **Examples**: 200 per test (CI profile)
- **Artifacts**: Test results (JUnit XML), Hypothesis database

**What it tests:**
- Metric transformation preservation
- Cross-vendor metric consistency
- Lab state round-trip
- Version control friendly formats
- Configuration idempotency

#### 3. Integration Tests Job
- **Runtime**: ~20 minutes
- **Timeout**: 30 minutes
- **Environment**: Ubuntu with containerlab
- **Artifacts**: Test results, containerlab logs, docker logs

**What it tests:**
- Complete deployment workflows
- Multi-vendor integration
- Monitoring stack pipeline (gNMIc → Prometheus → Grafana)
- Telemetry collection
- Configuration application

#### 4. Test Summary Job
- **Dependencies**: Runs after all test jobs complete
- **Purpose**: Aggregates results and publishes summary
- **Artifacts**: Combined test report

## Environment Differences

### Local Development (macOS ARM)
- Uses ORB for containerlab execution
- Commands prefixed with `orb -m clab`
- Full multi-vendor support

### CI Environment (Linux x86_64)
- Native containerlab execution
- No ORB prefix needed
- Direct docker and containerlab commands

## Test Execution

### Unit Tests

```bash
uv run pytest tests/unit/ \
  -v \
  --tb=short \
  --cov=scripts \
  --cov=ansible/plugins \
  --cov=ansible/filter_plugins \
  --cov-report=xml \
  --cov-report=term-missing \
  --junit-xml=test-results/unit-tests.xml
```

**Flags:**
- `-v`: Verbose output
- `--tb=short`: Short traceback format
- `--cov`: Coverage measurement

**Note:** All pytest commands are executed via `uv run` to ensure consistent environment.
- `--cov-report=xml`: XML coverage report for CI tools
- `--junit-xml`: JUnit XML for test result publishing

### Property-Based Tests

```bash
pytest tests/property/ \
  -v \
  --tb=short \
  --hypothesis-profile=ci \
  --hypothesis-show-statistics \
  --junit-xml=test-results/property-tests.xml
```

**Flags:**
- `--hypothesis-profile=ci`: Use CI profile (200 examples)
- `--hypothesis-show-statistics`: Show Hypothesis statistics

**Hypothesis Profiles:**
- `default`: 100 examples (local development)
- `ci`: 200 examples (CI environment)
- `dev`: 50 examples with verbose output (debugging)

### Integration Tests

```bash
pytest tests/integration/ \
  -v \
  -s \
  --tb=short \
  --timeout=300 \
  --junit-xml=test-results/integration-tests.xml
```

**Flags:**
- `-s`: Show print statements (for progress tracking)
- `--timeout=300`: 5-minute timeout per test

## Containerlab Setup in CI

### Installation

```bash
sudo bash -c "$(curl -sL https://get.containerlab.dev)"
```

### Image Management

Integration tests may require container images:
- SR Linux: `ghcr.io/nokia/srlinux:latest`
- Arista cEOS: `ceos:latest` (requires authentication)
- SONiC: `docker-sonic-vs:latest`
- Juniper cRPD: `crpd:latest` (requires authentication)

**Note**: Some vendor images require authentication or licenses. CI may use:
- Public images where available
- Mock implementations for testing
- Cached images from previous runs

### Resource Limits

CI runners have limited resources:
- CPU: 2 cores
- Memory: 7GB
- Disk: 14GB

Integration tests are designed to work within these limits by:
- Using minimal topologies (2-4 devices)
- Limiting concurrent operations
- Cleaning up resources after tests

## Test Failure Reporting

### Detailed Failure Reports

When tests fail, the CI provides:

1. **JUnit XML Reports**: Structured test results
2. **Coverage Reports**: Code coverage metrics
3. **Containerlab Logs**: Lab deployment status
4. **Docker Logs**: Container output
5. **Test Output**: Verbose test execution logs

### Artifacts

All test artifacts are uploaded and available for 90 days:
- `unit-test-results`: JUnit XML for unit tests
- `unit-coverage-report`: Coverage XML report
- `property-test-results`: JUnit XML for property tests
- `hypothesis-database`: Hypothesis examples database
- `integration-test-results`: JUnit XML for integration tests
- `integration-test-logs`: Containerlab and docker logs

### Pull Request Comments

For pull requests, the CI automatically:
- Comments with coverage changes
- Publishes test result summary
- Highlights failing tests
- Shows coverage trends

## Parallelization

### Unit Tests

Unit tests use `pytest-xdist` for parallel execution:

```bash
pytest tests/unit/ -n auto
```

This automatically detects available CPU cores and runs tests in parallel.

### Property Tests

Property tests run sequentially to avoid resource contention and ensure reproducibility.

### Integration Tests

Integration tests run sequentially due to:
- Shared containerlab environment
- Port conflicts
- Resource constraints

## Timeouts

### Job Timeouts

- Unit Tests: 10 minutes
- Property Tests: 15 minutes
- Integration Tests: 30 minutes

### Test Timeouts

Individual integration tests have a 5-minute timeout to prevent hanging.

## Coverage Requirements

### Thresholds

- **Green**: ≥80% coverage
- **Orange**: 60-79% coverage
- **Red**: <60% coverage

### Coverage Targets

- `scripts/`: Python scripts
- `ansible/plugins/`: Ansible plugins
- `ansible/filter_plugins/`: Ansible filters

## Troubleshooting

### Unit Tests Failing

1. Check test output for specific failures
2. Review coverage report for untested code
3. Run tests locally: `pytest tests/unit/ -v`

### Property Tests Failing

1. Check Hypothesis statistics for shrinking
2. Review failing examples in output
3. Download Hypothesis database artifact
4. Reproduce locally: `pytest tests/property/ -v --hypothesis-profile=ci`

### Integration Tests Failing

1. Check containerlab logs artifact
2. Review docker logs artifact
3. Verify image availability
4. Check resource limits
5. Run locally with containerlab

### Timeout Issues

If tests timeout:
1. Check for hanging processes
2. Review test execution time
3. Increase timeout if necessary
4. Optimize slow tests

## Local CI Simulation

To simulate CI environment locally:

```bash
# Run all tests as CI would
pytest tests/unit/ -v --cov=scripts --cov=ansible/plugins --cov=ansible/filter_plugins
pytest tests/property/ -v --hypothesis-profile=ci
pytest tests/integration/ -v -s --timeout=300

# Or use act to run GitHub Actions locally
act -j unit-tests
act -j property-tests
```

## Maintenance

### Updating Dependencies

When updating `requirements.txt`:
1. Test locally first
2. Update CI cache if needed
3. Verify all test jobs pass

### Adding New Tests

When adding new tests:
1. Add to appropriate directory (unit/property/integration)
2. Ensure tests pass locally
3. Update this documentation if needed
4. Verify CI runs successfully

### Modifying Workflow

When modifying `.github/workflows/test.yml`:
1. Test with workflow dispatch first
2. Review job dependencies
3. Check artifact uploads
4. Verify timeout values

## Performance Optimization

### Caching

The workflow uses caching for:
- Python packages (`pip cache`)
- Docker images (implicit)

### Parallel Execution

- Unit tests run in parallel (pytest-xdist)
- Test jobs run in parallel (unit, property, integration)

### Resource Management

- Cleanup after integration tests
- Docker system prune
- Containerlab destroy

## Requirements Validation

This CI/CD setup validates:

- **15.1**: Automated tests for deployment workflows ✓
- **15.2**: Automated tests for configuration management ✓
- **15.3**: Automated tests for telemetry collection ✓
- **15.4**: Automated tests for metric normalization ✓
- **15.5**: Detailed failure reports ✓
- **15.7**: Test suite completes within 10 minutes (unit + property < 10 min) ✓

## Future Enhancements

Potential improvements:

1. **Matrix Testing**: Test multiple Python versions
2. **Multi-Vendor Testing**: Test with actual vendor images
3. **Performance Benchmarks**: Track performance over time
4. **Security Scanning**: Add security vulnerability scanning
5. **Deployment Testing**: Test deployment to staging environment
6. **Scheduled Runs**: Nightly comprehensive test runs
7. **Slack Notifications**: Alert on test failures
8. **Coverage Trends**: Track coverage changes over time

## Support

For CI/CD issues:
1. Check workflow run logs
2. Download and review artifacts
3. Reproduce locally
4. Review this documentation
5. Check GitHub Actions status page
