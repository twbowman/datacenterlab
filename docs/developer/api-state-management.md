# State Management API

## Overview

The State Management API provides functionality to export, restore, compare, and incrementally update lab states. This enables reproducible test scenarios, configuration sharing, and version-controlled lab snapshots.

## Core Components

### State Export

Export complete lab state including topology, device configurations, and metrics.

**Location**: `state/export.py`

#### export_lab_state()

Exports the current lab state to a snapshot file.

```python
from state.export import export_lab_state

snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="lab-snapshot.yml",
    include_metrics=True,
    metrics_time_range="1h",
    description="Production-ready EVPN fabric configuration"
)
```

**Parameters**:
- `topology_file` (str): Path to containerlab topology definition
- `inventory_file` (str): Path to Ansible inventory file
- `output_file` (str): Output snapshot file path
- `include_metrics` (bool, optional): Include Prometheus metrics snapshot (default: True)
- `metrics_time_range` (str, optional): Metrics time range to export (default: "1h")
- `description` (str, optional): Human-readable snapshot description
- `tags` (list, optional): Tags for categorizing snapshots

**Returns**: `LabSnapshot` object

**Example**:
```python
# Basic export
snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="snapshots/evpn-fabric-v1.yml"
)

print(f"Exported {len(snapshot.devices)} devices")
print(f"Snapshot size: {snapshot.size_mb:.2f} MB")

# Export with custom settings
snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="snapshots/test-scenario.yml",
    include_metrics=False,  # Skip metrics for faster export
    description="BGP route reflector test scenario",
    tags=["bgp", "route-reflector", "test"]
)
```

#### export_device_configuration()

Exports configuration from a single device.

```python
from state.export import export_device_configuration

config = export_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    output_format="json"  # or "text"
)
```

**Parameters**:
- `device_name` (str): Device name
- `device_ip` (str): Device management IP
- `device_os` (str): Device OS type (srlinux, eos, sonic, junos)
- `output_format` (str, optional): Output format - "json" or "text" (default: "json")
- `gnmi_timeout` (int, optional): gNMI query timeout in seconds (default: 30)

**Returns**: Device configuration as string

**Example**:
```python
# Export as JSON (structured)
config_json = export_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    output_format="json"
)

# Export as text (CLI format)
config_text = export_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    output_format="text"
)

# Save to file
with open("configs/spine1-backup.json", "w") as f:
    f.write(config_json)
```

#### export_prometheus_snapshot()

Exports Prometheus metrics snapshot.

```python
from state.export import export_prometheus_snapshot

snapshot_path = export_prometheus_snapshot(
    prometheus_url="http://localhost:9090",
    time_range="2h",
    output_dir="snapshots/metrics"
)
```

**Parameters**:
- `prometheus_url` (str): Prometheus API endpoint
- `time_range` (str): Time range to export (e.g., "1h", "24h", "7d")
- `output_dir` (str): Directory for snapshot files

**Returns**: Path to snapshot directory

**Example**:
```python
# Export last 24 hours of metrics
snapshot_path = export_prometheus_snapshot(
    prometheus_url="http://localhost:9090",
    time_range="24h",
    output_dir="snapshots/metrics/2024-01-15"
)

print(f"Metrics snapshot saved to: {snapshot_path}")
```

### State Restore

Restore lab state from a snapshot file.

**Location**: `state/restore.py`

#### restore_lab_state()

Restores lab state from a snapshot file.

```python
from state.restore import restore_lab_state

result = restore_lab_state(
    snapshot_file="snapshots/evpn-fabric-v1.yml",
    restore_topology=True,
    restore_configs=True,
    restore_metrics=False,
    validate_before_restore=True,
    dry_run=False
)
```

**Parameters**:
- `snapshot_file` (str): Path to snapshot file
- `restore_topology` (bool, optional): Deploy topology (default: True)
- `restore_configs` (bool, optional): Restore device configurations (default: True)
- `restore_metrics` (bool, optional): Restore Prometheus metrics (default: False)
- `validate_before_restore` (bool, optional): Validate snapshot before restoring (default: True)
- `dry_run` (bool, optional): Simulate restore without applying changes (default: False)

**Returns**: `RestoreResult` object

**Example**:
```python
# Full restore
result = restore_lab_state(
    snapshot_file="snapshots/evpn-fabric-v1.yml"
)

if result.success:
    print(f"✅ Lab restored successfully in {result.duration_seconds:.1f}s")
    print(f"Devices restored: {len(result.devices_restored)}")
else:
    print(f"❌ Restore failed: {result.error_message}")
    for error in result.errors:
        print(f"  - {error}")

# Dry run to preview changes
result = restore_lab_state(
    snapshot_file="snapshots/test-scenario.yml",
    dry_run=True
)

print("Restore preview:")
print(f"  Topology changes: {result.topology_changes}")
print(f"  Config changes: {result.config_changes}")
print(f"  Estimated duration: {result.estimated_duration_seconds}s")

# Restore only configurations (topology already deployed)
result = restore_lab_state(
    snapshot_file="snapshots/config-only.yml",
    restore_topology=False,
    restore_configs=True
)
```

#### validate_snapshot()

Validates a snapshot file before restoration.

```python
from state.restore import validate_snapshot

validation = validate_snapshot(
    snapshot_file="snapshots/evpn-fabric-v1.yml"
)
```

**Parameters**:
- `snapshot_file` (str): Path to snapshot file

**Returns**: `SnapshotValidation` object

**Example**:
```python
validation = validate_snapshot("snapshots/evpn-fabric-v1.yml")

if validation.is_valid:
    print("✅ Snapshot is valid")
    print(f"Version: {validation.version}")
    print(f"Devices: {len(validation.devices)}")
    print(f"Created: {validation.timestamp}")
else:
    print("❌ Snapshot validation failed:")
    for error in validation.errors:
        print(f"  - {error}")
```

#### restore_device_configuration()

Restores configuration to a single device.

```python
from state.restore import restore_device_configuration

result = restore_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    configuration=config_data,
    verify_after_restore=True
)
```

**Parameters**:
- `device_name` (str): Device name
- `device_ip` (str): Device management IP
- `device_os` (str): Device OS type
- `configuration` (str or dict): Configuration to restore
- `verify_after_restore` (bool, optional): Verify configuration applied (default: True)

**Returns**: `DeviceRestoreResult` object

**Example**:
```python
# Restore from JSON config
with open("configs/spine1-backup.json") as f:
    config = f.read()

result = restore_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    configuration=config
)

if result.success:
    print(f"✅ Configuration restored to {result.device_name}")
else:
    print(f"❌ Restore failed: {result.error}")
```

### State Comparison

Compare lab snapshots to identify differences.

**Location**: `state/compare.py`

#### compare_snapshots()

Compares two lab snapshots.

```python
from state.compare import compare_snapshots

diff = compare_snapshots(
    snapshot1="snapshots/before.yml",
    snapshot2="snapshots/after.yml",
    compare_topology=True,
    compare_configs=True,
    compare_metrics=False
)
```

**Parameters**:
- `snapshot1` (str): Path to first snapshot (baseline)
- `snapshot2` (str): Path to second snapshot (comparison)
- `compare_topology` (bool, optional): Compare topology definitions (default: True)
- `compare_configs` (bool, optional): Compare device configurations (default: True)
- `compare_metrics` (bool, optional): Compare metric snapshots (default: False)

**Returns**: `SnapshotDiff` object

**Example**:
```python
diff = compare_snapshots(
    snapshot1="snapshots/v1.0.yml",
    snapshot2="snapshots/v1.1.yml"
)

print(f"Snapshot comparison: v1.0 → v1.1")
print(f"Topology changes: {len(diff.topology_changes)}")
print(f"Configuration changes: {len(diff.config_changes)}")

# Show topology changes
for change in diff.topology_changes:
    print(f"  {change.type}: {change.description}")

# Show configuration changes per device
for device, changes in diff.config_changes.items():
    print(f"\n{device}:")
    for change in changes:
        print(f"  {change.path}: {change.old_value} → {change.new_value}")

# Export diff to file
with open("diffs/v1.0-to-v1.1.json", "w") as f:
    f.write(diff.to_json())
```

#### diff_configurations()

Compares configurations between two devices or snapshots.

```python
from state.compare import diff_configurations

diff = diff_configurations(
    config1=config_before,
    config2=config_after,
    config_format="json",  # or "text"
    show_context=True,
    context_lines=3
)
```

**Parameters**:
- `config1` (str): First configuration (baseline)
- `config2` (str): Second configuration (comparison)
- `config_format` (str, optional): Configuration format - "json" or "text" (default: "json")
- `show_context` (bool, optional): Show surrounding context (default: True)
- `context_lines` (int, optional): Number of context lines (default: 3)

**Returns**: `ConfigurationDiff` object

**Example**:
```python
# Load configurations
with open("configs/spine1-before.json") as f:
    config_before = f.read()
with open("configs/spine1-after.json") as f:
    config_after = f.read()

# Compare
diff = diff_configurations(config_before, config_after)

print(f"Configuration changes: {len(diff.changes)}")

# Show changes
for change in diff.changes:
    if change.type == "added":
        print(f"+ {change.path}: {change.value}")
    elif change.type == "removed":
        print(f"- {change.path}: {change.value}")
    elif change.type == "modified":
        print(f"~ {change.path}: {change.old_value} → {change.new_value}")

# Generate unified diff
print("\nUnified diff:")
print(diff.to_unified_diff())
```

### Incremental Updates

Apply incremental state updates without full redeployment.

**Location**: `state/update.py`

#### apply_state_update()

Applies incremental state changes.

```python
from state.update import apply_state_update

result = apply_state_update(
    current_snapshot="snapshots/current.yml",
    target_snapshot="snapshots/target.yml",
    update_topology=False,  # Don't redeploy containers
    update_configs=True,
    validate_before_update=True,
    rollback_on_failure=True
)
```

**Parameters**:
- `current_snapshot` (str): Current lab state snapshot
- `target_snapshot` (str): Target lab state snapshot
- `update_topology` (bool, optional): Update topology (requires redeployment) (default: False)
- `update_configs` (bool, optional): Update device configurations (default: True)
- `validate_before_update` (bool, optional): Validate changes before applying (default: True)
- `rollback_on_failure` (bool, optional): Rollback on failure (default: True)

**Returns**: `UpdateResult` object

**Example**:
```python
# Apply incremental configuration changes
result = apply_state_update(
    current_snapshot="snapshots/current.yml",
    target_snapshot="snapshots/with-new-vlans.yml",
    update_topology=False,  # Keep existing containers
    update_configs=True
)

if result.success:
    print(f"✅ Update applied successfully")
    print(f"Devices updated: {len(result.devices_updated)}")
    print(f"Changes applied: {result.changes_applied}")
else:
    print(f"❌ Update failed: {result.error_message}")
    if result.rolled_back:
        print("⚠️  Changes were rolled back")
```

#### calculate_state_diff()

Calculates the difference between current and target states.

```python
from state.update import calculate_state_diff

diff = calculate_state_diff(
    current_snapshot="snapshots/current.yml",
    target_snapshot="snapshots/target.yml"
)
```

**Parameters**:
- `current_snapshot` (str): Current state snapshot
- `target_snapshot` (str): Target state snapshot

**Returns**: `StateDiff` object

**Example**:
```python
diff = calculate_state_diff(
    current_snapshot="snapshots/current.yml",
    target_snapshot="snapshots/target.yml"
)

print(f"State differences:")
print(f"  Topology changes: {diff.requires_redeployment}")
print(f"  Configuration changes: {len(diff.config_changes)}")
print(f"  Devices affected: {len(diff.affected_devices)}")

# Preview changes before applying
for device in diff.affected_devices:
    changes = diff.get_device_changes(device)
    print(f"\n{device}:")
    for change in changes:
        print(f"  {change}")
```

## Data Models

### LabSnapshot

Represents a complete lab state snapshot.

```python
@dataclass
class LabSnapshot:
    """Complete lab state snapshot"""
    
    version: str  # Snapshot format version
    timestamp: str  # ISO8601 timestamp
    lab_name: str  # Lab/topology name
    description: str  # Human-readable description
    tags: List[str]  # Categorization tags
    
    topology: Dict  # Topology definition
    devices: List[DeviceSnapshot]  # Device configurations
    metrics_snapshot: Optional[str]  # Path to Prometheus snapshot
    
    metadata: Dict[str, Any]  # Additional metadata
    size_mb: float  # Snapshot size in MB
    
    def to_yaml(self) -> str:
        """Export as YAML"""
    
    def to_json(self) -> str:
        """Export as JSON"""
    
    def save(self, output_file: str):
        """Save to file"""
```

**Example**:
```python
snapshot = LabSnapshot(
    version="1.0",
    timestamp="2024-01-15T10:30:00Z",
    lab_name="evpn-fabric",
    description="Production EVPN/VXLAN fabric with 2 spines and 4 leafs",
    tags=["evpn", "vxlan", "production"],
    topology=topology_data,
    devices=device_snapshots,
    metrics_snapshot="snapshots/metrics/2024-01-15",
    metadata={"created_by": "admin", "environment": "lab"},
    size_mb=15.3
)

# Save as YAML (version control friendly)
snapshot.save("snapshots/evpn-fabric-v1.yml")
```

### DeviceSnapshot

Configuration snapshot for a single device.

```python
@dataclass
class DeviceSnapshot:
    """Device configuration snapshot"""
    
    name: str  # Device name
    vendor: str  # Vendor (nokia, arista, sonic, juniper)
    os: str  # OS type (srlinux, eos, sonic, junos)
    os_version: str  # OS version
    management_ip: str  # Management IP address
    
    configuration: str  # Full device configuration
    config_format: str  # "json" or "text"
    
    timestamp: str  # When configuration was captured
    checksum: str  # Configuration checksum (SHA256)
```

### RestoreResult

Result of a lab state restoration.

```python
@dataclass
class RestoreResult:
    """Lab state restore result"""
    
    success: bool  # Overall success status
    snapshot_file: str  # Source snapshot file
    
    topology_restored: bool  # Topology deployment status
    devices_restored: List[str]  # Successfully restored devices
    devices_failed: List[str]  # Failed device restorations
    
    errors: List[str]  # Error messages
    error_message: str  # Primary error message
    
    duration_seconds: float  # Total restore time
    timestamp: str  # When restore completed
```

### SnapshotDiff

Difference between two lab snapshots.

```python
@dataclass
class SnapshotDiff:
    """Difference between two snapshots"""
    
    snapshot1: str  # First snapshot file (baseline)
    snapshot2: str  # Second snapshot file (comparison)
    
    topology_changes: List[TopologyChange]  # Topology differences
    config_changes: Dict[str, List[ConfigChange]]  # Per-device config changes
    
    devices_added: List[str]  # New devices in snapshot2
    devices_removed: List[str]  # Devices removed from snapshot1
    devices_modified: List[str]  # Devices with configuration changes
    
    def to_json(self) -> str:
        """Export as JSON"""
    
    def to_html(self) -> str:
        """Generate HTML diff report"""
```

### UpdateResult

Result of an incremental state update.

```python
@dataclass
class UpdateResult:
    """Incremental update result"""
    
    success: bool  # Overall success status
    
    devices_updated: List[str]  # Successfully updated devices
    devices_failed: List[str]  # Failed device updates
    changes_applied: int  # Number of changes applied
    
    rolled_back: bool  # Whether rollback was performed
    error_message: str  # Primary error message
    
    duration_seconds: float  # Update duration
```

## Usage Examples

### Export and Restore Workflow

```python
from state.export import export_lab_state
from state.restore import restore_lab_state

# Export current lab state
print("Exporting lab state...")
snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file="snapshots/baseline.yml",
    description="Baseline configuration before changes"
)

print(f"✅ Exported {len(snapshot.devices)} devices")

# Make changes to lab...
# (deploy new configs, test scenarios, etc.)

# Restore to baseline
print("\nRestoring to baseline...")
result = restore_lab_state(
    snapshot_file="snapshots/baseline.yml"
)

if result.success:
    print(f"✅ Restored to baseline in {result.duration_seconds:.1f}s")
```

### Configuration Backup and Restore

```python
from state.export import export_device_configuration
from state.restore import restore_device_configuration

# Backup device configuration
print("Backing up spine1 configuration...")
config = export_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux"
)

with open("backups/spine1-backup.json", "w") as f:
    f.write(config)

# Make changes...

# Restore from backup
print("Restoring spine1 configuration...")
with open("backups/spine1-backup.json") as f:
    config = f.read()

result = restore_device_configuration(
    device_name="spine1",
    device_ip="172.20.20.10",
    device_os="srlinux",
    configuration=config
)

if result.success:
    print("✅ Configuration restored")
```

### Compare Snapshots

```python
from state.compare import compare_snapshots

# Compare two versions
diff = compare_snapshots(
    snapshot1="snapshots/v1.0.yml",
    snapshot2="snapshots/v1.1.yml"
)

print("Changes from v1.0 to v1.1:")
print(f"  Devices added: {diff.devices_added}")
print(f"  Devices removed: {diff.devices_removed}")
print(f"  Devices modified: {len(diff.devices_modified)}")

# Show detailed changes
for device in diff.devices_modified:
    changes = diff.config_changes[device]
    print(f"\n{device}: {len(changes)} changes")
    for change in changes[:5]:  # Show first 5 changes
        print(f"  {change.type}: {change.path}")
```

### Incremental Updates

```python
from state.update import apply_state_update, calculate_state_diff

# Preview changes
diff = calculate_state_diff(
    current_snapshot="snapshots/current.yml",
    target_snapshot="snapshots/with-new-bgp-peers.yml"
)

print(f"Preview: {len(diff.config_changes)} configuration changes")
print(f"Requires redeployment: {diff.requires_redeployment}")

# Apply changes
if not diff.requires_redeployment:
    result = apply_state_update(
        current_snapshot="snapshots/current.yml",
        target_snapshot="snapshots/with-new-bgp-peers.yml",
        update_topology=False,
        update_configs=True
    )
    
    if result.success:
        print(f"✅ Applied {result.changes_applied} changes")
    else:
        print(f"❌ Update failed: {result.error_message}")
else:
    print("⚠️  Changes require full redeployment")
```

### Version Control Integration

```python
from state.export import export_lab_state
import subprocess
import datetime

# Export lab state
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
snapshot_file = f"snapshots/lab-{timestamp}.yml"

snapshot = export_lab_state(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    output_file=snapshot_file,
    include_metrics=False,  # Metrics not suitable for git
    description=f"Lab snapshot {timestamp}"
)

# Commit to git
subprocess.run(["git", "add", snapshot_file], check=True)
subprocess.run([
    "git", "commit", "-m",
    f"Lab snapshot: {len(snapshot.devices)} devices"
], check=True)

print(f"✅ Snapshot committed to git: {snapshot_file}")
```

## CLI Tools

### Export Lab State

```bash
# Export current lab state
./scripts/export-lab-state.sh --output snapshots/current.yml

# Export with description
./scripts/export-lab-state.sh \
    --output snapshots/evpn-fabric.yml \
    --description "EVPN fabric with BGP route reflectors" \
    --tags "evpn,bgp,production"

# Export without metrics (faster)
./scripts/export-lab-state.sh \
    --output snapshots/config-only.yml \
    --no-metrics
```

### Restore Lab State

```bash
# Restore from snapshot
./scripts/restore-lab-state.sh snapshots/evpn-fabric.yml

# Dry run (preview changes)
./scripts/restore-lab-state.sh snapshots/evpn-fabric.yml --dry-run

# Restore only configurations
./scripts/restore-lab-state.sh snapshots/config-only.yml --no-topology

# Skip validation (faster but risky)
./scripts/restore-lab-state.sh snapshots/current.yml --no-validate
```

### Compare Snapshots

```bash
# Compare two snapshots
./scripts/compare-states.sh snapshots/v1.0.yml snapshots/v1.1.yml

# Output JSON diff
./scripts/compare-states.sh \
    snapshots/before.yml \
    snapshots/after.yml \
    --format json > diff.json

# Show only configuration changes
./scripts/compare-states.sh \
    snapshots/v1.0.yml \
    snapshots/v1.1.yml \
    --configs-only
```

## Best Practices

1. **Regular Snapshots**: Export lab state before major changes
2. **Descriptive Names**: Use meaningful snapshot names and descriptions
3. **Version Control**: Store snapshots in git (without metrics)
4. **Validation**: Always validate snapshots before restoration
5. **Incremental Updates**: Use incremental updates when possible to avoid redeployment
6. **Backup Configs**: Keep device configuration backups separate from full snapshots
7. **Metrics Handling**: Metrics snapshots are large; export separately if needed

## See Also

- [Validation Engine API](api-validation-engine.md) - Configuration validation
- [Benchmarking API](api-benchmarking.md) - Performance measurement
- [Architecture Guide](architecture.md) - Overall system architecture
- [Configuration Guide](../user/configuration.md) - Lab configuration
