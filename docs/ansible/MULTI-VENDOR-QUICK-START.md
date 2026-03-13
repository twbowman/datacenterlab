# Multi-Vendor Ansible Quick Start

## Quick Setup

### 1. Install Required Collections

```bash
# SR Linux
ansible-galaxy collection install nokia.srlinux

# Arista EOS
ansible-galaxy collection install arista.eos

# SONiC
ansible-galaxy collection install dellemc.enterprise_sonic
```

### 2. Update Inventory

Edit `inventory-multi-vendor.yml` and set:
- Device management IPs (`ansible_host`)
- Credentials (`ansible_user`, `ansible_password`)
- Network OS type (`ansible_network_os`)

### 3. Deploy

```bash
# Test connectivity
ansible all -i inventory-multi-vendor.yml -m ping

# Deploy everything
ansible-playbook -i inventory-multi-vendor.yml site-multi-vendor.yml

# Deploy specific vendor
ansible-playbook -i inventory-multi-vendor.yml site-multi-vendor.yml --limit srlinux_devices
ansible-playbook -i inventory-multi-vendor.yml site-multi-vendor.yml --limit arista_devices

# Deploy specific role
ansible-playbook -i inventory-multi-vendor.yml site-multi-vendor.yml --tags interfaces
```

## How It Works

### Dispatcher Pattern

Each role has a `main.yml` that dispatches to vendor-specific implementations:

```yaml
# roles/multi_vendor_interfaces/tasks/main.yml
- include_tasks: srlinux.yml
  when: ansible_network_os == 'nokia.srlinux'

- include_tasks: arista_eos.yml
  when: ansible_network_os == 'arista.eos'

- include_tasks: sonic.yml
  when: ansible_network_os == 'dellemc.sonic'
```

### Common Data Model

All vendors use the same variable structure:

```yaml
interfaces:
  - name: ethernet-1/1      # Generic format
    ip: 10.1.1.0/31
    description: "to-leaf1"
```

### Vendor-Specific Translation

Each vendor implementation:
1. Translates interface names (ethernet-1/1 → Ethernet1/1)
2. Uses native YANG models
3. Calls vendor-specific modules

## Interface Name Translation

Use the provided filters:

```yaml
# In playbook
- name: Example
  debug:
    msg: "{{ 'ethernet-1/1' | to_arista_interface }}"  # Output: Ethernet1/1
```

Translations:
- `ethernet-1/1` (generic)
  - SR Linux: `ethernet-1/1`
  - Arista: `Ethernet1/1`
  - SONiC: `Ethernet0` (Dell), `Ethernet0` (Mellanox)

## Adding a New Vendor

1. Create vendor group in inventory:
```yaml
juniper_devices:
  vars:
    ansible_network_os: juniper.junos
  hosts:
    spine3: ...
```

2. Add vendor tasks to each role:
```bash
# In each role's tasks/
touch juniper.yml
```

3. Update dispatcher in `main.yml`:
```yaml
- include_tasks: juniper.yml
  when: ansible_network_os == 'juniper.junos'
```

4. Implement using Juniper native modules/models

## Testing Strategy

### Unit Testing (Per Vendor)

```bash
# Test SR Linux only
ansible-playbook site-multi-vendor.yml --limit srlinux_devices --check

# Test Arista only
ansible-playbook site-multi-vendor.yml --limit arista_devices --check
```

### Integration Testing (Mixed)

```bash
# Deploy mixed topology
ansible-playbook site-multi-vendor.yml

# Verify cross-vendor connectivity
ansible-playbook site-multi-vendor.yml --tags verify
```

### Comparison Testing

Deploy same config to different vendors and compare:

```bash
# Deploy to SR Linux spine
ansible-playbook site-multi-vendor.yml --limit spine1

# Deploy to Arista spine
ansible-playbook site-multi-vendor.yml --limit spine2

# Compare BGP state, routing tables, etc.
```

## Troubleshooting

### Check Network OS Detection

```bash
ansible all -i inventory-multi-vendor.yml -m debug -a "var=ansible_network_os"
```

### Verbose Output

```bash
ansible-playbook site-multi-vendor.yml -vvv
```

### Test Single Device

```bash
ansible-playbook site-multi-vendor.yml --limit spine1 --tags interfaces -vv
```

### Validate Inventory

```bash
ansible-inventory -i inventory-multi-vendor.yml --list
ansible-inventory -i inventory-multi-vendor.yml --graph
```

## Best Practices

1. **Keep data model vendor-agnostic**: Define topology once
2. **Use native models**: Don't force OpenConfig if incomplete
3. **Test per vendor**: Each vendor path needs validation
4. **Document quirks**: Note vendor-specific behaviors
5. **Version lock**: Pin collection versions for stability
6. **Interface mapping**: Use filters for name translation
7. **Idempotency**: Ensure tasks can run multiple times safely

## Common Pitfalls

1. **Interface naming**: Different vendors use different formats
2. **Feature parity**: Not all vendors support all features
3. **Module versions**: API changes between collection versions
4. **Connection types**: httpapi vs local vs network_cli
5. **Authentication**: Different credential requirements
6. **Port numbers**: gNMI, NETCONF, API ports vary

## Next Steps

1. Extend to BGP configuration role
2. Add EVPN/VXLAN overlay role
3. Build comprehensive verification role
4. Create CI/CD pipeline for testing
5. Add monitoring/telemetry collection
