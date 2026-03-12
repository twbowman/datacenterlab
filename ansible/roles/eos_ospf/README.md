# Arista EOS OSPF Role

This role configures OSPF on Arista EOS devices using the `arista.eos` collection, designed for datacenter underlay routing.

## Requirements

- Ansible 2.9 or higher
- `arista.eos` collection installed (`ansible-galaxy collection install arista.eos`)
- Network connectivity to Arista EOS devices

## Role Variables

### Required Variables

- `router_id`: OSPF router ID (typically loopback IP)
- `interfaces`: List of interface configurations
  - `name`: Interface name (will be translated to Arista format)
  - `ip`: IP address in CIDR notation

### Optional Variables

- `loopback_ip`: Loopback IP address (for leaf devices, configured as passive)
- `eos_ospf_debug`: Enable debug output (default: false)

## Dependencies

None

## Example Playbook

```yaml
- hosts: arista_devices
  roles:
    - role: eos_ospf
      vars:
        router_id: 10.0.0.1
        loopback_ip: 10.0.0.1/32
        interfaces:
          - name: ethernet-1/1
            ip: 10.1.1.0/31
          - name: ethernet-1/2
            ip: 10.1.2.0/31
```

## Features

- OSPF process 1 configuration
- Area 0 (backbone area)
- Point-to-point network type for fabric links
- Passive loopback interface (leafs only)
- Automatic interface name translation

## Network Design

This role implements OSPF for datacenter underlay:
- All interfaces in area 0.0.0.0
- Point-to-point network type for spine-leaf links
- Loopback interfaces advertised as passive
- Optimized for fast convergence

## Production Compatibility

This role is designed for direct production use. The same playbook works for:
- Lab environments (containerized Arista cEOS)
- Production environments (physical Arista switches)

Only the inventory file needs to change between environments.

## License

MIT

## Author

Network Automation Team
