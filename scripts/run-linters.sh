#!/bin/bash
# Run all linters and security checks locally

set -e

echo "================================"
echo "Running Linters & Security Scans"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Python Lint
echo "📝 Running Ruff lint..."
if uv run ruff check .; then
    echo -e "${GREEN}✓ Ruff lint passed${NC}"
else
    echo -e "${RED}✗ Ruff lint failed${NC}"
    FAILED=1
fi
echo ""

# Python Format Check
echo "📝 Checking Ruff format..."
if uv run ruff format --check .; then
    echo -e "${GREEN}✓ Ruff format passed${NC}"
else
    echo -e "${YELLOW}⚠ Ruff format issues found. Run: uv run ruff format .${NC}"
    FAILED=1
fi
echo ""

# Type Check
echo "🔍 Running Mypy type check..."
if uv run mypy scripts/ ansible/plugins/ ansible/filter_plugins/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ Mypy passed${NC}"
else
    echo -e "${RED}✗ Mypy failed${NC}"
    FAILED=1
fi
echo ""

# YAML Lint
echo "📝 Running yamllint..."
if command -v yamllint &> /dev/null; then
    if yamllint -c .yamllint.yml .; then
        echo -e "${GREEN}✓ yamllint passed${NC}"
    else
        echo -e "${RED}✗ yamllint failed${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠ yamllint not installed. Run: uv tool install yamllint${NC}"
fi
echo ""

# Ansible Lint
echo "📝 Running ansible-lint..."
if command -v ansible-lint &> /dev/null; then
    if ansible-lint ansible/; then
        echo -e "${GREEN}✓ ansible-lint passed${NC}"
    else
        echo -e "${YELLOW}⚠ ansible-lint found issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ansible-lint not installed. Run: uv tool install ansible-lint${NC}"
fi
echo ""

# ShellCheck
echo "📝 Running ShellCheck..."
if command -v shellcheck &> /dev/null; then
    if shellcheck scripts/*.sh; then
        echo -e "${GREEN}✓ ShellCheck passed${NC}"
    else
        echo -e "${RED}✗ ShellCheck failed${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠ shellcheck not installed${NC}"
fi
echo ""

# Bandit Security
echo "🔒 Running Bandit security scan..."
if uv tool run bandit -r scripts/ ansible/plugins/ ansible/filter_plugins/ --severity-level medium; then
    echo -e "${GREEN}✓ Bandit passed${NC}"
else
    echo -e "${RED}✗ Bandit found security issues${NC}"
    FAILED=1
fi
echo ""

# Checkov IaC Security
echo "🔒 Running Checkov IaC scan..."
if command -v checkov &> /dev/null; then
    if checkov -d .github/workflows --framework github_actions --quiet --compact 2>/dev/null; then
        echo -e "${GREEN}✓ Checkov (GitHub Actions) passed${NC}"
    else
        echo -e "${RED}✗ Checkov (GitHub Actions) found issues${NC}"
        FAILED=1
    fi
    if checkov -d ansible --framework ansible --quiet --compact --soft-fail 2>/dev/null; then
        echo -e "${GREEN}✓ Checkov (Ansible) passed${NC}"
    else
        echo -e "${YELLOW}⚠ Checkov (Ansible) found issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠ checkov not installed. Run: pip install checkov${NC}"
fi
echo ""

echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    exit 1
fi
