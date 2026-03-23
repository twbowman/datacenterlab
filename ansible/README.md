# Ansible Network Automation - Multi-Vendor Dispatcher

A role-based Ansible project supporting multiple vendors and configuration methods for network devices.

## Overview

The main `site.yml` uses a multi-vendor dispatcher pattern that detects `ansible_network_os` and routes configuration to the appropriate vendor-specific roles. Supported vendors:

- **Nokia SR Linux** (`nokia.srlinux`) - via gNMI with native YANG paths
- **Arista EOS** (`arista.eos`) - via eAPI/httpapi
- **SONiC** (`dellemc.sonic`) - via REST API/httpapi
- **Juniper** (`juniper.junos`) - via NETCONF

### Configuration Methods

- **srlinux_gnmi Method** (`methods/srlinux_gnmi/`) - Uses gnmic CLI tool with native SR Linux YANG paths
- **OpenConfig Method** (`site-openconfig.yml`) - Uses OpenConfig YANG models for vendor-neutral configuration
- **gNMI Modules Method** (`methods/gnmi_modules/`) - Planned, uses Ansible gNMI modules
- **REST Method** (`methods/rest/`) - Possible future, uses JSON-RPC API
- **NETCONF Method** (`methods/netconf/`) - N/A for SR Linux (doesn't support NETCONF)

### Important: SR Linux and OpenConfig Limitations

SR Linux only supports OpenConfig YANG models for **read operations** (monitoring/telemetry). Configuration changes **must use native SR Linux YANG paths**.

- OpenConfig GET operations work (reading state, monitoring)
- OpenConfig SET operations fail with "OpenConfig management interface is not operational"
- Native SR Linux paths work for all configuration operations

## Quick Start

### Deploy with Dispatcher (Default)
```bash
# Multi-vendor dispatcher - routes to correct roles per device
ansible-playbook -i inventory.yml site.yml

# From host machine via orb
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/site.yml
```

### Deploy with Specific Method
```bash
# SR Linux gNMI method directly
ansible-playbook methods/srlinux_gnmi/site.yml

# OpenConfig method
ansible-playbook -i inventory.yml site-openconfig.yml

# Multi-vendor site playbook
ansible-playbook -i inventory-multi-vendor.yml site-multi-vendor.yml
```

## Structure

```
ansible/
├── site.yml                       # Main playbook (multi-vendor dispatcher)
├── site-openconfig.yml            # OpenConfig-based configuration
├── site-multi-vendor.yml          # Multi-vendor deployment playbook
├── test-dispatcher.yml            # Dispatcher pattern unit tests
├── inventory.yml                  # SR Linux device inventory
├── inventory-multi-vendor.yml     # Multi-vendor device inventory
├── inventory-dynamic.yml          # Auto-generated dynamic inventory
├── inventory-dynamic-test.yml     # Dynamic inventory test
├── ansible.cfg                    # Shared configuration
├── requirements.yml               # Ansible collection requirements
├── group_vars/                    # Shared variables
│   ├── all.yml                    # Default validation paths (OpenConfig)
│   ├── arista_devices.yml         # Arista-specific variables
│   ├── juniper_devices.yml        # Juniper-specific variables
│   ├── sonic_devices.yml          # SONiC-specific variables
│   ├── srlinux_devices.yml        # SR Linux-specific variables
│   ├── leafs.yml                  # Leaf-specific variables
│   └── spines.yml                 # Spine-specific variables
│
├── methods/                       # Configuration methods
│   ├── srlinux_gnmi/              # gnmic CLI tool (implemented)
│   │   ├── site.yml
│   │   ├── playbooks/
│   │   │   ├── configure-interfaces.yml
│   │   │   ├── configure-bgp.yml
│   │   │   ├── configure-lldp.yml
│   │   │   ├── configure-evpn.yml
│   │   │   ├── verify.yml
│   │   │   ├── verify-detailed.yml
│   │   │   ├── verify-evpn.yml
│   │   │   └── diagnose.yml
│   │   ├── roles/
│   │   │   ├── gnmi_system/
│   │   │   ├── gnmi_interfaces/
│   │   │   ├── gnmi_lldp/
│   │   │   ├── gnmi_ospf/
│   │   │   ├── gnmi_bgp/
│   │   │   ├── gnmi_evpn_vxlan/
│   │   │   └── gnmi_static_routes/
│   │   └── README.md
│   ├── gnmi_modules/              # Ansible gNMI modules (planned)
│   ├── netconf/                   # Not applicable for SR Linux
│   └── rest/                      # Possible future
│
├── roles/                         # Vendor-specific and shared roles
│   ├── config_validation/         # Pre-deployment config validation
│   ├── config_rollback/           # Config state capture and rollback
│   ├── multi_vendor_interfaces/   # Multi-vendor interface abstraction
│   ├── openconfig_interfaces/     # OpenConfig interface config
│   ├── openconfig_lldp/           # OpenConfig LLDP config
│   ├── openconfig_ospf/           # OpenConfig OSPF config
│   ├── openconfig_bgp/            # OpenConfig BGP config
│   ├── eos_interfaces/            # Arista EOS interfaces
│   ├── eos_ospf/                  # Arista EOS OSPF
│   ├── eos_bgp/                   # Arista EOS BGP
│   ├── eos_evpn_vxlan/            # Arista EOS EVPN/VXLAN
│   ├── junos_interfaces/          # Juniper interfaces
│   ├── junos_ospf/                # Juniper OSPF
│   ├── junos_bgp/                 # Juniper BGP
│   ├── junos_evpn_vxlan/          # Juniper EVPN/VXLAN
│   ├── sonic_interfaces/          # SONiC interfaces
│   ├── sonic_ospf/                # SONiC OSPF
│   ├── sonic_bgp/                 # SONiC BGP
│   └── sonic_evpn_vxlan/          # SONiC EVPN/VXLAN
│
├── playbooks/                     # Shared utility and validation playbooks
│   ├── configure-bgp.yml
│   ├── configure-interfaces.yml
│   ├── configure-lldp.yml
│   ├── configure-evpn-arista.yml
│   ├── validate.yml
│   ├── validate-bgp.yml
│   ├── validate-interfaces.yml
│   ├── validate-lldp.yml
│   ├── validate-evpn.yml
│   ├── validate-evpn-data-model.yml
│   ├── validate-client-lldp.yml
│   ├── verify.yml
│   ├── verify-evpn-arista.yml
│   └── verify-gnmic.yml
│
├── plugins/                       # Custom plugins
│   └── inventory/
│       └── dynamic_inventory.py   # gNMI-based OS detection inventory
│
├── library/                       # Custom modules
│   └── gnmi_validate.py           # gNMI validation module
│
├── callback_plugins/              # Custom callback plugins
│   └── validation_report.py       # Validation report generator
│
├── filter_plugins/                # Custom Jinja2 filters
│   └── interface_names.py         # Interface name translation
│
├── templates/                     # Jinja2 templates
└── archive/                       # Archived playbooks
```

## Common Tasks

### Full Deployment
```bash
# Deploy via dispatcher (auto-detects vendor per device)
ansible-playbook -i inventory.yml site.yml

# Deploy to specific vendor group
ansible-playbook -i inventory-multi-vendor.yml site.yml --limit srlinux_devices
ansible-playbook -i inventory-multi-vendor.yml site.yml --limit arista_devices

# Deploy to specific hosts
ansible-playbook site.yml --limit spines
ansible-playbook site.yml --limit leaf1
```

### Deploy Components
```bash
# SR Linux gNMI method
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml
ansible-playbook methods/srlinux_gnmi/playbooks/configure-lldp.yml
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml
ansible-playbook methods/srlinux_gnmi/playbooks/configure-evpn.yml
```

### Using Tags
```bash
# Deploy specific components
ansible-playbook site.yml --tags interfaces
ansible-playbook site.yml --tags ospf
ansible-playbook site.yml --tags bgp
ansible-playbook site.yml --tags evpn
ansible-playbook site.yml --tags lldp

# Combine tags
ansible-playbook site.yml --tags interfaces,bgp

# Skip components
ansible-playbook site.yml --skip-tags lldp
```

### Verification and Validation
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
ansible-playbook playbooks/validate-client-lldp.yml

# Verify with tags
ansible-playbook playbooks/validate.yml --tags bgp
ansible-playbook playbooks/validate.yml --tags lldp
```

### Debug and Dry Run
```bash
# Verbose output
ansible-playbook site.yml -vvv

# Check what would change
ansible-playbook site.yml --check

# Check syntax
ansible-playbook site.yml --syntax-check

# Test dispatcher pattern
ansible-playbook test-dispatcher.yml
```

## Available Tags

| Tag | Description |
|-----|-------------|
| `config` | All configuration tasks |
| `system` | System configuration |
| `interfaces` | Interface configuration |
| `lldp` | LLDP configuration |
| `ospf` | OSPF underlay routing |
| `underlay` | Underlay routing protocols |
| `bgp` | BGP overlay routing |
| `overlay` | Overlay routing protocols |
| `evpn` | EVPN configuration |
| `vxlan` | VXLAN configuration |
| `validation` | Pre-deployment validation |
| `verify` | Post-deployment verification |

## Inventories

| File | Description |
|------|-------------|
| `inventory.yml` | SR Linux single-vendor (default) |
| `inventory-multi-vendor.yml` | Multi-vendor (SR Linux, Arista, SONiC) |
| `inventory-dynamic.yml` | Auto-generated via gNMI OS detection |
| `inventory-dynamic-test.yml` | Dynamic inventory test |

## Dynamic Inventory

The project includes a dynamic inventory plugin (`plugins/inventory/dynamic_inventory.py`) that queries containerlab devices via gNMI capabilities to auto-detect their OS:

```bash
# Generate dynamic inventory from topology
python3 plugins/inventory/dynamic_inventory.py -t ../topology-srlinux.yml -o inventory-dynamic.yml

# Use with Ansible
ansible-playbook -i inventory-dynamic.yml site.yml
```

Detection order: gNMI capabilities → containerlab labels → containerlab kind.

## Roles

### SR Linux gNMI Roles (`methods/srlinux_gnmi/roles/`)

| Role | Description |
|------|-------------|
| `gnmi_system` | System-level configuration |
| `gnmi_interfaces` | Interface and IP configuration |
| `gnmi_lldp` | LLDP neighbor discovery |
| `gnmi_ospf` | OSPF underlay routing |
| `gnmi_bgp` | BGP overlay routing (with route reflector support) |
| `gnmi_evpn_vxlan` | EVPN/VXLAN fabric overlay |
| `gnmi_static_routes` | Static route configuration |

### Vendor-Specific Roles (`roles/`)

| Vendor | Interfaces | OSPF | BGP | EVPN/VXLAN |
|--------|-----------|------|-----|------------|
| Arista EOS | `eos_interfaces` | `eos_ospf` | `eos_bgp` | `eos_evpn_vxlan` |
| Juniper | `junos_interfaces` | `junos_ospf` | `junos_bgp` | `junos_evpn_vxlan` |
| SONiC | `sonic_interfaces` | `sonic_ospf` | `sonic_bgp` | `sonic_evpn_vxlan` |

### OpenConfig Roles (`roles/`)

| Role | Description |
|------|-------------|
| `openconfig_interfaces` | Vendor-neutral interface config |
| `openconfig_lldp` | Vendor-neutral LLDP config |
| `openconfig_ospf` | Vendor-neutral OSPF config |
| `openconfig_bgp` | Vendor-neutral BGP config |

### Utility Roles (`roles/`)

| Role | Description |
|------|-------------|
| `config_validation` | Pre-deployment configuration syntax validation |
| `config_rollback` | Configuration state capture and rollback |
| `multi_vendor_interfaces` | Multi-vendor interface abstraction layer |

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
ansible all -m ping

# Check inventory
ansible-inventory --list

# Verify gNMI connectivity
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities
```

### Debugging
```bash
# Verbose output
ansible-playbook site.yml -vvv

# Step through tasks
ansible-playbook site.yml --step

# Start at specific task
ansible-playbook site.yml --start-at-task="Configure BGP"
```

## Documentation

- [SR Linux gNMI Method](methods/srlinux_gnmi/README.md) - gNMI method details
- [Underlay Routing](methods/srlinux_gnmi/UNDERLAY-ROUTING.md) - OSPF underlay design
- [Ansible Architecture](../docs/ansible/ARCHITECTURE.md) - Architecture overview
- [Dispatcher Pattern](../docs/ansible/DISPATCHER-PATTERN.md) - Multi-vendor dispatcher
- [Multi-Vendor Architecture](../docs/ansible/MULTI-VENDOR-ARCHITECTURE.md) - Multi-vendor design
- [EVPN/VXLAN Guide](../docs/ansible/EVPN-VXLAN-GUIDE.md) - EVPN configuration guide
- [Methods Comparison](../docs/ansible/COMPARISON.md) - Method comparison