# Juniper Junos BGP Role

This role configures BGP routing on Juniper Junos devices using the `junipernetworks.junos` collection. It supports iBGP with route reflectors and EVPN address family for VXLAN fabrics.

## Requirements

- Juniper Junos device (physical, VM, or cRPD container)
- `junipernetworks.junos` Ansible collection installed
- NETCONF access to the device
- Interfaces must be configured before BGP

## Role Variables

### Required Variables

- `asn`: BGP autonomous system number
- `router_id`: BGP router ID (typically loopback IP)

### Optional Variables

- `bgp_neighbors`: List of BGP neighbor configurations
  - `peer_address`: Neighbor IP address
  - `peer_asn`: Neighbor AS number
  - `description`: Neighbor description (optional)
- `bgp_role`: Set to "route_reflector" for spine devices
- `junos_bgp_debug`: Enable debug output (default: false)

## Features

- BGP global configuration with router ID
- IPv4 unicast address family
- EVPN address family for VXLAN
- iBGP neighbor configuration
- Route reflector support for spine devices
- Idempotent operations (safe to run multiple times)

## Example Inventory

```yaml
juniper_spines:
  hosts:
    juniper-spine1:
      ansible_host: 172.20.20.31
      router_id: 10.0.0.3
      asn: 65000
      bgp_role: route_reflector
      bgp_neighbors:
        - peer_address: 10.0.1.1
          peer_asn: 65000
          description: "leaf1"
        - peer_address: 10.0.1.2
          peer_asn: 65000
          description: "leaf2"

juniper_leafs:
  hosts:
    juniper-leaf1:
      ansible_host: 172.20.20.32
      router_id: 10.0.1.10
      asn: 65000
      bgp_neighbors:
        - peer_address: 10.0.0.1
          peer_asn: 65000
          description: "spine1"
        - peer_address: 10.0.0.2
          peer_asn: 65000
          description: "spine2"
```

## Example Playbook

```yaml
- hosts: juniper_devices
  roles:
    - junos_interfaces  # Must run first
    - junos_ospf        # Underlay routing
    - junos_bgp         # Overlay routing
```

## Dependencies

- junos_interfaces role (interfaces must be configured first)

## License

MIT

## Author Information

Production Network Testing Lab
