# Dispatcher Pattern Quick Reference

## One-Line Summary

Single playbook (`site.yml`) configures all vendors with automatic OS detection, pre-deployment validation, and rollback on failure.

## Quick Commands

```bash
# Deploy everything
ansible-playbook -i inventory.yml site.yml

# Deploy one device
ansible-playbook -i inventory.yml site.yml --limit spine1

# Deploy one vendor
ansible-playbook -i inventory.yml site.yml --limit srlinux_devices

# Validate only (no deployment)
ansible-playbook -i inventory.yml site.yml --tags validation

# Deploy with dynamic OS detection
ansible-playbook -i plugins/inventory/dynamic_inventory.py site.yml
```

## Supported Vendors

| Vendor | OS Name | Status |
|--------|---------|--------|
| Nokia SR Linux | `nokia.srlinux` or `srlinux` | ✅ Implemented |
| Arista EOS | `arista.eos` or `eos` | ⚠️ Placeholder |
| Dell SONiC | `dellemc.sonic` or `sonic` | ⚠️ Placeholder |
| Juniper | `juniper.junos` or `junos` | ⚠️ Placeholder |

## Deployment Flow

```
1. Validate OS is defined and supported
2. Normalize OS name (remove vendor prefix)
3. Validate configuration syntax
4. Capture current configuration (for rollback)
5. Deploy configuration to device
6. On failure: Rollback and report error
```

## Required Inventory Variables

### SR Linux
```yaml
ansible_network_os: nokia.srlinux
ansible_host: 172.20.20.10
gnmi_port: 57400
gnmi_username: admin
gnmi_password: NokiaSrl1!
```

### Arista EOS
```yaml
ansible_network_os: arista.eos
ansible_host: 172.20.20.11
ansible_user: admin
ansible_password: admin
```

### SONiC
```yaml
ansible_network_os: dellemc.sonic
ansible_host: 172.20.20.12
ansible_user: admin
ansible_password: admin
```

### Juniper
```yaml
ansible_network_os: juniper.junos
ansible_host: 172.20.20.13
ansible_user: admin
ansible_password: admin
```

## Common Errors

### "Network OS not detected"
**Fix**: Add `ansible_network_os` to inventory or use dynamic inventory

### "Network OS is not supported"
**Fix**: Use one of: `nokia.srlinux`, `arista.eos`, `dellemc.sonic`, `juniper.junos`

### "Invalid interface name"
**Fix**: Use vendor-specific format (see validation role README)

### "Rollback not available"
**Fix**: Check device connectivity before deployment

## Files to Know

- `ansible/site.yml` - Main playbook
- `ansible/roles/config_validation/` - Validation rules
- `ansible/roles/config_rollback/` - Rollback mechanism
- `ansible/DISPATCHER-PATTERN.md` - Full architecture
- `ansible/DISPATCHER-USAGE-GUIDE.md` - Detailed usage

## Validation Rules

### Interface Names

- **SR Linux**: `ethernet-1/1`, `mgmt0`, `lo0`
- **Arista**: `Ethernet1/1`, `Management1`
- **SONiC**: `Ethernet0`, `PortChannel1`
- **Juniper**: `ge-0/0/0`, `xe-0/0/1`, `lo0`

### IPv4 Addresses

- Format: `X.X.X.X/Y` (CIDR notation)
- Example: `10.1.1.0/31`

### BGP ASN

- Range: 1 to 4294967295
- Example: `65000`

### BGP Router ID

- Format: `X.X.X.X` (IPv4 address)
- Example: `10.0.0.1`

## Rollback Snapshots

- **Location**: `ansible/rollback_configs/`
- **Format**: `{hostname}_{timestamp}.{ext}`
- **SR Linux**: `.json` (gNMI format)
- **Others**: `.cfg` (CLI format)

## Tags

- `validation` - Run validation only
- `rollback` - Include rollback capture
- `config` - Configuration tasks
- `interfaces` - Interface configuration
- `bgp` - BGP configuration
- `ospf` - OSPF configuration
- `lldp` - LLDP configuration
- `system` - System configuration
- `always` - Always runs (validation, rollback)

## Production Usage

Same playbook works for lab and production:

```bash
# Lab
ansible-playbook -i inventory-lab.yml site.yml

# Production
ansible-playbook -i inventory-production.yml site.yml
```

Only inventory changes (IPs and credentials).

