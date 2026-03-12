# Multi-Vendor Dispatcher Pattern

## Overview

The dispatcher pattern enables a single Ansible playbook (`site.yml`) to configure network devices across multiple vendors (SR Linux, Arista EOS, SONiC, Juniper) by routing configuration tasks to vendor-specific implementations based on the detected network operating system.

**Validates: Requirements 2.8, 10.5**

## Architecture

### High-Level Flow

```
User runs: ansible-playbook -i inventory.yml site.yml
    ↓
1. Detect ansible_network_os for each device
    ↓
2. Validate OS is supported (srlinux, eos, sonic, junos)
    ↓
3. Normalize OS name (remove vendor prefix)
    ↓
4. Validate configuration syntax (vendor-specific rules)
    ↓
5. Capture current configuration state (for rollback)
    ↓
6. Route to vendor-specific configuration roles
    ↓
7. On failure: Execute rollback and report errors
```

### Dispatcher Logic

```yaml
# ansible/site.yml
- name: Configure Multi-Vendor Datacenter Network
  hosts: all
  tasks:
    # 1. OS Detection & Validation
    - assert: ansible_network_os is defined
    - assert: ansible_network_os in supported_vendors
    - set_fact: normalized_os = normalize(ansible_network_os)
    
    # 2. Pre-deployment Validation
    - include_role: config_validation
    
    # 3. Rollback Preparation
    - include_role: config_rollback  # Captures state
    
    # 4. Vendor-Specific Configuration
    - block:
        - include_role: vendor_specific_roles
      rescue:
        - include_tasks: rollback_{{ normalized_os }}.yml
        - fail: "Configuration failed, rollback completed"
      when: normalized_os == 'vendor'
```

## Supported Vendors

| Vendor | OS Name (Full) | OS Name (Short) | Status |
|--------|----------------|-----------------|--------|
| Nokia SR Linux | `nokia.srlinux` | `srlinux` | ✅ Implemented |
| Arista EOS | `arista.eos` | `eos` | ⚠️ Placeholder |
| Dell SONiC | `dellemc.sonic` | `sonic` | ⚠️ Placeholder |
| Juniper Junos | `juniper.junos` | `junos` | ⚠️ Placeholder |

## OS Name Normalization

The dispatcher normalizes OS names to short form for consistent routing:

```yaml
normalized_os: "{{ ansible_network_os | 
  regex_replace('^nokia\\.', '') | 
  regex_replace('^arista\\.', '') | 
  regex_replace('^dellemc\\.', '') | 
  regex_replace('^juniper\\.', '') }}"
```

**Examples**:
- `nokia.srlinux` → `srlinux`
- `arista.eos` → `eos`
- `dellemc.sonic` → `sonic`
- `juniper.junos` → `junos`

## Configuration Stages

### Stage 1: OS Detection & Validation

**Purpose**: Ensure device OS is detected and supported

**Validations**:
1. `ansible_network_os` is defined
2. `ansible_network_os` is not empty
3. `ansible_network_os` is in supported vendor list

**Error Handling**:
- Missing OS: Fails with message to check inventory or use dynamic inventory
- Unsupported OS: Fails with list of supported vendors

### Stage 2: Configuration Syntax Validation

**Purpose**: Validate configuration parameters before device communication

**Validations** (vendor-specific):
1. Required connection variables (host, port, credentials)
2. Interface name format
3. IPv4 address format (CIDR notation)
4. BGP configuration (ASN range, router ID format)
5. BGP neighbor syntax (IP format, peer AS range)

**Error Handling**:
- Validation failure: Stops deployment with descriptive error message
- Shows expected format and current value
- No device communication occurs on validation failure

**See**: `ansible/roles/config_validation/README.md`

### Stage 3: Configuration State Capture

**Purpose**: Save current device configuration for rollback capability

**Operations** (vendor-specific):
1. Create rollback directory (`ansible/rollback_configs/`)
2. Capture current configuration via device API
3. Save snapshot with timestamp
4. Set `rollback_available` flag

**Error Handling**:
- Capture failure: Warns but continues deployment
- Sets `rollback_available = false`
- Rollback won't be available if deployment fails

**See**: `ansible/roles/config_rollback/README.md`

### Stage 4: Vendor-Specific Configuration

**Purpose**: Apply configuration using vendor-specific roles

**SR Linux** (Implemented):
- Uses gNMI for configuration
- Roles: system, interfaces, LLDP, OSPF, BGP
- Location: `ansible/methods/srlinux_gnmi/roles/`

**Arista EOS** (Placeholder):
- Will use eAPI or gNMI
- Roles: TBD (Task 4)
- Location: TBD

**SONiC** (Placeholder):
- Will use REST API
- Roles: TBD (Task 5)
- Location: TBD

**Juniper** (Placeholder):
- Will use NETCONF
- Roles: TBD (Task 6)
- Location: TBD

**Error Handling**:
- Configuration failure: Triggers rescue block
- Reports error with remediation suggestions
- Executes automatic rollback if available
- Fails deployment after rollback

### Stage 5: Rollback on Failure

**Purpose**: Restore previous configuration if deployment fails

**Operations** (vendor-specific):
1. Check if rollback is available
2. Load saved configuration snapshot
3. Restore configuration via device API
4. Report rollback success or failure

**Error Handling**:
- Rollback unavailable: Reports manual recovery needed
- Rollback failure: Reports critical error, manual intervention required

## Vendor-Specific Routing

### SR Linux

```yaml
when: normalized_os == 'srlinux'
block:
  - include_role: gnmi_system
  - include_role: gnmi_interfaces
  - include_role: gnmi_lldp
  - include_role: gnmi_ospf
  - include_role: gnmi_bgp
rescue:
  - include_tasks: rollback_srlinux.yml
```

**Configuration Method**: gNMI with native SR Linux YANG models
**Connection**: Direct gNMI (port 57400)
**Rollback Method**: gNMI replace operation

### Arista EOS

```yaml
when: normalized_os == 'eos'
block:
  - include_role: eos_interfaces
  - include_role: eos_bgp
  - include_role: eos_ospf
rescue:
  - include_tasks: rollback_arista.yml
```

**Configuration Method**: eAPI or gNMI (TBD)
**Connection**: HTTPS API (port 443)
**Rollback Method**: Config replace via eAPI

### SONiC

```yaml
when: normalized_os == 'sonic'
block:
  - include_role: sonic_interfaces
  - include_role: sonic_bgp
  - include_role: sonic_ospf
rescue:
  - include_tasks: rollback_sonic.yml
```

**Configuration Method**: REST API
**Connection**: HTTPS REST API
**Rollback Method**: Config restore via REST API

### Juniper

```yaml
when: normalized_os == 'junos'
block:
  - include_role: junos_interfaces
  - include_role: junos_bgp
  - include_role: junos_ospf
rescue:
  - include_tasks: rollback_junos.yml
```

**Configuration Method**: NETCONF
**Connection**: NETCONF (port 830)
**Rollback Method**: Config replace via NETCONF

## Graceful Handling of Unsupported Vendors

### Current Implementation

For vendors with placeholder implementations (Arista, SONiC, Juniper):

```yaml
- name: Configure Arista EOS devices
  block:
    - debug:
        msg: "Arista EOS configuration roles are not yet implemented..."
    - meta: end_host  # Skip device gracefully
  when: normalized_os == 'eos'
```

**Behavior**:
- Displays informative message
- Skips device without failing entire playbook
- Allows other devices to continue configuration
- References future task number for implementation

### Future Implementation

Once vendor roles are implemented (Tasks 4, 5, 6):
1. Remove placeholder debug message
2. Remove `meta: end_host`
3. Add actual role inclusions
4. Keep rescue block for error handling

## Error Reporting

### Configuration Failure Report

```
✗ Configuration failed for SR Linux device spine1
Error: Connection timeout to 172.20.20.10:57400

Remediation suggestions:
- Verify device is reachable: ping 172.20.20.10
- Check gNMI service is running on port 57400
- Verify credentials: username=admin
- Review configuration syntax in inventory
- Check device logs for detailed error messages

Attempting automatic rollback...
```

### Rollback Success Report

```
✓ Configuration rollback successful for spine1
Restored from: ansible/rollback_configs/spine1_1705315800.json
```

### Rollback Failure Report

```
✗ Configuration rollback FAILED for spine1
Error: Connection timeout during rollback
Manual intervention required.
Rollback file: ansible/rollback_configs/spine1_1705315800.json
```

## Usage Examples

### Deploy All Devices

```bash
ansible-playbook -i inventory.yml site.yml
```

**Behavior**:
- Validates all device configurations
- Captures state for all devices
- Configures SR Linux devices
- Skips Arista/SONiC/Juniper devices (not implemented)

### Deploy Specific Vendor

```bash
# Only SR Linux devices
ansible-playbook -i inventory.yml site.yml --limit srlinux_devices

# Only Arista devices (will skip gracefully)
ansible-playbook -i inventory.yml site.yml --limit arista_devices
```

### Deploy Specific Configuration Stage

```bash
# Only interfaces
ansible-playbook -i inventory.yml site.yml --tags interfaces

# Only BGP
ansible-playbook -i inventory.yml site.yml --tags bgp

# Only validation (no deployment)
ansible-playbook -i inventory.yml site.yml --tags validation
```

### Deploy with Dynamic Inventory

```bash
ansible-playbook -i plugins/inventory/dynamic_inventory.py site.yml
```

**Behavior**:
- Automatically detects device OS
- Routes to appropriate vendor implementation
- No manual OS configuration needed

## Integration with Dynamic Inventory

The dispatcher pattern works seamlessly with the dynamic inventory plugin:

```python
# plugins/inventory/dynamic_inventory.py detects OS
device_os = detect_os_via_gnmi(device_ip)

# Sets ansible_network_os in inventory
inventory['_meta']['hostvars'][hostname] = {
    'ansible_network_os': device_os,
    'ansible_host': device_ip
}
```

**Workflow**:
1. Dynamic inventory detects OS for each device
2. Sets `ansible_network_os` variable
3. Dispatcher routes based on `ansible_network_os`
4. No manual OS configuration required

## Production Datacenter Usage

### Lab vs Production

**Lab Deployment**:
```bash
ansible-playbook -i inventory-lab.yml site.yml
```

**Production Deployment**:
```bash
ansible-playbook -i inventory-production.yml site.yml
```

**Key Point**: Same playbook, same roles, same dispatcher logic. Only inventory changes.

### Inventory Differences

**Lab Inventory** (`inventory-lab.yml`):
- Containerlab management IPs (172.20.20.x)
- Container-specific connection settings
- Test credentials

**Production Inventory** (`inventory-production.yml`):
- Datacenter management IPs (10.x.x.x)
- Production connection settings
- Production credentials

**Everything Else**: Identical (same roles, same templates, same validation, same rollback)

## Extending the Dispatcher

### Adding a New Vendor

1. **Add OS to supported list**:
```yaml
- assert:
    that:
      - ansible_network_os in [..., 'newvendor.newos']
```

2. **Add normalization rule**:
```yaml
normalized_os: "{{ ansible_network_os | regex_replace('^newvendor\\.', '') }}"
```

3. **Create validation tasks**:
```
ansible/roles/config_validation/tasks/validate_newos.yml
```

4. **Create rollback tasks**:
```
ansible/roles/config_rollback/tasks/capture_newos.yml
ansible/roles/config_rollback/tasks/rollback_newos.yml
```

5. **Add configuration block**:
```yaml
- name: Configure NewVendor devices
  block:
    - include_role: newvendor_interfaces
    - include_role: newvendor_bgp
  rescue:
    - include_tasks: rollback_newos.yml
  when: normalized_os == 'newos'
```

### Adding a New Configuration Role

To add a new configuration capability (e.g., EVPN):

1. **Create vendor-specific roles**:
```
ansible/methods/srlinux_gnmi/roles/gnmi_evpn/
ansible/methods/arista_eos/roles/eos_evpn/
ansible/methods/sonic/roles/sonic_evpn/
ansible/methods/junos/roles/junos_evpn/
```

2. **Add to dispatcher blocks**:
```yaml
- name: Include SR Linux EVPN role
  include_role:
    name: gnmi_evpn
  vars:
    ansible_role_path: "{{ playbook_dir }}/methods/srlinux_gnmi/roles"
  tags: [evpn, config]
```

3. **Add validation rules** (if needed):
```yaml
# ansible/roles/config_validation/tasks/validate_srlinux.yml
- name: Validate EVPN configuration syntax
  assert:
    that:
      - vni is defined
      - vni >= 1
      - vni <= 16777215
```

## Benefits

1. **Single Entry Point**: One playbook for all vendors
2. **Vendor Abstraction**: Users don't need to know vendor-specific details
3. **Graceful Degradation**: Unimplemented vendors are skipped, not failed
4. **Consistent Error Handling**: Same error reporting across vendors
5. **Automatic Rollback**: Configuration failures are automatically reverted
6. **Production Ready**: Same code works for lab and production

## Comparison with Alternative Approaches

### Alternative 1: Separate Playbooks per Vendor

```bash
ansible-playbook -i inventory.yml site-srlinux.yml
ansible-playbook -i inventory.yml site-arista.yml
ansible-playbook -i inventory.yml site-sonic.yml
```

**Drawbacks**:
- Multiple playbook runs for mixed-vendor topologies
- Duplicate validation and rollback logic
- More complex orchestration

### Alternative 2: Single Playbook with Manual OS Specification

```bash
ansible-playbook -i inventory.yml site.yml -e "vendor=srlinux"
```

**Drawbacks**:
- Manual OS specification required
- Cannot handle mixed-vendor topologies in single run
- Error-prone (user must know device OS)

### Alternative 3: Vendor-Specific Inventories

```bash
ansible-playbook -i inventory-srlinux.yml site.yml
ansible-playbook -i inventory-arista.yml site.yml
```

**Drawbacks**:
- Multiple inventory files to maintain
- Cannot represent mixed-vendor topologies
- Duplicate device information

### Chosen Approach: Dispatcher Pattern

**Advantages**:
- Single playbook run for all vendors
- Automatic OS detection
- Unified error handling and rollback
- Mixed-vendor topology support
- Production-ready architecture

## Related Documentation

- **Requirements**: See `.kiro/specs/production-network-testing-lab/requirements.md` (Requirements 2.8, 10.5)
- **Design**: See `.kiro/specs/production-network-testing-lab/design.md`
- **Main Playbook**: See `ansible/site.yml`
- **Validation Role**: See `ansible/roles/config_validation/`
- **Rollback Role**: See `ansible/roles/config_rollback/`
- **OS Detection**: See `ansible/OS-DETECTION-GUIDE.md`
- **Multi-Vendor Architecture**: See `ansible/MULTI-VENDOR-ARCHITECTURE.md`

