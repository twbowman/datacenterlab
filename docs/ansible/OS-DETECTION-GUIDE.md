# OS Detection System Guide

## Overview

The OS detection system automatically identifies network device operating systems during deployment and generates an Ansible inventory with the appropriate `ansible_network_os` variable. This eliminates the need for manual OS configuration and enables the dispatcher pattern to route configuration tasks to vendor-specific roles.

**Validates: Requirements 1.4, 1.5**

## How It Works

The OS detection system uses a three-tier detection strategy:

### 1. gNMI Capabilities Query (Primary Method)

The most reliable method queries each device's gNMI capabilities to identify the vendor:

```bash
gnmic -a <device-ip>:57400 -u admin -p <password> --insecure capabilities
```

The system parses the capabilities response for vendor-specific strings:
- `Nokia` → `srlinux`
- `Arista` → `eos`
- `SONiC` → `sonic`
- `Juniper` → `junos`

### 2. Containerlab Labels (Fallback)

If gNMI query fails, the system checks the topology file for explicit OS labels:

```yaml
nodes:
  spine1:
    labels:
      os: srlinux  # Used if gNMI detection fails
```

### 3. Containerlab Kind (Final Fallback)

As a last resort, the system infers OS from the containerlab `kind`:

```yaml
nodes:
  spine1:
    kind: nokia_srlinux  # Maps to 'srlinux'
```

## Usage

### Automatic Detection During Deployment

OS detection runs automatically when using the deployment scripts:

```bash
# Multi-vendor deployment with automatic OS detection
./deploy-multi-vendor.sh

# Single-vendor deployment with automatic OS detection
./deploy.sh
```

The deployment script will:
1. Deploy the topology with containerlab
2. Wait for devices to boot
3. Query each device via gNMI to detect OS
4. Generate `ansible/inventory-dynamic.yml` with detected OS types
5. Verify all devices have detected OS

### Manual OS Detection

If automatic detection fails or you need to re-detect after deployment:

```bash
# Detect OS for default topology
./scripts/detect-os.sh

# Detect OS for specific topology
./scripts/detect-os.sh topologies/topology-multi-vendor.yml

# Specify custom output file
./scripts/detect-os.sh topologies/topology-multi-vendor.yml my-inventory.yml
```

### Using the Python Script Directly

```bash
# Generate YAML inventory (default)
python3 ansible/plugins/inventory/dynamic_inventory.py -t topologies/topology-srlinux.yml -o inventory.yml

# Generate JSON inventory (for Ansible dynamic inventory)
python3 ansible/plugins/inventory/dynamic_inventory.py -t topologies/topology-srlinux.yml --list

# Output to stdout
python3 ansible/plugins/inventory/dynamic_inventory.py -t topologies/topology-srlinux.yml
```

## Generated Inventory Structure

The dynamic inventory groups devices by OS type and includes OS-specific connection variables:

```yaml
all:
  children:
    srlinux_devices:
      vars:
        ansible_connection: local
        gnmi_port: 57400
        gnmi_username: admin
        gnmi_password: NokiaSrl1!
        gnmi_skip_verify: true
      hosts:
        spine1:
          ansible_host: 172.20.20.10
          ansible_network_os: srlinux
          vendor: nokia
          role: spine
    
    eos_devices:
      vars:
        ansible_connection: httpapi
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
        ansible_user: admin
        ansible_password: admin
        ansible_httpapi_port: 443
      hosts:
        spine2:
          ansible_host: 172.20.20.11
          ansible_network_os: eos
          vendor: arista
          role: spine
```

## Integration with Ansible Dispatcher

The detected `ansible_network_os` variable enables the dispatcher pattern in playbooks:

```yaml
# ansible/site-multi-vendor.yml
- name: Configure all devices
  hosts: all
  tasks:
    - name: Include OS-specific roles
      include_role:
        name: "{{ ansible_network_os }}_{{ item }}"
      loop:
        - interfaces
        - bgp
        - ospf
      when: ansible_network_os in ['srlinux', 'eos', 'sonic', 'junos']
```

## Error Handling

### Detection Failures

If OS detection fails for a device, the system:

1. **Logs a warning** with the device name and reason
2. **Attempts fallback methods** (labels, kind)
3. **Sets OS to 'unknown'** if all methods fail
4. **Continues processing** other devices
5. **Reports summary** showing detection success rate

Example error output:

```
Warning: Failed to get capabilities from 172.20.20.10: connection timeout
Detected spine1 as srlinux via labels
Warning: Could not detect OS for leaf3
```

### Specific Error Messages

The system provides specific error messages for common issues:

| Error | Cause | Remediation |
|-------|-------|-------------|
| `Topology file not found` | Missing topology file | Check file path |
| `gnmic command not found` | gnmic not installed | Install gnmic: `bash -c "$(curl -sL https://get.gnmic.dev)"` |
| `Timeout querying <host>` | Device not responding | Wait for device to boot, check connectivity |
| `No management IP for <device>` | Missing mgmt-ipv4 in topology | Add mgmt-ipv4 to node config |
| `Could not detect OS for <device>` | All detection methods failed | Add explicit OS label to topology |

### Verification

After detection, verify all devices have detected OS:

```bash
# Check detection summary in deployment output
./deploy-multi-vendor.sh

# Manually verify inventory
grep "ansible_network_os:" ansible/inventory-dynamic.yml

# Count unknown devices
grep -c "ansible_network_os: unknown" ansible/inventory-dynamic.yml || echo "0"
```

## Troubleshooting

### Device Not Detected

**Problem**: Device shows as `ansible_network_os: unknown`

**Solutions**:
1. Verify device is running: `docker ps | grep <device-name>`
2. Check device is reachable: `ping <device-ip>`
3. Test gNMI manually: `gnmic -a <device-ip>:57400 -u admin -p <password> --insecure capabilities`
4. Add explicit OS label to topology:
   ```yaml
   nodes:
     mydevice:
       labels:
         os: srlinux
   ```

### gNMI Connection Timeout

**Problem**: `Timeout querying <host>`

**Solutions**:
1. Wait longer for device to boot (some vendors take 90-120 seconds)
2. Verify gNMI port is correct (default: 57400)
3. Check device logs: `docker logs clab-<lab-name>-<device-name>`
4. Verify gNMI is enabled on the device

### gnmic Not Found

**Problem**: `gnmic command not found`

**Solution**: Install gnmic:
```bash
bash -c "$(curl -sL https://get.gnmic.dev)"
```

### Wrong OS Detected

**Problem**: Device detected as wrong OS type

**Solutions**:
1. Check gNMI capabilities output manually
2. Add explicit OS label to override detection
3. Update OS_MAPPINGS in `dynamic_inventory.py` if vendor string is different

## Supported Operating Systems

| OS | Vendor | Detection String | ansible_network_os |
|----|--------|------------------|-------------------|
| SR Linux | Nokia | `Nokia` | `srlinux` |
| cEOS | Arista | `Arista` | `eos` |
| SONiC | Dell/Microsoft | `SONiC` | `sonic` |
| Junos | Juniper | `Juniper` | `junos` |

## Adding New Vendors

To add support for a new vendor:

1. **Update OS_MAPPINGS** in `ansible/plugins/inventory/dynamic_inventory.py`:
   ```python
   OS_MAPPINGS = {
       'Nokia': 'srlinux',
       'Arista': 'eos',
       'SONiC': 'sonic',
       'Juniper': 'junos',
       'NewVendor': 'newos',  # Add new mapping
   }
   ```

2. **Add OS-specific variables** in `_get_os_vars()`:
   ```python
   'newos': {
       'ansible_connection': 'netconf',
       'ansible_user': 'admin',
       'ansible_password': 'admin',
   }
   ```

3. **Test detection**:
   ```bash
   gnmic -a <device-ip>:57400 -u admin -p <password> --insecure capabilities
   ```
   Look for vendor-specific strings in the output.

4. **Create vendor-specific roles**:
   ```
   ansible/roles/newos_interfaces/
   ansible/roles/newos_bgp/
   ansible/roles/newos_ospf/
   ```

## Production Considerations

### Lab vs Production

The OS detection system works identically for lab (containers) and production (physical/VM) devices:

- **Lab**: Detects containerlab devices via gNMI
- **Production**: Detects physical/VM devices via gNMI
- **Same Code**: No changes needed between environments

### Security

For production deployments:

1. **Use secure credentials**: Don't hardcode passwords in the script
2. **Enable TLS**: Remove `--insecure` flag and configure certificates
3. **Restrict access**: Limit who can run OS detection
4. **Audit logs**: Log all detection attempts

Example secure detection:

```python
# Use environment variables for credentials
gnmi_username = os.environ.get('GNMI_USERNAME', 'admin')
gnmi_password = os.environ.get('GNMI_PASSWORD')

# Use TLS certificates
cmd = [
    'gnmic',
    '-a', f'{host}:{port}',
    '-u', gnmi_username,
    '-p', gnmi_password,
    '--tls-ca', '/path/to/ca.crt',
    '--tls-cert', '/path/to/client.crt',
    '--tls-key', '/path/to/client.key',
    'capabilities'
]
```

### Performance

- **Detection time**: ~2-5 seconds per device
- **Parallel detection**: Not currently implemented (sequential)
- **Caching**: Not currently implemented
- **For large deployments**: Consider caching results or using labels

## Examples

### Example 1: Single-Vendor Lab

```bash
# Deploy SR Linux lab
./deploy.sh

# OS detection runs automatically
# Output: ansible/inventory-dynamic.yml with all devices as 'srlinux'
```

### Example 2: Multi-Vendor Lab

```bash
# Deploy multi-vendor lab
./deploy-multi-vendor.sh

# OS detection runs automatically
# Output: ansible/inventory-dynamic.yml with mixed OS types
```

### Example 3: Manual Detection After Deployment

```bash
# Deploy without automatic detection
containerlab deploy -t topologies/topology-multi-vendor.yml

# Wait for devices to boot
sleep 120

# Run manual detection
./scripts/detect-os.sh topologies/topology-multi-vendor.yml

# Use generated inventory
ansible-playbook -i ansible/inventory-dynamic.yml ansible/site-multi-vendor.yml
```

### Example 4: Custom Topology

```bash
# Create custom topology
cat > my-topology.yml <<EOF
name: my-lab
topology:
  nodes:
    router1:
      kind: nokia_srlinux
      mgmt-ipv4: 192.168.1.10
    router2:
      kind: arista_ceos
      mgmt-ipv4: 192.168.1.11
EOF

# Deploy and detect
containerlab deploy -t my-topology.yml
sleep 90
./scripts/detect-os.sh my-topology.yml my-inventory.yml

# Use custom inventory
ansible-playbook -i my-inventory.yml ansible/site-multi-vendor.yml
```

## References

- **Requirements**: See `.kiro/specs/production-network-testing-lab/requirements.md`
  - Requirement 1.4: Automatic OS detection
  - Requirement 1.5: Specific error messages
- **Design**: See `.kiro/specs/production-network-testing-lab/design.md`
  - Dispatcher pattern architecture
  - OS detection logic
- **gNMI**: See `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md`
- **Multi-Vendor**: See `ansible/MULTI-VENDOR-ARCHITECTURE.md`
