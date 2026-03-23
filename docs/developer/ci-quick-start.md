# CI/CD Quick Start Guide

## For Developers

### Before You Push

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras

# Run all tests locally (simulates CI)
./scripts/run-ci-tests.sh

# Or run just unit and property tests (faster)
./scripts/run-ci-tests.sh --no-integration
```

### Understanding Test Results

**✓ Green**: All tests passed - ready to push!
**✗ Red**: Some tests failed - fix before pushing
**⚠ Yellow**: Warning or skipped - review if needed

### Common Commands

```bash
# Run only unit tests (fastest)
./scripts/run-ci-tests.sh --unit-only

# Run only property tests
./scripts/run-ci-tests.sh --property-only

# Run specific test file
uv run pytest tests/unit/test_deployment.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=scripts --cov-report=html

# Run all tests manually
uv run pytest tests/ -v
```

### Viewing Coverage

After running tests with coverage:
```bash
# Open coverage report in browser
open htmlcov/unit/index.html  # macOS
xdg-open htmlcov/unit/index.html  # Linux
```

## For Reviewers

### Checking CI Status

1. Go to the **Actions** tab
2. Find the workflow run for the PR
3. Check all jobs are green ✓
4. Review coverage changes in PR comments

### Common Issues

**Tests failing in CI but passing locally?**
- Environment differences (Linux vs macOS)
- Ask developer to run `./scripts/run-ci-tests.sh`

**Coverage dropped?**
- New code without tests
- Ask developer to add tests

**Integration tests timing out?**
- Resource constraints in CI
- May need to optimize or increase timeout

## Test Types

### Unit Tests (~5 min)
- Fast, isolated component tests
- Run on every push
- Must pass before merge

### Property Tests (~10 min)
- Hypothesis-driven tests
- 200 examples per test in CI
- Validate universal properties

### Integration Tests (~20 min)
- End-to-end with containerlab
- Test complete workflows
- May be slower in CI

## CI Workflow

```
Push/PR → GitHub Actions
  ├─ Unit Tests (parallel)
  ├─ Property Tests (parallel)
  ├─ Integration Tests (parallel)
  └─ Test Summary (after all)
```

## Artifacts

Available for 90 days after test run:
- Test results (JUnit XML)
- Coverage reports
- Containerlab logs
- Docker logs
- Hypothesis database

## Tips

### Speed Up Local Testing

```bash
# Skip slow integration tests
./scripts/run-ci-tests.sh --no-integration

# Run specific test
pytest tests/unit/test_deployment.py::TestTopologyValidation::test_valid_srlinux_topology -v

# Use pytest-xdist for parallel execution
pytest tests/unit/ -n auto
```

### Debug Failing Tests

```bash
# Run with verbose output
pytest tests/unit/test_deployment.py -vv

# Show local variables on failure
pytest tests/unit/test_deployment.py -l

# Drop into debugger on failure
pytest tests/unit/test_deployment.py --pdb
```

### Check Coverage

```bash
# Show missing lines
pytest tests/unit/ --cov=scripts --cov-report=term-missing

# Generate HTML report
pytest tests/unit/ --cov=scripts --cov-report=html

# Check specific file
pytest tests/unit/test_deployment.py --cov=scripts/validate-topology.py
```

## Requirements

### Local Development
- Python 3.9+
- pip
- pytest
- hypothesis

### Integration Tests (Optional)
- Docker
- containerlab (Linux) or remote server (macOS)

## Getting Help

1. Check [README.md](.github/README.md) for detailed info
2. Check [CI-CONFIGURATION.md](.github/CI-CONFIGURATION.md) for configuration
3. Review test documentation in `tests/*/README.md`
4. Check workflow logs in GitHub Actions

## Best Practices

✓ **DO**: Run tests before pushing
✓ **DO**: Add tests for new code
✓ **DO**: Keep coverage above 80%
✓ **DO**: Fix failing tests promptly

✗ **DON'T**: Push without running tests
✗ **DON'T**: Ignore coverage drops
✗ **DON'T**: Skip test failures
✗ **DON'T**: Commit commented-out tests

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/run-ci-tests.sh` | Run all tests (CI simulation) |
| `./scripts/run-ci-tests.sh --unit-only` | Run only unit tests |
| `./scripts/run-ci-tests.sh --no-integration` | Skip integration tests |
| `pytest tests/unit/ -v` | Run unit tests |
| `pytest tests/property/ -v` | Run property tests |
| `pytest tests/integration/ -v -s` | Run integration tests |
| `pytest --cov=scripts` | Run with coverage |
| `pytest -k test_name` | Run specific test |
| `pytest -m unit` | Run tests with marker |

## Status Badges

Add to README.md:
```markdown
![Tests](https://github.com/USERNAME/REPO/workflows/Test%20Suite/badge.svg)
```

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "Permission denied" on script
```bash
chmod +x scripts/run-ci-tests.sh
```

### Tests hanging
- Check for infinite loops
- Add timeouts: `pytest --timeout=60`
- Kill hanging processes: `pkill -f pytest`

### Coverage not working
```bash
pip install pytest-cov
```

## Next Steps

1. Run `./scripts/run-ci-tests.sh` to verify setup
2. Check that all tests pass
3. Review coverage report
4. Push changes and check CI
5. Monitor GitHub Actions for results

---

**Remember**: Green CI = Happy Team! 🎉
