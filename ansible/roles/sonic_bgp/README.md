# SONiC BGP Role

Configures BGP routing protocol on SONiC devices using the dellemc.enterprise_sonic collection.

## Requirements

- dellemc.enterprise_sonic collection
- SONiC device with REST API enabled
- Ansible connection: httpapi

## Role Variables

### Required Variables

- `asn`: BGP autonomous system number
- `router_id`: BGP router ID (IPv4 address format)
- `bgp_neighbors`: List of BGP neighbor configurations
  - `peer_address`: Neighbor IP address
  - `peer_asn`: Neighbor AS number
  - `description`: Neighbor description (optional)

### Optional Variables

- `bgp_role`: Set to "route_reflector" for spine devices (enables route reflector client configuration)
- `sonic_bgp_debug`: Enable debug output (default: false)

## Features

- Configures iBGP sessions
- Supports IPv4 unicast and L2VPN EVPN address families
- Configures route reflector clients on spine devices
- Uses update-source Loopback0 for iBGP sessions

## Example Inventory

```yaml
sonic_devices:
  hosts:
    spine1:
      ansible_host: 172.20.20.10
      ansible_network_os: dellemc.sonic
      ansible_connection: httpapi
      router_id: 10.0.0.1
      asn: 65000
      bgp_role: route_reflector
      loopback_ip: 10.0.0.1/32
      bgp_neighbors:
        - peer_address: 10.0.1.1
          peer_asn: 65000
          description: "leaf1"
        - peer_address: 10.0.1.2
          peer_asn: 65000
          description: "leaf2"
    
    leaf1:
      ansible_host: 172.20.20.21
      ansible_network_os: dellemc.sonic
      ansible_connection: httpapi
      router_id: 10.0.1.1
      asn: 65000
      bgp_role: client
      loopback_ip: 10.0.1.1/32
      bgp_neighbors:
        - peer_address: 10.0.0.1
          peer_asn: 65000
          description: "spine1"
        - peer_address: 10.0.0.2
          peer_asn: 65000
          description: "spine2"
```

## Dependencies

None

## Example Playbook

```yaml
- hosts: sonic_devices
  roles:
    - sonic_bgp
```

## License

MIT

## Author Information

Production Network Testing Lab
