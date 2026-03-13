# Validation Engine API

## Overview

The Validation Engine provides automated verification of deployed network configurations, telemetry collection, and lab state. It validates that the actual network state matches expected configurations and identifies issues with specific remediation suggestions.

## Core Components

### ValidationEngine Class

The main orchestrator for all validation operations.

**Location**: `validation/engine.py`

#### Constructor

```python
from validation.engine import ValidationEngine

engine = ValidationEngine(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    prometheus_url="http://localhost:9090",
    gnmic_url="http://localhost:9273"
)
```

**Parameters**:
- `topology_file` (str): Path to containerlab topology definition
- `inventory_file` (str): Path to Ansible inventory file
- `prometheus_url` (str, optional): Prometheus API endpoint (default: "http://localhost:9090")
- `gnmic_url` (str, optional): gNMIc metrics endpoint (default: "http://localhost:9273")

#### Methods

##### validate_all()

Runs all validation checks and returns comprehensive results.

```python
result = engine.validate_all()
```

**Returns**: `ValidationReport` object containing all check results

**Example**:
```python
report = engine.validate_all()
print(f"Overall status: {report.overall_status}")
print(f"Passed: {report.summary.passed}/{report.summary.total_checks}")

for device_result in report.devices:
    print(f"\nDevice: {device_result.name}")
    for check in device_result.checks:
        if check.status == "fail":
            print(f"  ❌ {check.name}: {check.message}")
            print(f"     Remediation: {check.remediation}")
```

##### validate_deployment()

Validates that all devices are deployed and reachable.

```python
result = engine.validate_deployment()
```

**Returns**: `ValidationResult` object

**Checks**:
- All topology nodes are running containers
- All devices respond to management connections
- Device OS matches expected type

**Example**:
```python
result = engine.validate_deployment()
if result.status == "pass":
    print(f"All {len(result.details)} devices are reachable")
else:
    print(f"Deployment issues: {result.message}")
```

##### validate_configuration()

Validates deployed configurations match expected state.

```python
result = engine.validate_configuration(
    check_bgp=True,
    check_ospf=True,
    check_interfaces=True,
    check_evpn=False
)
```

**Parameters**:
- `check_bgp` (bool): Validate BGP sessions (default: True)
- `check_ospf` (bool): Validate OSPF adjacencies (default: True)
- `check_interfaces` (bool): Validate interface states (default: True)
- `check_evpn` (bool): Validate EVPN routes (default: False)
- `check_lldp` (bool): Validate LLDP neighbors (default: True)

**Returns**: `ValidationResult` object

**Example**:
```python
result = engine.validate_configuration(check_evpn=True)

for check in result.checks:
    if check.category == "bgp" and check.status == "fail":
        print(f"BGP issue on {check.device}: {check.message}")
```

##### validate_telemetry()

Validates telemetry collection is working correctly.

```python
result = engine.validate_telemetry(
    check_streaming=True,
    check_prometheus=True,
    check_normalization=True,
    check_queries=True
)
```

**Parameters**:
- `check_streaming` (bool): Verify gNMI subscriptions are active (default: True)
- `check_prometheus` (bool): Verify metrics in Prometheus (default: True)
- `check_normalization` (bool): Verify metric normalization (default: True)
- `check_queries` (bool): Verify universal queries work (default: True)

**Returns**: `ValidationResult` object

**Example**:
```python
result = engine.validate_telemetry()

if not result.passed:
    missing_devices = [d for d in result.details if d["status"] == "no_metrics"]
    print(f"Devices not streaming: {[d['name'] for d in missing_devices]}")
```

##### validate_bgp_sessions()

Validates BGP session states for all devices.

```python
result = engine.validate_bgp_sessions(
    expected_neighbors=None,  # Auto-detect from inventory
    timeout=30
)
```

**Parameters**:
- `expected_neighbors` (dict, optional): Expected BGP neighbors per device
- `timeout` (int): gNMI query timeout in seconds (default: 30)

**Returns**: `ValidationResult` object with BGP-specific details

**Example**:
```python
# Auto-detect expected neighbors from inventory
result = engine.validate_bgp_sessions()

# Or specify expected neighbors explicitly
expected = {
    "spine1": ["10.0.0.11", "10.0.0.12", "10.0.0.13", "10.0.0.14"],
    "spine2": ["10.0.0.11", "10.0.0.12", "10.0.0.13", "10.0.0.14"]
}
result = engine.validate_bgp_sessions(expected_neighbors=expected)
```

##### validate_evpn_routes()

Validates EVPN route advertisement and reception.

```python
result = engine.validate_evpn_routes(
    expected_vnis=None,  # Auto-detect from inventory
    check_route_targets=True
)
```

**Parameters**:
- `expected_vnis` (list, optional): Expected VNI list
- `check_route_targets` (bool): Verify route targets (default: True)

**Returns**: `ValidationResult` object

**Example**:
```python
result = engine.validate_evpn_routes(expected_vnis=[10100, 10200, 10300])

for device, routes in result.details.items():
    print(f"{device}: {len(routes)} EVPN routes")
```

##### validate_lldp_neighbors()

Validates LLDP neighbors match topology definition.

```python
result = engine.validate_lldp_neighbors()
```

**Returns**: `ValidationResult` object

**Example**:
```python
result = engine.validate_lldp_neighbors()

for issue in result.issues:
    if issue["type"] == "missing_neighbor":
        print(f"{issue['device']} missing neighbor: {issue['expected']}")
```

##### validate_interface_states()

Validates interface operational states.

```python
result = engine.validate_interface_states(
    check_admin_state=True,
    check_oper_state=True,
    check_mismatch=True
)
```

**Parameters**:
- `check_admin_state` (bool): Verify admin state (default: True)
- `check_oper_state` (bool): Verify operational state (default: True)
- `check_mismatch` (bool): Detect admin/oper mismatches (default: True)

**Returns**: `ValidationResult` object

**Example**:
```python
result = engine.validate_interface_states()

mismatches = [i for i in result.details if i["admin"] == "up" and i["oper"] == "down"]
for iface in mismatches:
    print(f"{iface['device']}:{iface['name']} - admin up but oper down")
```

## Data Models

### ValidationResult

Represents the result of a single validation check or group of checks.

```python
@dataclass
class ValidationResult:
    """Result of a validation check"""
    
    status: str  # "pass", "fail", "warning", "error"
    category: str  # "deployment", "bgp", "ospf", "interface", "lldp", "telemetry"
    name: str  # Human-readable check name
    message: str  # Status message
    expected: Any  # Expected value/state
    actual: Any  # Actual value/state
    remediation: str  # Suggested fix for failures
    details: Dict[str, Any]  # Additional check-specific data
    timestamp: str  # ISO8601 timestamp
    duration_seconds: float  # Check execution time
```

**Example**:
```python
result = ValidationResult(
    status="fail",
    category="bgp",
    name="BGP Session Validation",
    message="2 of 4 BGP sessions not established",
    expected=["10.0.0.11", "10.0.0.12", "10.0.0.13", "10.0.0.14"],
    actual=["10.0.0.11", "10.0.0.12"],
    remediation="Check BGP configuration on leaf3 and leaf4. Verify underlay connectivity.",
    details={
        "established": ["10.0.0.11", "10.0.0.12"],
        "missing": ["10.0.0.13", "10.0.0.14"]
    },
    timestamp="2024-01-15T10:30:00Z",
    duration_seconds=5.2
)
```

### DeviceValidationResult

Validation results for a single device.

```python
@dataclass
class DeviceValidationResult:
    """Validation results for a single device"""
    
    name: str  # Device name
    vendor: str  # Vendor (nokia, arista, sonic, juniper)
    os: str  # OS type (srlinux, eos, sonic, junos)
    checks: List[ValidationResult]  # Individual check results
    overall_status: str  # "pass", "fail", "warning"
    duration_seconds: float  # Total validation time for device
```

**Example**:
```python
device_result = DeviceValidationResult(
    name="spine1",
    vendor="nokia",
    os="srlinux",
    checks=[bgp_result, ospf_result, interface_result],
    overall_status="pass",
    duration_seconds=12.5
)
```

### ValidationReport

Complete validation report for entire lab.

```python
@dataclass
class ValidationReport:
    """Complete validation report"""
    
    timestamp: str  # ISO8601 timestamp
    lab_name: str  # Lab/topology name
    devices: List[DeviceValidationResult]  # Per-device results
    summary: ValidationSummary  # Aggregate statistics
    overall_status: str  # "pass", "fail", "warning"
    duration_seconds: float  # Total validation time
    
    def to_json(self) -> str:
        """Export report as JSON"""
        
    def to_dict(self) -> Dict:
        """Export report as dictionary"""
        
    def print_summary(self):
        """Print human-readable summary"""
```

**Example**:
```python
report = engine.validate_all()

# Export to JSON
with open("validation-report.json", "w") as f:
    f.write(report.to_json())

# Print summary
report.print_summary()
# Output:
# ✅ Validation Report - gnmi-clos
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Overall Status: PASS
# Total Checks: 24
# Passed: 22
# Failed: 0
# Warnings: 2
# Duration: 45.3s
```

### ValidationSummary

Aggregate statistics for validation report.

```python
@dataclass
class ValidationSummary:
    """Validation summary statistics"""
    
    total_checks: int
    passed: int
    failed: int
    warnings: int
    errors: int
    total_devices: int
    devices_passed: int
    devices_failed: int
```

## Usage Examples

### Basic Validation

```python
from validation.engine import ValidationEngine

# Initialize engine
engine = ValidationEngine(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml"
)

# Run all validations
report = engine.validate_all()

# Check overall status
if report.overall_status == "pass":
    print("✅ All validations passed!")
else:
    print(f"❌ Validation failed: {report.summary.failed} checks failed")
    
    # Show failures
    for device in report.devices:
        for check in device.checks:
            if check.status == "fail":
                print(f"\n{device.name} - {check.name}")
                print(f"  Expected: {check.expected}")
                print(f"  Actual: {check.actual}")
                print(f"  Fix: {check.remediation}")
```

### Selective Validation

```python
# Only validate BGP and interfaces
engine = ValidationEngine("topology.yml", "ansible/inventory.yml")

bgp_result = engine.validate_bgp_sessions()
interface_result = engine.validate_interface_states()

if bgp_result.status == "pass" and interface_result.status == "pass":
    print("✅ BGP and interfaces validated successfully")
```

### Continuous Validation

```python
import time
from validation.engine import ValidationEngine

engine = ValidationEngine("topology.yml", "ansible/inventory.yml")

while True:
    report = engine.validate_all()
    
    if report.overall_status != "pass":
        print(f"⚠️  Validation issues detected at {report.timestamp}")
        # Send alert, log issue, etc.
    
    time.sleep(300)  # Check every 5 minutes
```

### Integration with Deployment

```python
from validation.engine import ValidationEngine
import subprocess

# Deploy topology
subprocess.run(["./deploy.sh"], check=True)

# Wait for devices to boot
time.sleep(60)

# Validate deployment
engine = ValidationEngine("topology.yml", "ansible/inventory.yml")
deployment_result = engine.validate_deployment()

if deployment_result.status != "pass":
    print("❌ Deployment validation failed")
    subprocess.run(["./destroy.sh"])
    exit(1)

# Apply configuration
subprocess.run([
    "ansible-playbook",
    "-i", "ansible/inventory.yml",
    "ansible/site.yml"
], check=True)

# Validate configuration
config_result = engine.validate_configuration()

if config_result.status != "pass":
    print("❌ Configuration validation failed")
    # Rollback or alert
    exit(1)

print("✅ Lab deployed and validated successfully")
```

### Custom Validation Logic

```python
from validation.engine import ValidationEngine, ValidationResult

class CustomValidator(ValidationEngine):
    """Extended validator with custom checks"""
    
    def validate_custom_metric(self, metric_name: str, threshold: float) -> ValidationResult:
        """Validate custom metric threshold"""
        
        # Query Prometheus
        query = f'max({metric_name}) by (device)'
        response = self._query_prometheus(query)
        
        failures = []
        for result in response["data"]["result"]:
            device = result["metric"]["device"]
            value = float(result["value"][1])
            
            if value > threshold:
                failures.append({
                    "device": device,
                    "value": value,
                    "threshold": threshold
                })
        
        if failures:
            return ValidationResult(
                status="fail",
                category="custom",
                name="Custom Metric Threshold",
                message=f"{len(failures)} devices exceed threshold",
                expected=f"<= {threshold}",
                actual=failures,
                remediation="Investigate high metric values on affected devices",
                details={"failures": failures},
                timestamp=datetime.now().isoformat(),
                duration_seconds=1.0
            )
        
        return ValidationResult(
            status="pass",
            category="custom",
            name="Custom Metric Threshold",
            message="All devices within threshold",
            expected=f"<= {threshold}",
            actual="All devices OK",
            remediation="",
            details={},
            timestamp=datetime.now().isoformat(),
            duration_seconds=1.0
        )

# Use custom validator
validator = CustomValidator("topology.yml", "ansible/inventory.yml")
result = validator.validate_custom_metric("network_interface_errors_total", 100)
```

## Error Handling

The validation engine handles errors gracefully and includes them in results:

```python
try:
    result = engine.validate_bgp_sessions()
except ValidationError as e:
    print(f"Validation error: {e}")
    # Error details available in exception
    print(f"Category: {e.category}")
    print(f"Device: {e.device}")
    print(f"Details: {e.details}")
```

Common error scenarios:
- **Device unreachable**: Returns "error" status with connectivity remediation
- **gNMI timeout**: Returns "error" status with timeout details
- **Invalid configuration**: Returns "fail" status with configuration fix
- **Missing metrics**: Returns "warning" status with telemetry troubleshooting

## Performance Considerations

- **Parallel execution**: Validation checks run in parallel across devices
- **Timeout handling**: All gNMI queries have configurable timeouts
- **Caching**: Topology and inventory data cached for repeated validations
- **Target duration**: Complete validation should finish within 60 seconds

```python
# Configure performance settings
engine = ValidationEngine(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    max_workers=10,  # Parallel device checks
    gnmi_timeout=30,  # gNMI query timeout
    cache_ttl=300  # Cache topology/inventory for 5 minutes
)
```

## CLI Tool

The validation engine includes a command-line interface:

```bash
# Run all validations
./scripts/validate-lab.sh

# Run specific validation
./scripts/validate-lab.sh --check bgp

# Output JSON report
./scripts/validate-lab.sh --format json > report.json

# Fail fast (exit on first failure)
./scripts/validate-lab.sh --fail-fast

# Verbose output
./scripts/validate-lab.sh --verbose
```

## See Also

- [Architecture Guide](architecture.md) - Overall system architecture
- [State Management API](api-state-management.md) - Lab state export/restore
- [Benchmarking API](api-benchmarking.md) - Performance measurement
- [Troubleshooting Guide](../user/troubleshooting.md) - Common issues and fixes
