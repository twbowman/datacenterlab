# Datacenter Automation Ansible Collection

Multi-vendor datacenter network automation using gNMI, OpenConfig, and vendor-native YANG models.

## Supported Vendors

| Vendor | NOS | Config Method | Telemetry |
|--------|-----|---------------|-----------|
| Nokia | SR Linux | gNMI SET (native YANG) | OpenConfig + native |
| Arista | cEOS | gNMI SET | OpenConfig |
| Dell | SONiC | gNMI SET | OpenConfig + native |
| Juniper | cRPD/JunOS | gNMI SET | OpenConfig + native |

## Installation

```bash
# From Galaxy (when published)
ansible-galaxy collection install datacenter.automation

# From local build
ansible-galaxy collection build ansible-collection/
ansible-galaxy collection install datacenter-automation-1.0.0.tar.gz

# From git
ansible-galaxy collection install git+https://github.com/twbowman/ansible-network-automation.git
```

## Collection Structure

```
ansible-collection/
├── galaxy.yml                    # Collection metadata
├── README.md
├── plugins/
│   ├── modules/
│   │   └── gnmi_validate.py      # gNMI state validation module
│   ├── filter/
│   │   └── interface_names.py    # Cross-vendor interface name translation
│   ├── callback/
│   │   └── validation_report.py  # JSON validation report aggregator
│   └── inventory/
│       └── dynamic_inventory.py  # Containerlab topology → Ansible inventory
├── roles/
│   ├── gnmi_interfaces/          # SR Linux interface config (gNMI native)
│   ├── gnmi_bgp/                 # SR Linux BGP config (gNMI native)
│   ├── gnmi_ospf/                # SR Linux OSPF config (gNMI native)
│   ├── gnmi_lldp/                # SR Linux LLDP config (gNMI native)
│   ├── gnmi_evpn_vxlan/          # SR Linux EVPN/VXLAN config (gNMI native)
│   ├── gnmi_system/              # SR Linux system config (gNMI native)
│   ├── gnmi_static_routes/       # SR Linux static routes (gNMI native)
│   ├── eos_interfaces/           # Arista interface config
│   ├── eos_bgp/                  # Arista BGP config
│   ├── eos_ospf/                 # Arista OSPF config
│   ├── eos_evpn_vxlan/           # Arista EVPN/VXLAN config
│   ├── sonic_interfaces/         # SONiC interface config
│   ├── sonic_bgp/                # SONiC BGP config
│   ├── sonic_ospf/               # SONiC OSPF config
│   ├── sonic_evpn_vxlan/         # SONiC EVPN/VXLAN config
│   ├── junos_interfaces/         # Juniper interface config
│   ├── junos_bgp/                # Juniper BGP config
│   ├── junos_ospf/               # Juniper OSPF config
│   ├── junos_evpn_vxlan/         # Juniper EVPN/VXLAN config
│   ├── openconfig_interfaces/    # Vendor-neutral OpenConfig interfaces
│   ├── openconfig_bgp/           # Vendor-neutral OpenConfig BGP
│   ├── openconfig_ospf/          # Vendor-neutral OpenConfig OSPF
│   ├── openconfig_lldp/          # Vendor-neutral OpenConfig LLDP
│   ├── config_validation/        # Configuration validation utilities
│   ├── config_rollback/          # Configuration rollback utilities
│   └── multi_vendor_interfaces/  # Multi-vendor interface dispatcher
├── playbooks/
│   ├── site.yml                  # Main dispatcher playbook
│   ├── site-srlinux-gnmi.yml     # SR Linux gNMI-specific playbook
│   ├── site-multi-vendor.yml     # Multi-vendor playbook
│   ├── site-openconfig.yml       # OpenConfig-only playbook
│   ├── validate.yml              # Master validation playbook
│   ├── validate-bgp.yml          # BGP session validation
│   ├── validate-evpn.yml         # EVPN route validation
│   ├── validate-lldp.yml         # LLDP neighbor validation
│   ├── validate-client-lldp.yml  # Client LLDP validation
│   └── validate-interfaces.yml   # Interface state validation
├── examples/
│   ├── group_vars/               # Example variable files
│   │   ├── all.yml
│   │   ├── spines.yml
│   │   ├── leafs.yml
│   │   ├── srlinux_devices.yml
│   │   ├── arista_devices.yml
│   │   ├── sonic_devices.yml
│   │   └── juniper_devices.yml
│   └── inventories/
│       ├── inventory-lab.yml
│       └── inventory-multi-vendor.yml
└── templates/
    ├── srlinux-config.j2
    └── evpn_vxlan_data_model.md
```

## Quick Start

### 1. Configure your inventory

Copy an example inventory and customize for your environment:

```bash
cp examples/inventories/inventory-lab.yml inventory.yml
# Edit inventory.yml with your device IPs and credentials
```

### 2. Set up group variables

```bash
cp -r examples/group_vars/ group_vars/
# Edit group_vars/ to match your network design
```

### 3. Run the dispatcher playbook

```bash
# Configure all devices (auto-detects vendor OS)
ansible-playbook -i inventory.yml datacenter.automation.site

# Or use vendor-specific playbook
ansible-playbook -i inventory.yml datacenter.automation.site-srlinux-gnmi
```

### 4. Validate

```bash
# Run all validation checks
ansible-playbook -i inventory.yml datacenter.automation.validate
```

## Key Plugins

### gnmi_validate module

Queries device state via gNMI GET and compares against expected values:

```yaml
- name: Validate BGP sessions
  datacenter.automation.gnmi_validate:
    host: "{{ ansible_host }}"
    port: "{{ gnmi_port }}"
    username: "{{ gnmi_username }}"
    password: "{{ gnmi_password }}"
    check_name: "bgp_sessions"
    path: "/network-instances/network-instance[name=default]/protocols/protocol/bgp/neighbors/neighbor/state"
    origin: "openconfig"
    expected:
      session_state: "ESTABLISHED"
    remediation_hint: "Check BGP config and OSPF underlay reachability"
```

### interface_names filter

Translates interface names across vendors:

```yaml
# SR Linux → Arista
{{ "ethernet-1/1" | to_arista_interface }}  # Ethernet1/1

# Arista → SR Linux
{{ "Ethernet1/1" | to_srlinux_interface }}  # ethernet-1/1
```

## Dependencies

- `gnmic` CLI (for gNMI SET operations in roles)
- `pygnmi` Python package (for gnmi_validate module)
- `dictdiffer` Python package (for state comparison)

## License

MIT
