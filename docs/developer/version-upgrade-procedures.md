# Version Upgrade Procedures

This document describes procedures for upgrading between versions of the Production Network Testing Lab, including state snapshot migrations, configuration updates, and compatibility management.

## Overview

The lab uses [Semantic Versioning](https://semver.org/) (SemVer) for version numbers:

- **Major version** (X.0.0): Breaking changes that require migration
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

## Version Compatibility

### Compatibility Rules

1. **State Snapshots**: Compatible within same major version
2. **Configurations**: Compatible within same major version
3. **APIs**: Compatible within same major version
4. **Dependencies**: Minimum versions specified in `CHANGELOG.md`

### Checking Compatibility

Use the version checking tool to verify compatibility:

```bash
# Check current version
python scripts/version.py

# Check snapshot compatibility
python scripts/check-snapshot-version.py snapshots/my-snapshot.yml

# Check all dependencies
python scripts/version.py --check-deps
```

## Upgrade Procedures

### Minor Version Upgrades (e.g., 0.8.x → 0.9.x)

Minor version upgrades are backward compatible and require no migration.

**Steps:**

1. **Backup Current State**
   ```bash
   # Export current lab state
   python scripts/export-state.py --output backups/pre-upgrade-$(date +%Y%m%d).yml
   
   # Backup configurations
   cp -r ansible/inventory.yml ansible/inventory.yml.backup
   cp -r monitoring/gnmic/gnmic-config.yml monitoring/gnmic/gnmic-config.yml.backup
   ```

2. **Update Code**
   ```bash
   git fetch origin
   git checkout v0.9.0  # or desired version
   ```

3. **Update Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Verify Installation**
   ```bash
   python scripts/version.py
   ./lab verify
   ```

5. **Test Functionality**
   ```bash
   # Run unit tests
   pytest tests/unit/
   
   # Run integration tests (optional)
   pytest tests/integration/
   ```

### Major Version Upgrades (e.g., 0.x.x → 1.0.0)

Major version upgrades may include breaking changes and require migration.

**Steps:**

1. **Review Breaking Changes**
   - Read `CHANGELOG.md` migration guide for target version
   - Identify affected components (snapshots, configs, APIs)
   - Plan migration steps

2. **Backup Everything**
   ```bash
   # Create comprehensive backup
   ./scripts/backup-lab.sh
   
   # This backs up:
   # - State snapshots
   # - Configurations
   # - Inventory files
   # - Custom scripts
   ```

3. **Run Pre-Migration Checks**
   ```bash
   # Check what needs migration
   python scripts/check-migration-requirements.py --target-version 1.0.0
   ```

4. **Migrate State Snapshots**
   ```bash
   # Migrate snapshot format
   python scripts/migrate-snapshots.py \
     --from 1.0 \
     --to 2.0 \
     --input snapshots/ \
     --output snapshots-migrated/
   
   # Verify migrated snapshots
   python scripts/validate-snapshots.py snapshots-migrated/
   ```

5. **Migrate Configurations**
   ```bash
   # Migrate Ansible inventory
   python scripts/migrate-inventory.py \
     --input ansible/inventory.yml \
     --output ansible/inventory-v2.yml
   
   # Migrate gNMIc configuration
   python scripts/migrate-gnmic-config.py \
     --input monitoring/gnmic/gnmic-config.yml \
     --output monitoring/gnmic/gnmic-config-v2.yml
   ```

6. **Update Code**
   ```bash
   git checkout v1.0.0
   pip install -r requirements.txt --upgrade
   ```

7. **Test Migration**
   ```bash
   # Test with migrated configurations
   ./lab start --config ansible/inventory-v2.yml
   ./lab verify
   
   # Restore a migrated snapshot
   python scripts/restore-state.py snapshots-migrated/test-snapshot.yml
   ```

8. **Finalize Migration**
   ```bash
   # If tests pass, replace old configs
   mv ansible/inventory-v2.yml ansible/inventory.yml
   mv monitoring/gnmic/gnmic-config-v2.yml monitoring/gnmic/gnmic-config.yml
   mv snapshots-migrated snapshots
   ```

## Component-Specific Upgrades

### State Snapshot Format Upgrades

State snapshots include version information for compatibility tracking.

**Snapshot Version History:**
- **1.0**: Initial format (lab versions 0.0.1 - 0.9.x)
- **2.0**: Enhanced format (lab versions 1.0.0+) - *planned*

**Migration Example:**

```python
# scripts/migrate-snapshots.py usage
python scripts/migrate-snapshots.py \
  --from 1.0 \
  --to 2.0 \
  --input snapshots/evpn-fabric.yml \
  --output snapshots/evpn-fabric-v2.yml \
  --validate
```

**Manual Migration:**

If automatic migration fails, you can manually update snapshots:

```yaml
# Old format (1.0)
version: "1.0"
timestamp: "2024-01-15T10:30:00Z"
lab_name: "evpn-fabric"
topology:
  # ... topology definition

# New format (2.0)
version: "2.0"
lab_version: "1.0.0"
timestamp: "2024-01-15T10:30:00Z"
lab_name: "evpn-fabric"
metadata:
  created_with_version: "1.0.0"
  component_versions:
    state_snapshot_format: "2.0"
    gnmic_config_format: "1.0"
topology:
  # ... enhanced topology definition with additional fields
```

### Ansible Inventory Upgrades

Inventory format changes are documented in migration guides.

**Inventory Version History:**
- **1.0**: Initial format (lab versions 0.0.1 - 0.9.x)
- **2.0**: Standardized variables (lab versions 1.0.0+) - *planned*

**Migration Example:**

```bash
python scripts/migrate-inventory.py ansible/inventory.yml
```

**Variable Name Changes (1.0 → 2.0):**

| Old Name (1.0) | New Name (2.0) | Notes |
|----------------|----------------|-------|
| `ansible_network_os` | `device_os` | Standardized naming |
| `device_role` | `topology_role` | Clarified purpose |
| N/A | `device_vendor` | New required field |

### gNMIc Configuration Upgrades

gNMIc configuration structure may change between versions.

**Config Version History:**
- **1.0**: Initial format (lab versions 0.0.1 - 0.9.x)
- **2.0**: Reorganized structure (lab versions 1.0.0+) - *planned*

**Migration Example:**

```bash
python scripts/migrate-gnmic-config.py monitoring/gnmic/gnmic-config.yml
```

### API Upgrades

When using the lab's Python APIs, check for breaking changes.

**API Version History:**
- **1.0**: Initial API (lab versions 0.0.1 - 0.9.x)
- **2.0**: Enhanced API (lab versions 1.0.0+) - *planned*

**Code Migration Example:**

```python
# Old API (1.0)
from state.export import export_state
snapshot = export_state(lab_name)

# New API (2.0)
from state.export import export_state
snapshot = export_state(
    lab_name,
    include_metrics=True,
    format_version="2.0"
)
```

## Rollback Procedures

If an upgrade fails, you can rollback to the previous version.

### Rollback Steps

1. **Stop Lab**
   ```bash
   ./lab stop
   ./destroy.sh
   ```

2. **Restore Previous Version**
   ```bash
   git checkout v0.8.0  # or previous version
   pip install -r requirements.txt
   ```

3. **Restore Configurations**
   ```bash
   cp ansible/inventory.yml.backup ansible/inventory.yml
   cp monitoring/gnmic/gnmic-config.yml.backup monitoring/gnmic/gnmic-config.yml
   ```

4. **Restore State**
   ```bash
   python scripts/restore-state.py backups/pre-upgrade-20240115.yml
   ```

5. **Verify Rollback**
   ```bash
   python scripts/version.py
   ./lab start
   ./lab verify
   ```

## Version Tracking in State Snapshots

All state snapshots include version information for compatibility tracking.

### Version Fields

```yaml
version: "1.0"                    # Snapshot format version
lab_version: "0.9.0"              # Lab version that created snapshot
timestamp: "2024-01-15T10:30:00Z" # Creation timestamp

metadata:
  created_with_version: "0.9.0"   # Lab version
  component_versions:
    state_snapshot_format: "1.0"
    gnmic_config_format: "1.0"
    ansible_inventory_format: "1.0"
  description: "EVPN fabric baseline"
  tags: ["evpn", "production-ready"]
```

### Checking Snapshot Version

```python
from scripts.version import validate_snapshot_version, check_snapshot_compatibility

# Load snapshot
import yaml
with open('snapshots/my-snapshot.yml') as f:
    snapshot = yaml.safe_load(f)

# Validate version
is_valid, message = validate_snapshot_version(snapshot)
print(f"Valid: {is_valid}, Message: {message}")

# Check compatibility
result = check_snapshot_compatibility(snapshot['version'])
print(f"Status: {result.status}")
print(f"Message: {result.message}")

if result.upgrade_available:
    print(f"Upgrade path: {' → '.join(result.upgrade_path)}")
```

### Adding Version to Snapshots

When creating snapshots programmatically:

```python
from scripts.version import add_version_to_snapshot

snapshot = {
    'lab_name': 'evpn-fabric',
    'timestamp': '2024-01-15T10:30:00Z',
    'topology': { ... },
    'configurations': { ... }
}

# Add version information
snapshot = add_version_to_snapshot(snapshot)

# Now includes version fields
assert 'version' in snapshot
assert 'lab_version' in snapshot
assert 'metadata' in snapshot
```

## Compatibility Matrix

See `CHANGELOG.md` for the complete version compatibility matrix.

### Current Compatibility (0.9.x)

| Component | Version | Compatible With |
|-----------|---------|-----------------|
| State Snapshot Format | 1.0 | Lab 0.0.1 - 0.9.x |
| gNMIc Config Format | 1.0 | Lab 0.0.1 - 0.9.x |
| Ansible Inventory Format | 1.0 | Lab 0.0.1 - 0.9.x |
| API Version | 1.0 | Lab 0.0.1 - 0.9.x |

### Dependency Requirements

| Dependency | Minimum Version | Recommended Version |
|------------|----------------|---------------------|
| Python | 3.9.0 | 3.11+ |
| Containerlab | 0.48.0 | Latest |
| Ansible | 2.14.0 | 2.15+ |
| gNMIc | 0.31.0 | Latest |

## Best Practices

1. **Always Backup Before Upgrading**
   - Export state snapshots
   - Backup configuration files
   - Document current state

2. **Test Upgrades in Non-Production**
   - Use a separate lab instance
   - Verify all functionality
   - Test snapshot restore

3. **Read Release Notes**
   - Review `CHANGELOG.md` thoroughly
   - Check for breaking changes
   - Plan migration steps

4. **Incremental Upgrades**
   - Don't skip major versions
   - Upgrade one minor version at a time
   - Verify after each upgrade

5. **Version Control Everything**
   - Commit configurations to git
   - Tag releases
   - Document changes

6. **Monitor Deprecation Notices**
   - Check `CHANGELOG.md` for deprecations
   - Plan migrations before features are removed
   - Update code proactively

## Troubleshooting

### Snapshot Version Mismatch

**Problem**: Snapshot version is incompatible with current lab version.

**Solution**:
```bash
# Check snapshot version
python scripts/check-snapshot-version.py snapshots/my-snapshot.yml

# Migrate if possible
python scripts/migrate-snapshots.py --from X.Y --to A.B snapshots/my-snapshot.yml
```

### Dependency Version Conflicts

**Problem**: Dependency versions don't meet requirements.

**Solution**:
```bash
# Check dependency versions
python scripts/version.py --check-deps

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify versions
python scripts/version.py
```

### Configuration Format Errors

**Problem**: Configuration files use old format.

**Solution**:
```bash
# Validate configuration
python scripts/validate-config.py ansible/inventory.yml

# Migrate if needed
python scripts/migrate-inventory.py ansible/inventory.yml
```

### API Compatibility Issues

**Problem**: Code uses deprecated API methods.

**Solution**:
1. Check `CHANGELOG.md` for API changes
2. Update code to use new API
3. Test thoroughly
4. Consider using version-specific imports:
   ```python
   from state.export import export_state_v2 as export_state
   ```

## Getting Help

- **Documentation**: See `docs/` directory
- **Changelog**: See `CHANGELOG.md` for version history
- **Issues**: Report problems on GitHub
- **Discussions**: Ask questions in GitHub Discussions

## Related Documentation

- [CHANGELOG.md](../../CHANGELOG.md) - Version history and migration guides
- [Contributing Guide](contributing.md) - Development and release process
- [API Reference](api-reference.md) - API documentation
- [State Management API](api-state-management.md) - State snapshot API
