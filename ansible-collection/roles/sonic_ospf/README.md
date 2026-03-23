# SONiC OSPF Role

Configures OSPF routing protocol on SONiC devices using the dellemc.enterprise_sonic collection.

## Requirements

- dellemc.enterprise_sonic collection
- SONiC device with REST API enabled
- Ansible connection: httpapi

## Role Variables

### Required Variables

- `router_id`: OSPF router ID (IPv4 address format)
- `interfaces`: List of interface configurations
  - `name`: Interface name (will be translated via to_sonic_interface filter)
  - `ip`: IP address with prefix (required for OSPF to be enabled on interface)

### Optional Variables

- `loopback_ip`: Loopback0 IP address (for leaf devices, will be configured as passive OSPF interface)
- `sonic_ospf_debug`: Enable debug output (default: false)

## Features

- Configures OSPF process with router ID
- Enables OSPF on all physical interfaces with IP addresses
- Configures point-to-point network type on physical interfaces
- Configures loopback as passive OSPF interface (leafs only)
- Uses OSPF area 0.0.0.0 (backbone area)

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
      loopback_ip: 10.0.0.1/32
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.1.0/31
          description: "to-leaf1"
        - name: ethernet-1/2
          ip: 10.1.2.0/31
          description: "to-leaf2"
    
    leaf1:
      ansible_host: 172.20.20.21
      ansible_network_os: dellemc.sonic
      ansible_connection: httpapi
      router_id: 10.0.1.1
      asn: 65000
      loopback_ip: 10.0.1.1/32
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.1.1/31
          description: "to-spine1"
```

## Dependencies

None

## Example Playbook

```yaml
- hosts: sonic_devices
  roles:
    - sonic_ospf
```

## License

MIT

## Author Information

Production Network Testing Lab
