# UV Migration Guide

This document describes the migration from pip/venv to uv for Python environment management.

## What Changed

### Before (pip/venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/
```

### After (uv)
```bash
uv sync
uv run pytest tests/
```

## Benefits of UV

1. **Speed**: 10-100x faster than pip for package installation
2. **Simplicity**: No need to manually manage virtual environments
3. **Reproducibility**: Automatic lockfile generation (uv.lock)
4. **Modern**: Built in Rust, designed for modern Python workflows

## Files Changed

### New Files
- `pyproject.toml` - Project metadata and dependencies (replaces requirements.txt)
- `uv.lock` - Lockfile for reproducible installs (auto-generated, gitignored)
- `tests/README.md` - Testing guide with uv instructions
- `docs/developer/uv-migration.md` - This file

### Modified Files
- `scripts/run-ci-tests.sh` - Updated to use `uv run pytest`
- `.github/workflows/test.yml` - Updated CI to use uv
- `.gitignore` - Added uv.lock

### Deprecated Files
- `requirements.txt` - Kept for reference, but pyproject.toml is now the source of truth

## Installation

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Common Commands

### Install/Update Dependencies
```bash
uv sync                 # Install dependencies from pyproject.toml
uv sync --all-extras    # Install with optional dependencies
```

### Run Tests
```bash
uv run pytest tests/unit/              # Run unit tests
uv run pytest tests/property/          # Run property tests
uv run pytest tests/integration/       # Run integration tests
uv run pytest --cov=scripts            # Run with coverage
```

### Add Dependencies
```bash
# Add to pyproject.toml manually, then:
uv sync

# Or use uv to add:
uv add requests
uv add --dev pytest-mock
```

### Run Scripts
```bash
uv run python scripts/validate-topology.py
uv run python scripts/version.py
```

### CI/CD
The GitHub Actions workflow automatically:
1. Installs uv using `astral-sh/setup-uv@v4`
2. Syncs dependencies with `uv sync`
3. Runs tests with `uv run pytest`

## Migration Checklist

- [x] Create pyproject.toml with dependencies
- [x] Update test scripts to use `uv run`
- [x] Update CI/CD workflows
- [x] Update .gitignore for uv.lock
- [x] Create migration documentation
- [x] Test local execution
- [ ] Test CI/CD execution
- [ ] Update developer onboarding docs

## Troubleshooting

### "uv: command not found"
Install uv using the installation command above, then restart your shell.

### "No such file or directory: pyproject.toml"
Make sure you're in the project root directory.

### Tests fail with import errors
Run `uv sync` to ensure all dependencies are installed.

### Want to use a specific Python version
```bash
uv python install 3.9
uv python pin 3.9
uv sync
```

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [pyproject.toml Specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [GitHub Actions uv Setup](https://github.com/astral-sh/setup-uv)
