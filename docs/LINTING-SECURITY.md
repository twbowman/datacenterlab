# Linting & Security Scanning

This project uses comprehensive linting and security scanning tools to maintain code quality and security.

## Tools Overview

### Python Linting
- **Ruff**: Fast Python linter and formatter (replaces flake8, isort, black)
- **Mypy**: Static type checker

### YAML Linting
- **yamllint**: YAML syntax and style checker

### Ansible Linting
- **ansible-lint**: Best practices checker for Ansible playbooks

### Shell Linting
- **ShellCheck**: Shell script static analysis

### Security Scanning
- **Bandit**: Python security vulnerability scanner
- **Trivy**: Comprehensive security scanner (filesystem + IaC)
- **Gitleaks**: Secret detection in git history

## Running Locally

### Install Dependencies
```bash
uv sync --all-extras
```

### Python Lint
```bash
# Check code
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type check
uv run mypy scripts/ ansible/plugins/ ansible/filter_plugins/
```

### YAML Lint
```bash
uv tool install yamllint
yamllint -c .yamllint.yml .
```

### Ansible Lint
```bash
uv tool install ansible-lint
ansible-lint ansible/
```

### Shell Lint
```bash
# Install shellcheck via package manager
# macOS: brew install shellcheck
# Ubuntu: apt install shellcheck

shellcheck scripts/*.sh
```

### Security Scans
```bash
# Bandit (Python security)
uv tool install bandit
bandit -r scripts/ ansible/plugins/ ansible/filter_plugins/

# Trivy (requires Docker)
docker run --rm -v $(pwd):/workspace aquasec/trivy fs /workspace

# Gitleaks (secret detection)
docker run --rm -v $(pwd):/path zricethezav/gitleaks:latest detect --source /path
```

## CI/CD Integration

All checks run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

View results in GitHub Actions under "Lint & Security" workflow.


## Configuration Files

- `.yamllint.yml` - YAML linting rules
- `ruff.toml` - Ruff linter/formatter config
- `.ansible-lint` - Ansible linting rules
- `.gitleaks.toml` - Secret detection allowlist
- `pyproject.toml` - Python tool configurations

## Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
set -e

echo "Running linters..."
uv run ruff check .
uv run ruff format --check .
yamllint -c .yamllint.yml .

echo "All checks passed!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Fixing Common Issues

### Ruff Format Issues
```bash
uv run ruff format .
```

### Import Sorting
```bash
uv run ruff check --select I --fix .
```

### YAML Indentation
Most YAML issues can be auto-fixed by your editor with yamllint integration.

### Ansible Warnings
Review ansible-lint output and update playbooks according to best practices.
