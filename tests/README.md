# Testing Guide

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management and pytest for testing.

## Prerequisites

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

Run all tests:
```bash
./scripts/run-ci-tests.sh
```

Run specific test suites:
```bash
# Unit tests only
./scripts/run-ci-tests.sh --unit-only

# Property-based tests only
./scripts/run-ci-tests.sh --property-only

# Skip integration tests
./scripts/run-ci-tests.sh --no-integration
```

## Manual Test Execution

Run tests directly with uv:

```bash
# Sync dependencies first
uv sync --all-extras

# Run unit tests
uv run pytest tests/unit/ -v

# Run property tests
uv run pytest tests/property/ -v

# Run integration tests
uv run pytest tests/integration/ -v -s

# Run with coverage
uv run pytest tests/unit/ --cov=scripts --cov-report=html
```

## Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/property/` - Property-based tests using Hypothesis
- `tests/integration/` - Integration tests requiring containerlab

## Environment Management

uv automatically manages the Python environment based on `pyproject.toml`:

- Dependencies are defined in `pyproject.toml`
- `uv sync` creates/updates the virtual environment
- `uv run` executes commands in the managed environment
- No need to manually activate virtual environments

## CI/CD

The CI pipeline uses the same uv-based workflow:

1. Install uv
2. Sync dependencies with `uv sync`
3. Run tests with `uv run pytest`

See `.github/workflows/` for CI configuration.
