# netgnmi.dcfabric — Ansible Collection

Multi-vendor datacenter CLOS fabric automation via gNMI. Configure spine-leaf fabrics, validate topology state, and manage EVPN/VXLAN overlays across vendors using a single set of playbooks.

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
ansible-galaxy collection install netgnmi.dcfabric

# From local build
ansible-galaxy collection build .
ansible-galaxy collection install netgnmi-dcfabric-1.0.0.tar.gz

# From git
ansible-galaxy collection install git+https://github.com/twbowman/ansible-collection-netgnmi-dcfabric.git
```

## What's Included

### Roles (26)

Vendor-specific configuration roles for spine-leaf CLOS fabrics:

- **SR Linux (gNMI native)**: `gnmi_interfaces`, `gnmi_bgp`, `gnmi_ospf`, `gnmi_lldp`, `gnmi_evpn_vxlan`, `gnmi_system`, `gnmi_static_routes`
- **Arista EOS**: `eos_interfaces`, `eos_bgp`, `eos_ospf`, `eos_evpn_vxlan`
- **SONiC**: `sonic_interfaces`, `sonic_bgp`, `sonic_ospf`, `sonic_evpn_vxlan`
- **Juniper**: `junos_interfaces`, `junos_bgp`, `junos_ospf`, `junos_evpn_vxlan`
- **OpenConfig**: `openconfig_interfaces`, `openconfig_bgp`, `openconfig_ospf`, `openconfig_lldp`
- **Utility**: `config_validation`, `config_rollback`, `multi_vendor_interfaces`

### Playbooks

- `site.yml` — Main dispatcher (auto-detects vendor OS)
- `site-srlinux-gnmi.yml` — SR Linux gNMI-specific
- `site-multi-vendor.yml` — Multi-vendor
- `validate.yml` — Master validation (all checks)
- `validate-bgp.yml` — BGP session validation
- `validate-evpn.yml` — EVPN route distribution
- `validate-lldp.yml` — LLDP neighbor adjacencies
- `validate-client-lldp.yml` — Client LLDP validation
- `validate-interfaces.yml` — Interface state validation

### Plugins

- **Module**: `gnmi_validate` — gNMI GET state comparison with structured diffs and remediation hints
- **Filter**: `interface_names` — Cross-vendor interface name translation
- **Callback**: `validation_report` — JSON validation report aggregator
- **Inventory**: `dynamic_inventory` — Containerlab topology → Ansible inventory with OS detection

## Quick Start

### 1. Configure inventory

```bash
cp examples/inventories/inventory-lab.yml inventory.yml
# Edit with your device IPs and credentials
```

### 2. Set up group variables

```bash
cp -r examples/group_vars/ group_vars/
# Edit to match your network design
```

### 3. Configure the fabric

```bash
ansible-playbook -i inventory.yml netgnmi.dcfabric.site
```

### 4. Validate

```bash
ansible-playbook -i inventory.yml netgnmi.dcfabric.validate
```

## Key Plugins

### gnmi_validate module

Queries device state via gNMI GET and compares against expected values:

```yaml
- name: Validate BGP sessions
  netgnmi.dcfabric.gnmi_validate:
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

```yaml
{{ "ethernet-1/1" | to_arista_interface }}  # Ethernet1/1
{{ "Ethernet1/1" | to_srlinux_interface }}  # ethernet-1/1
```

## Dependencies

- `gnmic` CLI (gNMI SET operations in roles)
- `pygnmi` Python package (gnmi_validate module)
- `dictdiffer` Python package (state comparison)

## Future: netgnmi.core

When additional topology collections are built (e.g., butterfly fabric), the topology-agnostic plugins (`gnmi_validate`, `interface_names`, `validation_report`, `dynamic_inventory`) will be extracted into `netgnmi.core` as a shared dependency.

## License

MIT
