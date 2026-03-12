# Arista EOS Interfaces Role

This role configures network interfaces on Arista EOS devices using the `arista.eos` collection.

## Requirements

- Ansible 2.9 or higher
- `arista.eos` collection installed (`ansible-galaxy collection install arista.eos`)
- Network connectivity to Arista EOS devices

## Role Variables

### Required Variables

- `interfaces`: List of interface configurations
  - `name`: Interface name (will be translated to Arista format)
  - `ip`: IP address in CIDR notation (optional)
  - `description`: Interface description (optional)

### Optional Variables

- `loopback_ip`: Loopback IP address in CIDR notation (for leaf devices)
- `eos_interfaces_debug`: Enable debug output (default: false)

## Dependencies

None

## Example Playbook

```yaml
- hosts: arista_devices
  roles:
    - role: eos_interfaces
      vars:
        loopback_ip: 10.0.1.1/32
        interfaces:
          - name: ethernet-1/1
            ip: 10.1.1.0/31
            description: "to spine1"
          - name: ethernet-1/2
            ip: 10.1.2.0/31
            description: "to spine2"
```

## Interface Name Translation

The role uses the `to_arista_interface` filter to translate interface names:
- `ethernet-1/1` → `Ethernet1/1`
- `eth-1/1` → `Ethernet1/1`

## Production Compatibility

This role is designed for direct production use. The same playbook works for:
- Lab environments (containerized Arista cEOS)
- Production environments (physical Arista switches)

Only the inventory file needs to change between environments.

## License

MIT

## Author

Network Automation Team
