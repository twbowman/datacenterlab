# GitHub Actions CI/CD

This directory contains the continuous integration and deployment workflows for the production network testing lab.

## Workflows

### test.yml - Test Suite Workflow

Comprehensive test execution workflow that runs on every push and pull request.

**Jobs:**
1. **unit-tests**: Fast unit tests with coverage reporting
2. **property-tests**: Property-based tests using Hypothesis
3. **integration-tests**: End-to-end integration tests with containerlab
4. **test-summary**: Aggregates and publishes test results

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Duration:** ~30 minutes total (jobs run in parallel)

## Quick Start

### Running Tests Locally

Before pushing to CI, run tests locally:

```bash
# Run all tests (simulates CI)
./scripts/run-ci-tests.sh

# Run only unit tests
./scripts/run-ci-tests.sh --unit-only

# Run without integration tests (faster)
./scripts/run-ci-tests.sh --no-integration
```

### Viewing CI Results

1. Go to the **Actions** tab in GitHub
2. Select the workflow run
3. View job results and logs
4. Download artifacts for detailed analysis

### Understanding Test Results

**Green checkmark (✓)**: All tests passed
**Red X (✗)**: Some tests failed - click for details
**Yellow dot (●)**: Tests are running

## Test Types

### Unit Tests (5 minutes)

Fast, isolated tests of individual components:
- Topology validation
- Configuration generation
- Telemetry processing
- Validation engine
- State management

**Coverage Target:** 80%+

### Property-Based Tests (10 minutes)

Hypothesis-driven tests validating universal properties:
- Metric transformation preservation
- Cross-vendor consistency
- State round-trip preservation
- Configuration idempotency

**Examples per test:** 200 (CI profile)

### Integration Tests (20 minutes)

End-to-end tests with real containerlab deployment:
- Complete deployment workflows
- Multi-vendor integration
- Monitoring stack pipeline
- Telemetry collection

**Environment:** Ubuntu with containerlab

## Artifacts

Test artifacts are available for 90 days:

- **unit-test-results**: JUnit XML test results
- **unit-coverage-report**: Code coverage report
- **property-test-results**: Property test results
- **hypothesis-database**: Hypothesis examples
- **integration-test-results**: Integration test results
- **integration-test-logs**: Containerlab and docker logs

## Coverage Reporting

Coverage reports are automatically:
- Generated for each PR
- Commented on pull requests
- Uploaded as artifacts
- Tracked over time

**Thresholds:**
- Green: ≥80%
- Orange: 60-79%
- Red: <60%

## Troubleshooting

### Tests Failing in CI but Passing Locally

**Possible causes:**
1. Environment differences (Linux vs macOS)
2. Missing dependencies in CI
3. Timing issues (CI is slower)
4. Resource constraints

**Solutions:**
1. Run `./scripts/run-ci-tests.sh` to simulate CI
2. Check CI logs for specific errors
3. Download artifacts for detailed analysis
4. Adjust timeouts if needed

### Integration Tests Timing Out

**Possible causes:**
1. Slow container startup
2. Network issues
3. Resource constraints
4. Hanging processes

**Solutions:**
1. Check containerlab logs artifact
2. Review docker logs artifact
3. Increase timeout in workflow
4. Optimize test setup

### Coverage Dropping

**Possible causes:**
1. New code without tests
2. Removed tests
3. Changed coverage configuration

**Solutions:**
1. Add tests for new code
2. Review coverage report artifact
3. Check coverage thresholds

## Best Practices

### Before Pushing

1. Run tests locally: `./scripts/run-ci-tests.sh`
2. Check coverage: `pytest tests/unit/ --cov`
3. Fix any failures
4. Commit and push

### Writing Tests

1. Add unit tests for new functions
2. Add property tests for universal properties
3. Add integration tests for workflows
4. Ensure tests are deterministic
5. Use descriptive test names

### Pull Requests

1. Ensure all CI checks pass
2. Review coverage changes
3. Address test failures promptly
4. Keep PRs focused and small

## Configuration

### Workflow Configuration

Edit `.github/workflows/test.yml` to:
- Change Python version
- Adjust timeouts
- Modify test commands
- Add new jobs

### Test Configuration

Edit test files to:
- Add new test cases
- Modify test fixtures
- Adjust Hypothesis settings
- Update test data

### Coverage Configuration

Edit `.coveragerc` (if exists) to:
- Change coverage targets
- Exclude files from coverage
- Adjust reporting format

## Performance

### Current Performance

- Unit tests: ~5 minutes
- Property tests: ~10 minutes
- Integration tests: ~20 minutes
- Total (parallel): ~30 minutes

### Optimization Tips

1. Use pytest-xdist for parallel unit tests
2. Cache Python dependencies
3. Reuse containerlab deployments
4. Minimize integration test scope
5. Use fast Hypothesis profiles locally

## Requirements Validation

This CI/CD setup validates the following requirements:

- ✓ **15.1**: Automated tests for deployment workflows
- ✓ **15.2**: Automated tests for configuration management
- ✓ **15.3**: Automated tests for telemetry collection
- ✓ **15.4**: Automated tests for metric normalization
- ✓ **15.5**: Detailed failure reports with logs and diagnostics
- ✓ **15.7**: Test suite completes within 10 minutes (unit + property)

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Containerlab Documentation](https://containerlab.dev/)

## Support

For CI/CD issues:

1. Check workflow logs in GitHub Actions
2. Download and review artifacts
3. Run tests locally with `./scripts/run-ci-tests.sh`
4. Review [CI-CONFIGURATION.md](CI-CONFIGURATION.md)
5. Check test documentation in `tests/*/README.md`

## Future Enhancements

Planned improvements:

- [ ] Matrix testing (multiple Python versions)
- [ ] Multi-vendor image testing
- [ ] Performance benchmarking
- [ ] Security scanning
- [ ] Deployment testing
- [ ] Scheduled nightly runs
- [ ] Slack notifications
- [ ] Coverage trend tracking
