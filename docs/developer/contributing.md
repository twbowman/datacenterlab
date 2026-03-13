# Contribution Guide

## Overview

Thank you for your interest in contributing to the Production Network Testing Lab! This guide explains our development process, code standards, testing requirements, and pull request guidelines.

**Validates: Requirements 10.1, 13.1**

## Getting Started

### Prerequisites

- Python 3.8+
- Ansible 2.10+
- Docker 20.10+
- Containerlab 0.40+
- Git

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/org/production-network-testing-lab.git
cd production-network-testing-lab

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r ansible/requirements.yml

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify installation
./scripts/verify-environment.sh
```

### Project Structure

```
production-network-testing-lab/
├── ansible/                 # Ansible automation
│   ├── methods/            # Vendor-specific methods
│   ├── roles/              # Shared roles
│   ├── plugins/            # Custom plugins
│   └── site.yml            # Main playbook
├── monitoring/             # Telemetry and monitoring
│   ├── gnmic/             # gNMIc configuration
│   ├── prometheus/        # Prometheus configuration
│   └── grafana/           # Grafana dashboards
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── property/          # Property-based tests
├── docs/                   # Documentation
│   ├── user/              # User documentation
│   └── developer/         # Developer documentation
├── scripts/                # Utility scripts
├── topologies/            # Topology definitions
└── configs/               # Device configurations
```

## Development Workflow

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/add-sonic-support

# Create bugfix branch
git checkout -b bugfix/fix-bgp-validation

# Create documentation branch
git checkout -b docs/update-vendor-guide
```

### Branch Naming Convention

- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Changes

Follow our code style guidelines (see below) and write tests for your changes.

### 3. Test Your Changes

```bash
# Run linters
./scripts/lint.sh

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run property-based tests
pytest tests/property/ -v

# Run all tests
pytest tests/ -v --cov=ansible --cov=monitoring
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add SONiC BGP configuration role

- Implement SONiC BGP role using REST API
- Add BGP session validation
- Include integration tests
- Update documentation

Closes #123"
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/improvements
- `refactor`: Code refactoring
- `style`: Code style changes (formatting)
- `chore`: Maintenance tasks

**Example**:
```
feat: Add Arista cEOS EVPN/VXLAN support

- Implement eos_evpn_vxlan role
- Add EVPN route validation
- Include integration tests for EVPN fabric
- Update vendor extension guide

Validates: Requirements 2.1, 7.2
Closes #45
```

### 5. Push and Create Pull Request

```bash
# Push branch
git push origin feature/add-sonic-support

# Create pull request on GitHub
# Fill out PR template
```

## Code Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Good: Clear, descriptive names
def detect_os_via_gnmi(host: str, port: int = 57400) -> str:
    """
    Detect device OS via gNMI capabilities.
    
    Args:
        host: Device hostname or IP address
        port: gNMI port (default: 57400)
    
    Returns:
        OS name (srlinux, eos, sonic, junos) or "unknown"
    
    Raises:
        ConnectionError: If device is unreachable
    """
    try:
        capabilities = gnmi_capabilities(host, port)
        
        if "Nokia" in capabilities.supported_models:
            return "srlinux"
        elif "Arista" in capabilities.supported_models:
            return "eos"
        
        return "unknown"
    
    except Exception as e:
        logger.warning(f"Could not detect OS for {host}: {e}")
        return "unknown"

# Bad: Unclear names, no docstring
def detect(h, p=57400):
    c = gnmi_capabilities(h, p)
    if "Nokia" in c.supported_models:
        return "srlinux"
    return "unknown"
```

**Key Points**:
- Use type hints
- Write docstrings for all functions
- Use descriptive variable names
- Handle exceptions appropriately
- Log errors with context
- Maximum line length: 100 characters

### Ansible Code Style

```yaml
# Good: Clear task names, proper indentation
- name: Configure BGP on SR Linux
  gnmi_set:
    path: /network-instance[name=default]/protocols/bgp
    value:
      autonomous-system: "{{ bgp_asn }}"
      router-id: "{{ router_id }}"
      neighbor:
        - peer-address: "{{ item.ip }}"
          peer-as: "{{ item.peer_as }}"
  loop: "{{ bgp_neighbors }}"
  when: bgp_neighbors is defined
  register: bgp_config
  tags: [bgp, config]

# Bad: Unclear names, inconsistent indentation
- name: bgp
  gnmi_set:
    path: /network-instance[name=default]/protocols/bgp
    value:
      autonomous-system: "{{bgp_asn}}"
  loop: "{{bgp_neighbors}}"
```

**Key Points**:
- Use descriptive task names
- Consistent 2-space indentation
- Use `when` for conditionals
- Use `register` for task results
- Add tags for selective execution
- Use `{{ variable }}` with spaces

### YAML Style

```yaml
# Good: Consistent formatting
targets:
  spine1:
    address: 172.20.20.10:57400
    username: admin
    password: NokiaSrl1!
    skip-verify: true
    tags:
      vendor: nokia
      os: srlinux
      role: spine

# Bad: Inconsistent formatting
targets:
  spine1:
    address: 172.20.20.10:57400
    username: admin
    password: NokiaSrl1!
    skip-verify: true
    tags: {vendor: nokia, os: srlinux, role: spine}
```

**Key Points**:
- Use 2-space indentation
- Use block style (not flow style)
- Quote strings with special characters
- Consistent key ordering

### Shell Script Style

```bash
#!/bin/bash
# Good: Error handling, clear output

set -euo pipefail

readonly TOPOLOGY_FILE="${1:-topology.yml}"
readonly WAIT_TIME=120

main() {
    echo "Deploying topology: ${TOPOLOGY_FILE}"
    
    if ! sudo containerlab deploy -t "${TOPOLOGY_FILE}"; then
        echo "Error: Deployment failed" >&2
        return 1
    fi
    
    echo "Waiting ${WAIT_TIME}s for devices to boot..."
    sleep "${WAIT_TIME}"
    
    echo "Deployment complete"
}

main "$@"

# Bad: No error handling, unclear
#!/bin/bash
sudo containerlab deploy -t $1
sleep 120
```

**Key Points**:
- Use `set -euo pipefail`
- Use `readonly` for constants
- Quote variables
- Use functions
- Handle errors
- Provide clear output

## Testing Requirements

### Unit Tests

**Required for**:
- All Python functions
- Ansible filter plugins
- Validation logic
- Utility scripts

**Example**:
```python
# tests/unit/test_os_detection.py
import pytest
from ansible.plugins.inventory.dynamic_inventory import detect_os_via_gnmi

def test_detect_srlinux():
    """Test SR Linux OS detection"""
    # Mock gNMI capabilities
    with patch('gnmi_capabilities') as mock_gnmi:
        mock_gnmi.return_value.supported_models = ["Nokia SR Linux"]
        
        result = detect_os_via_gnmi("172.20.20.10")
        
        assert result == "srlinux"

def test_detect_unknown():
    """Test unknown OS detection"""
    with patch('gnmi_capabilities') as mock_gnmi:
        mock_gnmi.return_value.supported_models = ["Unknown Device"]
        
        result = detect_os_via_gnmi("172.20.20.10")
        
        assert result == "unknown"

def test_detect_connection_error():
    """Test OS detection with connection error"""
    with patch('gnmi_capabilities') as mock_gnmi:
        mock_gnmi.side_effect = ConnectionError("Device unreachable")
        
        result = detect_os_via_gnmi("172.20.20.10")
        
        assert result == "unknown"
```

### Integration Tests

**Required for**:
- New vendor support
- Configuration roles
- Telemetry collection
- End-to-end workflows

**Example**:
```python
# tests/integration/test_sonic_integration.py
import pytest
from tests.helpers import deploy_topology, configure_device

@pytest.fixture(scope="module")
def sonic_topology():
    """Deploy topology with SONiC device"""
    topology = deploy_topology("topology-sonic-test.yml")
    yield topology
    topology.destroy()

def test_sonic_bgp_configuration(sonic_topology):
    """Test SONiC BGP configuration"""
    device = sonic_topology.get_device("sonic-leaf1")
    
    config = {
        "bgp_asn": 65001,
        "router_id": "10.0.0.1",
        "bgp_neighbors": [
            {"ip": "10.1.1.1", "peer_as": 65002}
        ]
    }
    
    result = configure_device(device, config)
    
    assert result.success
    assert result.changed
    
    # Verify BGP session
    bgp_state = device.get_bgp_state()
    assert bgp_state["10.1.1.1"]["state"] == "Established"
```

### Property-Based Tests

**Required for**:
- Configuration idempotency
- Metric normalization
- Round-trip properties
- State management

**Example**:
```python
# tests/property/test_configuration_properties.py
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(config=st.bgp_configurations())
def test_configuration_idempotency(config):
    """
    Property: Applying the same configuration multiple times
    should produce identical device state.
    """
    device = get_test_device()
    
    # Apply configuration first time
    apply_configuration(device, config)
    state1 = get_device_state(device)
    
    # Apply same configuration second time
    apply_configuration(device, config)
    state2 = get_device_state(device)
    
    # States should be identical
    assert state1 == state2
```

### Test Coverage Requirements

- **Minimum coverage**: 80%
- **Critical paths**: 100% (OS detection, configuration, rollback)
- **New features**: Must include tests
- **Bug fixes**: Must include regression test

### Running Tests

```bash
# Run specific test file
pytest tests/unit/test_os_detection.py -v

# Run with coverage
pytest tests/ --cov=ansible --cov=monitoring --cov-report=html

# Run only fast tests
pytest tests/ -m "not slow"

# Run with verbose output
pytest tests/ -vv

# Run and stop on first failure
pytest tests/ -x
```

## Pull Request Guidelines

### PR Template

When creating a pull request, fill out the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Test improvement

## Changes Made
- Detailed list of changes
- Include file paths
- Explain design decisions

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Property tests added/updated (if applicable)
- [ ] All tests passing
- [ ] Coverage maintained/improved

## Documentation
- [ ] Code comments added
- [ ] Docstrings updated
- [ ] User documentation updated
- [ ] Developer documentation updated
- [ ] CHANGELOG.md updated

## Validation
- [ ] Requirements validated (list requirement numbers)
- [ ] Design document updated (if needed)
- [ ] Breaking changes documented

## Checklist
- [ ] Code follows style guidelines
- [ ] Commits follow commit message format
- [ ] Branch is up to date with main
- [ ] No merge conflicts
- [ ] CI/CD pipeline passing
```

### PR Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linters
2. **Code Review**: At least one maintainer reviews code
3. **Testing**: Reviewer tests changes in their environment
4. **Approval**: Maintainer approves PR
5. **Merge**: Maintainer merges PR

### PR Review Criteria

**Code Quality**:
- Follows style guidelines
- Well-documented
- No unnecessary complexity
- Proper error handling

**Testing**:
- Adequate test coverage
- Tests are meaningful
- All tests passing
- No flaky tests

**Documentation**:
- Code is documented
- User docs updated
- Developer docs updated
- Examples provided

**Design**:
- Follows architecture patterns
- Maintains backward compatibility
- Considers production use
- Scalable solution

## Documentation Standards

### Code Documentation

```python
def normalize_metric(metric: dict, vendor: str) -> dict:
    """
    Normalize vendor-specific metric to OpenConfig format.
    
    This function transforms vendor-specific metric names and labels
    to universal OpenConfig paths, enabling vendor-agnostic queries.
    
    Args:
        metric: Vendor-specific metric dictionary with keys:
            - name: Metric name (e.g., "/srl_nokia/interface/statistics/in-octets")
            - labels: Metric labels (e.g., {"interface": "ethernet-1/1"})
            - value: Metric value
            - timestamp: Unix timestamp
        vendor: Vendor name (srlinux, eos, sonic, junos)
    
    Returns:
        Normalized metric dictionary with OpenConfig name and labels
    
    Raises:
        ValueError: If vendor is not supported
        KeyError: If required metric fields are missing
    
    Example:
        >>> metric = {
        ...     "name": "/srl_nokia/interface/statistics/in-octets",
        ...     "labels": {"interface": "ethernet-1/1"},
        ...     "value": 123456,
        ...     "timestamp": 1705315800
        ... }
        >>> normalize_metric(metric, "srlinux")
        {
            "name": "network_interface_in_octets",
            "labels": {"interface": "eth1_1", "vendor": "nokia"},
            "value": 123456,
            "timestamp": 1705315800
        }
    """
    if vendor not in SUPPORTED_VENDORS:
        raise ValueError(f"Unsupported vendor: {vendor}")
    
    # Implementation...
```

### User Documentation

- **Audience**: Network engineers using the lab
- **Style**: Step-by-step instructions
- **Format**: Markdown with code examples
- **Location**: `docs/user/`

### Developer Documentation

- **Audience**: Contributors extending the lab
- **Style**: Technical explanations with examples
- **Format**: Markdown with diagrams
- **Location**: `docs/developer/`

### Inline Comments

```python
# Good: Explain why, not what
# Use exponential backoff to avoid overwhelming device during reconnection
retry_delay = min(2 ** attempt, 300)

# Bad: Explain what (obvious from code)
# Set retry_delay to 2 to the power of attempt
retry_delay = 2 ** attempt
```

## Continuous Integration

### CI/CD Pipeline

Our CI/CD pipeline runs on every push and pull request:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run linters
        run: ./scripts/lint.sh
  
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup containerlab
        run: bash -c "$(curl -sL https://get.containerlab.dev)"
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

### Required Checks

All PRs must pass:
- ✅ Linting (Python, YAML, Shell)
- ✅ Unit tests (>80% coverage)
- ✅ Integration tests
- ✅ Documentation build
- ✅ Code review approval

## Release Process

### Versioning

We use Semantic Versioning (SemVer):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features (backward compatible)
- **Patch** (0.0.1): Bug fixes

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Git tag created
- [ ] Release notes written
- [ ] Announcement posted

## Getting Help

### Communication Channels

- **Slack**: #network-lab-dev
- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bugs and feature requests
- **Email**: network-lab@example.com

### Resources

- **Documentation**: `docs/`
- **Examples**: `topologies/examples/`
- **Tests**: `tests/`
- **Architecture**: `docs/developer/architecture.md`
- **Vendor Extension**: `docs/developer/vendor-extension.md`

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Violations will result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report violations to: conduct@example.com

## Recognition

### Contributors

We recognize contributors in:
- CONTRIBUTORS.md file
- Release notes
- Project README
- Annual contributor report

### Contribution Types

We value all contributions:
- Code contributions
- Documentation improvements
- Bug reports
- Feature suggestions
- Code reviews
- Community support

## FAQ

### Q: How do I add a new vendor?

A: See `docs/developer/vendor-extension.md` for step-by-step guide.

### Q: How do I run tests locally?

A: Run `pytest tests/ -v` after setting up development environment.

### Q: What if my PR fails CI checks?

A: Review the CI logs, fix issues, and push updates. CI will re-run automatically.

### Q: How long does PR review take?

A: Usually 1-3 business days. Complex PRs may take longer.

### Q: Can I work on multiple features simultaneously?

A: Yes, but create separate branches and PRs for each feature.

### Q: How do I update my branch with latest main?

A: `git fetch origin && git rebase origin/main`

## Summary

Contributing to the Production Network Testing Lab:

1. **Setup**: Install dependencies, create branch
2. **Develop**: Follow code style, write tests
3. **Test**: Run linters and tests locally
4. **Document**: Update relevant documentation
5. **Submit**: Create PR with detailed description
6. **Review**: Address reviewer feedback
7. **Merge**: Maintainer merges approved PR

Thank you for contributing! Your efforts help make this lab better for everyone.
