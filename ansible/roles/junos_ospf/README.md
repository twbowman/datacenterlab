# Juniper Junos OSPF Role

This role configures OSPF routing on Juniper Junos devices using the `junipernetworks.junos` collection. It configures OSPF as the underlay routing protocol for datacenter fabrics.

## Requirements

- Juniper Junos device (physical, VM, or cRPD container)
- `junipernetworks.junos` Ansible collection installed
- NETCONF access to the device
- Interfaces must be configured before OSPF

## Role Variables

### Required Variables

- `router_id`: OSPF router ID (typically loopback IP)
- `interfaces`: List of interface configurations (same as junos_interfaces role)

### Optional Variables

- `loopback_ip`: Loopback0 IP address (for leaf devices, advertised as passive)
- `junos_ospf_debug`: Enable debug output (default: false)

## Features

- OSPF process configuration with router ID
- Area 0 (backbone) configuration
- Point-to-point network type on physical interfaces
- Passive interface on loopback (leafs only)
- Idempotent operations (safe to run multiple times)

## Interface Name Translation

The role uses the `to_junos_interface` filter to translate generic interface names to Junos format:

- `ethernet-1/1` → `ge-0/0/0`
- `ethernet-1/2` → `ge-0/0/1`

## Example Inventory

```yaml
juniper_devices:
  vars:
    ansible_network_os: juniper.junos
    ansible_connection: netconf
    ansible_user: admin
    ansible_password: admin
  hosts:
    juniper-spine1:
      ansible_host: 172.20.20.31
      router_id: 10.0.0.3
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.1.0/31
          description: "to-leaf1"
        - name: ethernet-1/2
          ip: 10.2.1.0/31
          description: "to-leaf2"
    
    juniper-leaf1:
      ansible_host: 172.20.20.32
      router_id: 10.0.1.10
      loopback_ip: 10.0.1.10/32
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.1.1/31
          description: "to-spine1"
```

## Example Playbook

```yaml
- hosts: juniper_devices
  roles:
    - junos_interfaces  # Must run first
    - junos_ospf        # Underlay routing
    - junos_bgp         # Overlay routing (optional)
```

## Dependencies

- junos_interfaces role (interfaces must be configured first)

## License

MIT

## Author Information

Production Network Testing Lab
