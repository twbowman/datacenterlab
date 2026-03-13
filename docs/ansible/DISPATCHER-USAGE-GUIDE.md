# Dispatcher Pattern Usage Guide

## Quick Start

### Deploy Multi-Vendor Network

```bash
# Deploy all devices with validation and rollback
ansible-playbook -i inventory.yml site.yml

# Deploy with dynamic OS detection
ansible-playbook -i plugins/inventory/dynamic_inventory.py site.yml
```

### Deploy Specific Vendor

```bash
# Only SR Linux devices
ansible-playbook -i inventory.yml site.yml --limit srlinux_devices

# Only Arista devices (will skip gracefully - not yet implemented)
ansible-playbook -i inventory.yml site.yml --limit arista_devices
```

### Deploy Specific Configuration

```bash
# Only interfaces
ansible-playbook -i inventory.yml site.yml --tags interfaces

# Only BGP
ansible-playbook -i inventory.yml site.yml --tags bgp

# Only validation (no deployment)
ansible-playbook -i inventory.yml site.yml --tags validation
```

## Deployment Stages

### Stage 1: Pre-flight Checks

**What happens**:
- Validates `ansible_network_os` is defined
- Validates OS is supported
- Normalizes OS name for routing

**Output**:
```
TASK [Validate ansible_network_os is defined]
ok: [spine1] => {
    "msg": "Network OS detected: nokia.srlinux"
}

TASK [Validate ansible_network_os is supported]
ok: [spine1] => {
    "msg": "Network OS nokia.srlinux is supported"
}
```

**Possible Errors**:
```
FAILED! => {
    "msg": "Network OS not detected for spine1.\nPlease ensure ansible_network_os is set in inventory or use dynamic inventory plugin."
}
```

### Stage 2: Configuration Validation

**What happens**:
- Validates connection variables
- Validates interface name format
- Validates IPv4 address format
- Validates BGP configuration syntax

**Output**:
```
TASK [Validate required SR Linux variables]
ok: [spine1] => {
    "msg": "SR Linux connection variables validated"
}

TASK [Validate interface configuration syntax]
ok: [spine1] => (item={'name': 'ethernet-1/1', 'ip': '10.1.1.0/31'})
ok: [spine1] => (item={'name': 'ethernet-1/2', 'ip': '10.1.2.0/31'})
```

**Possible Errors**:
```
FAILED! => {
    "msg": "Invalid SR Linux interface name: Ethernet1/1\nExpected format: ethernet-X/Y, mgmt0, system0, or loX"
}
```

### Stage 3: Configuration Capture

**What happens**:
- Creates rollback directory
- Captures current device configuration
- Saves snapshot with timestamp
- Sets rollback_available flag

**Output**:
```
TASK [Capture current SR Linux configuration via gNMI]
ok: [spine1]

TASK [Save configuration snapshot]
changed: [spine1] => {
    "dest": "ansible/rollback_configs/spine1_1705315800.json"
}
```

**Possible Warnings**:
```
WARNING: Failed to capture current configuration for spine1.
Rollback will not be available if configuration deployment fails.
Error: Connection timeout
```

### Stage 4: Configuration Deployment

**What happens**:
- Routes to vendor-specific roles
- Applies configuration via vendor API
- Reports success or failure

**Output (Success)**:
```
TASK [Include SR Linux interfaces role]
included: /path/to/methods/srlinux_gnmi/roles/gnmi_interfaces/tasks/main.yml

TASK [Configure interface admin state (SR Linux)]
changed: [spine1] => (item={'name': 'ethernet-1/1', 'ip': '10.1.1.0/31'})
```

**Output (Failure)**:
```
TASK [Report SR Linux configuration failure]
ok: [spine1] => {
    "msg": "✗ Configuration failed for SR Linux device spine1\nError: Connection timeout to 172.20.20.10:57400\n\nRemediation suggestions:\n- Verify device is reachable: ping 172.20.20.10\n- Check gNMI service is running on port 57400\n- Verify credentials: username=admin\n- Review configuration syntax in inventory\n- Check device logs for detailed error messages\n\nAttempting automatic rollback..."
}
```

### Stage 5: Automatic Rollback (on failure)

**What happens**:
- Loads saved configuration snapshot
- Restores configuration via vendor API
- Reports rollback success or failure

**Output (Success)**:
```
TASK [Execute rollback for SR Linux]
included: roles/config_rollback/tasks/rollback_srlinux.yml

TASK [Restore SR Linux configuration via gNMI]
changed: [spine1]

TASK [Report rollback success]
ok: [spine1] => {
    "msg": "✓ Configuration rollback successful for spine1\nRestored from: ansible/rollback_configs/spine1_1705315800.json"
}
```

**Output (Failure)**:
```
TASK [Report rollback failure]
ok: [spine1] => {
    "msg": "✗ Configuration rollback FAILED for spine1\nError: Connection timeout during rollback\nManual intervention required.\nRollback file: ansible/rollback_configs/spine1_1705315800.json"
}
```

## Inventory Configuration

### SR Linux Devices

```yaml
all:
  children:
    srlinux_devices:
      vars:
        ansible_network_os: nokia.srlinux
        ansible_connection: local
        gnmi_port: 57400
        gnmi_username: admin
        gnmi_password: NokiaSrl1!
        gnmi_skip_verify: true
      hosts:
        spine1:
          ansible_host: 172.20.20.10
          router_id: 10.0.0.1
          asn: 65000
          interfaces:
            - name: ethernet-1/1
              ip: 10.1.1.0/31
```

### Arista EOS Devices

```yaml
all:
  children:
    arista_devices:
      vars:
        ansible_network_os: arista.eos
        ansible_connection: httpapi
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
        ansible_user: admin
        ansible_password: admin
      hosts:
        spine2:
          ansible_host: 172.20.20.11
          router_id: 10.0.0.2
          asn: 65000
          interfaces:
            - name: ethernet-1/1  # Will be translated to Ethernet1/1
              ip: 10.2.1.0/31
```

### Mixed Vendor Topology

```yaml
all:
  children:
    spines:
      children:
        srlinux_spines:
          hosts:
            spine1:
              ansible_host: 172.20.20.10
              ansible_network_os: nokia.srlinux
        arista_spines:
          hosts:
            spine2:
              ansible_host: 172.20.20.11
              ansible_network_os: arista.eos
```

## Error Scenarios

### Scenario 1: Missing ansible_network_os

**Inventory**:
```yaml
spine1:
  ansible_host: 172.20.20.10
  # ansible_network_os not set
```

**Error**:
```
FAILED! => {
    "msg": "Network OS not detected for spine1.\nPlease ensure ansible_network_os is set in inventory or use dynamic inventory plugin."
}
```

**Solution**:
- Add `ansible_network_os` to inventory
- Or use dynamic inventory plugin

### Scenario 2: Unsupported OS

**Inventory**:
```yaml
spine1:
  ansible_host: 172.20.20.10
  ansible_network_os: cisco.iosxr
```

**Error**:
```
FAILED! => {
    "msg": "Network OS 'cisco.iosxr' is not supported.\nSupported vendors: SR Linux (nokia.srlinux), Arista EOS (arista.eos), SONiC (dellemc.sonic), Juniper (juniper.junos)"
}
```

**Solution**:
- Use a supported vendor
- Or extend dispatcher to support new vendor

### Scenario 3: Invalid Interface Name

**Inventory**:
```yaml
interfaces:
  - name: Ethernet1/1  # Wrong format for SR Linux
    ip: 10.1.1.0/31
```

**Error**:
```
FAILED! => {
    "msg": "Invalid SR Linux interface name: Ethernet1/1\nExpected format: ethernet-X/Y, mgmt0, system0, or loX"
}
```

**Solution**:
- Use correct format: `ethernet-1/1`
- Or use interface name translation filter

### Scenario 4: Configuration Deployment Failure

**Scenario**: Device unreachable during configuration

**Output**:
```
TASK [Include SR Linux interfaces role]
fatal: [spine1]: FAILED! => {
    "msg": "Connection timeout to 172.20.20.10:57400"
}

TASK [Report SR Linux configuration failure]
ok: [spine1] => {
    "msg": "✗ Configuration failed for SR Linux device spine1\n..."
}

TASK [Execute rollback for SR Linux]
included: roles/config_rollback/tasks/rollback_srlinux.yml

TASK [Restore SR Linux configuration via gNMI]
changed: [spine1]

TASK [Report rollback success]
ok: [spine1] => {
    "msg": "✓ Configuration rollback successful for spine1"
}

FAILED! => {
    "msg": "Configuration deployment failed for spine1.\nRollback completed. Device restored to previous state."
}
```

**Result**: Device is in original state, deployment failed safely

## Advanced Usage

### Skip Validation

```bash
# Skip validation (not recommended)
ansible-playbook -i inventory.yml site.yml --skip-tags validation
```

### Skip Rollback Capture

```bash
# Skip rollback capture (not recommended)
ansible-playbook -i inventory.yml site.yml --skip-tags rollback
```

### Dry Run (Check Mode)

```bash
# Check what would be changed without applying
ansible-playbook -i inventory.yml site.yml --check
```

### Verbose Output

```bash
# Show detailed execution
ansible-playbook -i inventory.yml site.yml -v

# Show very detailed execution
ansible-playbook -i inventory.yml site.yml -vvv
```

### Deploy to Production

```bash
# Same playbook, different inventory
ansible-playbook -i inventory-production.yml site.yml
```

## Troubleshooting

### Issue: "Network OS not detected"

**Cause**: `ansible_network_os` not set in inventory

**Solutions**:
1. Add to inventory:
   ```yaml
   vars:
     ansible_network_os: nokia.srlinux
   ```

2. Use dynamic inventory:
   ```bash
   ansible-playbook -i plugins/inventory/dynamic_inventory.py site.yml
   ```

### Issue: "Network OS is not supported"

**Cause**: Using unsupported vendor

**Solutions**:
1. Check supported vendors list
2. Verify OS name spelling
3. Extend dispatcher for new vendor

### Issue: Validation fails with "Invalid interface name"

**Cause**: Using wrong interface naming convention for vendor

**Solutions**:
1. Check vendor-specific naming in `config_validation/README.md`
2. Use correct format for your vendor
3. Use interface name translation filters

### Issue: "Rollback not available"

**Cause**: Configuration capture failed before deployment

**Solutions**:
1. Check device connectivity
2. Verify API credentials
3. Check device API service is running
4. Review capture error message

### Issue: Configuration succeeds but device not working

**Cause**: Validation only checks syntax, not semantics

**Solutions**:
1. Run verification playbook:
   ```bash
   ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/verify.yml
   ```
2. Check device logs
3. Verify BGP sessions, LLDP neighbors, etc.

## Testing the Dispatcher

### Run Dispatcher Tests

```bash
ansible-playbook test-dispatcher.yml
```

**Expected Output**:
```
✓ Test 1 passed: SR Linux OS normalized correctly
✓ Test 2 passed: Arista EOS OS normalized correctly
✓ Test 3 passed: SONiC OS normalized correctly
✓ Test 4 passed: Juniper OS normalized correctly
✓ Test 5 passed: Short form OS names work correctly
✓ Test 6 passed: All OS variants are in supported list

========================================
✓ All dispatcher pattern tests passed!
========================================
```

## Related Documentation

- **Dispatcher Pattern**: See `ansible/DISPATCHER-PATTERN.md`
- **Validation Role**: See `ansible/roles/config_validation/README.md`
- **Rollback Role**: See `ansible/roles/config_rollback/README.md`
- **OS Detection**: See `ansible/OS-DETECTION-GUIDE.md`
- **Multi-Vendor Architecture**: See `ansible/MULTI-VENDOR-ARCHITECTURE.md`

