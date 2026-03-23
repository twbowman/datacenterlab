# Configuration Rollback Role

## Overview

This role provides automatic configuration rollback capabilities for multi-vendor network devices. It captures the current device configuration before changes are applied and can restore it if deployment fails.

**Validates: Requirements 2.6**

## Features

- **Pre-deployment Capture**: Automatically saves device configuration before changes
- **Automatic Rollback**: Restores previous configuration on deployment failure
- **Multi-Vendor Support**: Works with SR Linux, Arista EOS, SONiC, and Juniper
- **Error Reporting**: Provides detailed error messages and remediation suggestions
- **Graceful Degradation**: Warns if rollback is unavailable but continues deployment

## Architecture

### Dispatcher Pattern

The role uses a dispatcher pattern to route rollback operations to vendor-specific implementations:

```
config_rollback/
├── tasks/
│   ├── main.yml              # Dispatcher
│   ├── capture_srlinux.yml   # SR Linux state capture
│   ├── capture_arista.yml    # Arista EOS state capture
│   ├── capture_sonic.yml     # SONiC state capture
│   ├── capture_junos.yml     # Juniper state capture
│   ├── rollback_srlinux.yml  # SR Linux rollback execution
│   ├── rollback_arista.yml   # Arista EOS rollback execution
│   ├── rollback_sonic.yml    # SONiC rollback execution
│   └── rollback_junos.yml    # Juniper rollback execution
└── handlers/
    └── main.yml              # Rollback handler
```

## Usage

### Automatic Integration

The role is automatically included in `ansible/site.yml` before configuration deployment:

```yaml
- name: Capture current configuration state
  include_role:
    name: config_rollback
  tags: [rollback, always]

- name: Configure devices
  block:
    # Configuration tasks...
  rescue:
    - name: Execute rollback
      include_tasks: roles/config_rollback/tasks/rollback_{{ normalized_os }}.yml
      when: rollback_available | default(false)
```

### Manual Rollback

To manually trigger a rollback (requires a saved snapshot):

```bash
# Rollback specific device
ansible-playbook -i inventory.yml rollback.yml --limit spine1

# Rollback all devices
ansible-playbook -i inventory.yml rollback.yml
```

## Configuration Snapshots

### Storage Location

Configuration snapshots are stored in:
```
ansible/rollback_configs/
├── spine1_1705315800.json    # SR Linux (JSON via gNMI)
├── spine2_1705315801.cfg     # Arista EOS (CLI format)
├── leaf1_1705315802.cfg      # SONiC (CLI format)
└── leaf2_1705315803.cfg      # Juniper (CLI format)
```

### Snapshot Format

- **SR Linux**: JSON format (full gNMI tree)
- **Arista EOS**: CLI configuration format
- **SONiC**: CLI configuration format
- **Juniper**: CLI configuration format

### Snapshot Naming

Format: `{hostname}_{unix_timestamp}.{extension}`
- Hostname: Ansible inventory hostname
- Timestamp: Unix epoch time
- Extension: `.json` for SR Linux, `.cfg` for others

## Vendor-Specific Implementations

### SR Linux

**Capture Method**: gNMI get operation on root path `/`
**Restore Method**: gNMI replace operation on root path `/`
**Format**: JSON (IETF JSON encoding)

```yaml
- name: Capture current SR Linux configuration via gNMI
  nokia.srlinux.gnmi_get:
    host: "{{ ansible_host }}"
    port: "{{ gnmi_port }}"
    path: "/"
    encoding: json_ietf
  register: current_config
```

### Arista EOS

**Capture Method**: `show running-config` via eAPI
**Restore Method**: `eos_config` with replace mode
**Format**: CLI configuration text

```yaml
- name: Capture current Arista EOS configuration
  arista.eos.eos_command:
    commands:
      - show running-config
  register: current_config
```

### SONiC

**Capture Method**: `show running-configuration` via REST API
**Restore Method**: `sonic_config` module
**Format**: CLI configuration text

```yaml
- name: Capture current SONiC configuration
  dellemc.enterprise_sonic.sonic_command:
    commands:
      - show running-configuration
  register: current_config
```

### Juniper

**Capture Method**: `show configuration` via NETCONF
**Restore Method**: `junos_config` with replace mode
**Format**: Junos configuration text

```yaml
- name: Capture current Juniper configuration
  junipernetworks.junos.junos_command:
    commands:
      - show configuration
  register: current_config
```

## Error Handling

### Capture Failures

If configuration capture fails:
1. Warning message is displayed
2. `rollback_available` flag is set to `false`
3. Deployment continues (rollback won't be available on failure)

### Rollback Failures

If rollback fails:
1. Error message is displayed with details
2. Manual intervention message is shown
3. Rollback configuration file path is provided
4. Playbook execution fails

### Remediation Suggestions

On configuration failure, the role provides vendor-specific remediation suggestions:
- Connectivity checks (ping device)
- Service availability checks (gNMI, eAPI, REST API, NETCONF)
- Credential verification
- Configuration syntax review
- Device log inspection

## Variables

### Required Variables (per vendor)

**SR Linux**:
- `ansible_host`: Device management IP
- `gnmi_port`: gNMI port (default: 57400)
- `gnmi_username`: gNMI username
- `gnmi_password`: gNMI password
- `gnmi_skip_verify`: Skip TLS verification (default: true)

**Arista EOS**:
- `ansible_host`: Device management IP
- `ansible_user`: API username
- `ansible_password`: API password

**SONiC**:
- `ansible_host`: Device management IP
- `ansible_user`: API username
- `ansible_password`: API password

**Juniper**:
- `ansible_host`: Device management IP
- `ansible_user`: NETCONF username
- `ansible_password`: NETCONF password

### Runtime Variables

- `rollback_available`: Boolean flag indicating if rollback is possible
- `rollback_config_file`: Path to saved configuration snapshot
- `normalized_os`: Normalized OS name (srlinux, eos, sonic, junos)

## Testing

### Test Rollback Functionality

1. Deploy initial configuration:
```bash
ansible-playbook -i inventory.yml site.yml
```

2. Introduce a configuration error in inventory

3. Attempt deployment (should fail and rollback):
```bash
ansible-playbook -i inventory.yml site.yml
```

4. Verify device is in original state

### Test Without Rollback

To test deployment without rollback capability:
```bash
ansible-playbook -i inventory.yml site.yml --skip-tags rollback
```

## Limitations

1. **Full Configuration Replacement**: Rollback replaces entire configuration, not incremental
2. **No Partial Rollback**: Cannot rollback individual configuration sections
3. **Storage Management**: Old snapshots are not automatically cleaned up
4. **No Versioning**: Only the most recent snapshot is used for rollback
5. **Vendor Module Dependencies**: Requires vendor-specific Ansible collections

## Future Enhancements

- Incremental rollback (specific configuration sections)
- Snapshot versioning and management
- Automatic snapshot cleanup (retention policy)
- Configuration diff before rollback
- Rollback dry-run mode
- Checkpoint-based rollback (multiple restore points)

## Related Documentation

- **Requirements**: See `.kiro/specs/production-network-testing-lab/requirements.md` (Requirement 2.6)
- **Design**: See `.kiro/specs/production-network-testing-lab/design.md` (Property 8)
- **Main Playbook**: See `ansible/site.yml`
- **Validation Role**: See `ansible/roles/config_validation/`

