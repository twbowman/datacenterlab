# API Reference

## Overview

This document provides an index to all API documentation for the Production Network Testing Lab. The lab provides three main programmatic APIs for validation, state management, and performance benchmarking.

## API Documentation

### [Validation Engine API](api-validation-engine.md)

Automated verification of deployed network configurations, telemetry collection, and lab state.

**Key Features**:
- Validate deployment (device reachability, OS detection)
- Validate configurations (BGP sessions, EVPN routes, LLDP neighbors, interface states)
- Validate telemetry (streaming status, metric normalization, Prometheus ingestion)
- Generate comprehensive validation reports with remediation suggestions
- Integration with deployment workflows

**Main Classes**:
- `ValidationEngine` - Main orchestrator for validation operations
- `ValidationResult` - Result of a single validation check
- `ValidationReport` - Complete validation report for entire lab

**Common Use Cases**:
```python
from validation.engine import ValidationEngine

# Validate entire lab
engine = ValidationEngine("topology.yml", "ansible/inventory.yml")
report = engine.validate_all()

# Validate specific components
bgp_result = engine.validate_bgp_sessions()
telemetry_result = engine.validate_telemetry()
```

**See**: [Full Validation Engine API Documentation](api-validation-engine.md)

---

### [State Management API](api-state-management.md)

Export, restore, compare, and incrementally update lab states for reproducible test scenarios.

**Key Features**:
- Export complete lab state (topology, configurations, metrics)
- Restore lab from snapshots with validation
- Compare snapshots to identify differences
- Apply incremental updates without full redeployment
- Version control friendly snapshot format (YAML)

**Main Functions**:
- `export_lab_state()` - Export current lab state to snapshot
- `restore_lab_state()` - Restore lab from snapshot
- `compare_snapshots()` - Compare two lab snapshots
- `apply_state_update()` - Apply incremental changes

**Common Use Cases**:
```python
from state.export import export_lab_state
from state.restore import restore_lab_state
from state.compare import compare_snapshots

# Export current state
snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="snapshots/baseline.yml"
)

# Restore from snapshot
result = restore_lab_state(snapshot_file="snapshots/baseline.yml")

# Compare snapshots
diff = compare_snapshots("snapshots/v1.yml", "snapshots/v2.yml")
```

**See**: [Full State Management API Documentation](api-state-management.md)

---

### [Benchmarking API](api-benchmarking.md)

Comprehensive performance measurement and analysis for deployment, configuration, telemetry, and resource usage.

**Key Features**:
- Benchmark deployment times across topology sizes
- Measure configuration deployment performance
- Measure telemetry collection overhead (CPU, latency, ingestion rate)
- Monitor resource usage (CPU, memory, storage)
- Compare vendor performance
- Identify performance bottlenecks with recommendations

**Main Classes**:
- `BenchmarkRunner` - Main orchestrator for benchmarking operations
- `BenchmarkReport` - Complete benchmark report with all measurements
- `VendorComparison` - Performance comparison across vendors
- `BottleneckAnalysis` - Performance bottleneck identification

**Common Use Cases**:
```python
from benchmarks.framework import BenchmarkRunner

# Run all benchmarks
runner = BenchmarkRunner("topology.yml", "ansible/inventory.yml")
report = runner.benchmark_all(iterations=5)

# Benchmark specific components
deployment = runner.benchmark_deployment(topology_sizes=[2, 4, 8, 16])
telemetry = runner.benchmark_telemetry(duration_seconds=600)

# Compare vendors
comparison = runner.compare_vendors(
    metrics=["deployment_time", "config_time", "cpu_usage"]
)
```

**See**: [Full Benchmarking API Documentation](api-benchmarking.md)

---

## Quick Start

### Installation

The APIs are part of the lab environment. Ensure you have the lab dependencies installed:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r ansible/requirements.yml
```

### Basic Usage Example

Here's a complete example using all three APIs:

```python
from validation.engine import ValidationEngine
from state.export import export_lab_state
from benchmarks.framework import BenchmarkRunner

# 1. Validate lab is working
print("Validating lab...")
validator = ValidationEngine("topology.yml", "ansible/inventory.yml")
validation = validator.validate_all()

if validation.overall_status != "pass":
    print(f"❌ Validation failed: {validation.summary.failed} checks failed")
    exit(1)

print("✅ Lab validation passed")

# 2. Export current state
print("\nExporting lab state...")
snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="snapshots/current.yml",
    description="Validated lab state"
)
print(f"✅ Exported {len(snapshot.devices)} devices")

# 3. Run performance benchmarks
print("\nRunning benchmarks...")
benchmarker = BenchmarkRunner("topology.yml", "ansible/inventory.yml")
report = benchmarker.benchmark_all(iterations=3)

print(f"✅ Benchmarks complete:")
print(f"   Deployment: {report.deployment.mean_time:.1f}s")
print(f"   Configuration: {report.configuration.total_time.mean:.1f}s")
print(f"   Telemetry CPU: {report.telemetry.cpu_overhead_percent:.2f}%")

# Save results
report.save("benchmarks/results/report.json")
```

## API Design Principles

All APIs follow these design principles:

1. **Consistent Interface**: Similar patterns across all APIs
2. **Type Safety**: Use dataclasses for structured data
3. **Error Handling**: Graceful error handling with detailed messages
4. **Extensibility**: Easy to extend with custom checks/benchmarks
5. **Documentation**: Comprehensive docstrings and examples
6. **CLI Integration**: All APIs accessible via command-line tools

## Data Model Conventions

### Common Patterns

All APIs use consistent data model patterns:

```python
# Results always include status
result.status  # "pass", "fail", "warning", "error"

# Timestamps are ISO8601
result.timestamp  # "2024-01-15T10:30:00Z"

# Durations are in seconds
result.duration_seconds  # 45.3

# All results can be exported
result.to_json()  # Export as JSON
result.to_dict()  # Export as dictionary
result.save(file)  # Save to file
```

### Status Values

Standard status values across all APIs:

- `pass` - Check/operation succeeded
- `fail` - Check/operation failed
- `warning` - Non-critical issue detected
- `error` - Unexpected error occurred

## CLI Tools

Each API includes command-line tools:

### Validation

```bash
./scripts/validate-lab.sh
./scripts/validate-lab.sh --check bgp
./scripts/validate-lab.sh --format json
```

### State Management

```bash
./scripts/export-lab-state.sh --output snapshots/current.yml
./scripts/restore-lab-state.sh snapshots/baseline.yml
./scripts/compare-states.sh snapshots/v1.yml snapshots/v2.yml
```

### Benchmarking

```bash
./scripts/run-benchmarks.sh
./scripts/run-benchmarks.sh --type deployment
./scripts/compare-vendor-performance.sh
```

## Integration Examples

### CI/CD Integration

```python
# In CI pipeline
from validation.engine import ValidationEngine
import sys

engine = ValidationEngine("topology.yml", "ansible/inventory.yml")
report = engine.validate_all()

if report.overall_status != "pass":
    print("Validation failed!")
    report.print_summary()
    sys.exit(1)

print("Validation passed!")
```

### Automated Testing

```python
# In test suite
from state.export import export_lab_state
from state.restore import restore_lab_state

def test_configuration_change():
    # Export baseline
    baseline = export_lab_state(
        topology_file="topology.yml",
        inventory_file="ansible/inventory.yml",
        output_file="/tmp/baseline.yml"
    )
    
    # Apply changes
    apply_configuration_changes()
    
    # Validate changes
    validator = ValidationEngine("topology.yml", "ansible/inventory.yml")
    result = validator.validate_configuration()
    
    assert result.status == "pass"
    
    # Restore baseline
    restore_lab_state(snapshot_file="/tmp/baseline.yml")
```

### Performance Monitoring

```python
# Continuous performance monitoring
from benchmarks.framework import BenchmarkRunner
import time

runner = BenchmarkRunner("topology.yml", "ansible/inventory.yml")

while True:
    result = runner.benchmark_telemetry(duration_seconds=60)
    
    if result.cpu_overhead_percent > 5.0:
        send_alert(f"Telemetry CPU overhead: {result.cpu_overhead_percent:.2f}%")
    
    time.sleep(300)  # Check every 5 minutes
```

## Error Handling

All APIs use consistent error handling:

```python
from validation.engine import ValidationEngine, ValidationError

try:
    engine = ValidationEngine("topology.yml", "ansible/inventory.yml")
    result = engine.validate_all()
except ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Category: {e.category}")
    print(f"Details: {e.details}")
except FileNotFoundError as e:
    print(f"Configuration file not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Validation Engine

- Parallel execution across devices
- Configurable timeouts for gNMI queries
- Caching of topology and inventory data
- Target: Complete validation within 60 seconds

### State Management

- Streaming export for large configurations
- Incremental updates to avoid full redeployment
- Compression for large snapshots
- Version control friendly YAML format

### Benchmarking

- Multiple iterations for statistical significance
- Warm-up iterations to avoid cold start effects
- Resource monitoring with minimal overhead
- Parallel benchmark execution where possible

## Best Practices

1. **Validation**: Run validation after every configuration change
2. **State Management**: Export state before major changes
3. **Benchmarking**: Establish baseline and track trends over time
4. **Error Handling**: Always check result status before proceeding
5. **Logging**: Enable verbose logging for troubleshooting
6. **Documentation**: Document custom extensions and integrations

## Related Documentation

- [Architecture Guide](architecture.md) - Overall system architecture
- [Vendor Extension Guide](vendor-extension.md) - Adding new vendors
- [Contributing Guide](contributing.md) - Development guidelines
- [User Documentation](../user/setup.md) - Lab setup and usage

## Support and Contribution

For questions, issues, or contributions:

1. Check existing documentation
2. Review example code in this guide
3. See [Contributing Guide](contributing.md) for development process
4. Open an issue for bugs or feature requests

## Version History

- **v1.0** (2024-01) - Initial API documentation
  - Validation Engine API
  - State Management API
  - Benchmarking API
