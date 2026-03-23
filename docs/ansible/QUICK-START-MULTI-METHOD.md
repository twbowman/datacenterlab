# Quick Start: Multi-Method Configuration

## TL;DR

```bash
# Deploy everything with multi-vendor dispatcher (default)
ansible-playbook -i inventory.yml site.yml

# Or from host machine
ansible-playbook -i ansible/inventory.yml ansible/site.yml
```

## What Changed?

The ansible directory now supports multiple vendors and configuration methods. The main `site.yml` uses a dispatcher pattern that auto-detects `ansible_network_os` and routes to vendor-specific roles.

## Available Methods

| Method | Status | Command |
|--------|--------|---------|
| SR Linux gNMI | ✅ Ready | `ansible-playbook methods/srlinux_gnmi/site.yml` |
| OpenConfig | ✅ Ready | `ansible-playbook -i inventory.yml site-openconfig.yml` |
| Multi-vendor dispatcher | ✅ Ready | `ansible-playbook -i inventory.yml site.yml` |
| gNMI Modules | 🚧 Planned | `ansible-playbook methods/gnmi_modules/site.yml` |
| REST | 💡 Future | `ansible-playbook methods/rest/site.yml` |

## Quick Commands

### Deploy Everything
```bash
# Default (multi-vendor dispatcher)
ansible-playbook -i inventory.yml site.yml

# SR Linux gNMI method directly
ansible-playbook methods/srlinux_gnmi/site.yml

# OpenConfig method
ansible-playbook -i inventory.yml site-openconfig.yml
```

### Deploy Components
```bash
# Interfaces only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml

# BGP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml

# LLDP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-lldp.yml

# EVPN/VXLAN
ansible-playbook methods/srlinux_gnmi/playbooks/configure-evpn.yml
```

### Use Tags
```bash
# Deploy only BGP
ansible-playbook site.yml --tags bgp

# Deploy interfaces and LLDP
ansible-playbook site.yml --tags interfaces,lldp

# Skip LLDP
ansible-playbook site.yml --skip-tags lldp
```

### Limit to Devices
```bash
# Spines only
ansible-playbook site.yml --limit spines

# One device
ansible-playbook site.yml --limit spine1

# Leafs only
ansible-playbook site.yml --limit leafs

# Specific vendor group (multi-vendor inventory)
ansible-playbook -i inventory-multi-vendor.yml site.yml --limit srlinux_devices
```

## Common Workflows

### Fresh Deployment
```bash
# Deploy topology
./scripts/deploy.sh

# Wait for boot, then configure
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Verify
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify.yml
```

### Deploy with Validation
```bash
# Deploy + auto-validate
./scripts/deploy.sh --validate
```

### Update Configuration
```bash
# Edit inventory
vim ansible/inventory.yml

# Apply changes
ansible-playbook -i inventory.yml site.yml

# Verify
ansible-playbook playbooks/validate.yml
```

### Deploy Specific Component
```bash
# Update only interfaces
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml

# Update only BGP
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml
```

## Verification and Validation

```bash
# SR Linux gNMI verification
ansible-playbook methods/srlinux_gnmi/playbooks/verify.yml
ansible-playbook methods/srlinux_gnmi/playbooks/verify-detailed.yml
ansible-playbook methods/srlinux_gnmi/playbooks/verify-evpn.yml

# Shared validation playbooks
ansible-playbook playbooks/validate.yml
ansible-playbook playbooks/validate-bgp.yml
ansible-playbook playbooks/validate-interfaces.yml
ansible-playbook playbooks/validate-lldp.yml
ansible-playbook playbooks/validate-evpn.yml
```

## Troubleshooting

### Check Syntax
```bash
ansible-playbook site.yml --syntax-check
```

### Dry Run
```bash
ansible-playbook site.yml --check
```

### Verbose Output
```bash
ansible-playbook site.yml -vvv
```

### Test Dispatcher Pattern
```bash
ansible-playbook test-dispatcher.yml
```

### Test Connectivity
```bash
ansible all -m ping
```

## Method Selection Guide

### Use SR Linux gNMI Method When:
- Working exclusively with SR Linux devices
- Need true idempotency via gNMI protocol
- Want direct gnmic CLI tool access
- Performance is critical

### Use Multi-Vendor Dispatcher When:
- Mixed vendor environment
- Want automatic OS detection and routing
- Need vendor-specific role selection

### Use OpenConfig Method When:
- Want vendor-neutral configuration
- Working with devices that support OpenConfig SET operations
- Note: SR Linux only supports OpenConfig for read operations

## File Locations

### Main Files
- `ansible/site.yml` - Multi-vendor dispatcher playbook
- `ansible/site-openconfig.yml` - OpenConfig playbook
- `ansible/site-multi-vendor.yml` - Multi-vendor deployment
- `ansible/inventory.yml` - SR Linux inventory
- `ansible/inventory-multi-vendor.yml` - Multi-vendor inventory

### SR Linux gNMI Method
- `ansible/methods/srlinux_gnmi/site.yml` - Method main playbook
- `ansible/methods/srlinux_gnmi/playbooks/` - Component playbooks
- `ansible/methods/srlinux_gnmi/roles/` - gNMI roles

### Documentation
- `ansible/README.md` - Main documentation
- `docs/ansible/METHODS.md` - Method overview
- `docs/ansible/COMPARISON.md` - Method comparison
- `ansible/methods/srlinux_gnmi/README.md` - gNMI method details
- `docs/ansible/DISPATCHER-PATTERN.md` - Dispatcher pattern details