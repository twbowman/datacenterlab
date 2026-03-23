# Arista EOS BGP Role

This role configures BGP on Arista EOS devices using the `arista.eos` collection, supporting iBGP with route reflectors and EVPN address family.

## Requirements

- Ansible 2.9 or higher
- `arista.eos` collection installed (`ansible-galaxy collection install arista.eos`)
- Network connectivity to Arista EOS devices

## Role Variables

### Required Variables

- `asn`: BGP Autonomous System Number
- `router_id`: BGP router ID (typically loopback IP)
- `bgp_neighbors`: List of BGP neighbor configurations
  - `peer_address`: Neighbor IP address
  - `peer_asn`: Neighbor AS number
  - `description`: Neighbor description (optional)

### Optional Variables

- `bgp_role`: BGP role (`route_reflector` or `client`)
- `eos_bgp_debug`: Enable debug output (default: false)

## Dependencies

None

## Example Playbook

### Route Reflector (Spine)

```yaml
- hosts: spines
  roles:
    - role: eos_bgp
      vars:
        asn: 65000
        router_id: 10.0.0.1
        bgp_role: route_reflector
        bgp_neighbors:
          - peer_address: 10.0.1.1
            peer_asn: 65000
            description: "leaf1"
          - peer_address: 10.0.1.2
            peer_asn: 65000
            description: "leaf2"
```

### Route Reflector Client (Leaf)

```yaml
- hosts: leafs
  roles:
    - role: eos_bgp
      vars:
        asn: 65000
        router_id: 10.0.1.1
        bgp_role: client
        bgp_neighbors:
          - peer_address: 10.0.0.1
            peer_asn: 65000
            description: "spine1"
          - peer_address: 10.0.0.2
            peer_asn: 65000
            description: "spine2"
```

## Features

- iBGP configuration with route reflectors
- IPv4 unicast address family
- EVPN address family (L2VPN EVPN)
- Automatic neighbor activation for both address families
- Route reflector client configuration for spines

## Production Compatibility

This role is designed for direct production use. The same playbook works for:
- Lab environments (containerized Arista cEOS)
- Production environments (physical Arista switches)

Only the inventory file needs to change between environments.

## License

MIT

## Author

Network Automation Team
