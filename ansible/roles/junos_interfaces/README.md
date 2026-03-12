# Juniper Junos Interfaces Role

This role configures network interfaces on Juniper Junos devices using the `junipernetworks.junos` collection.

## Requirements

- Juniper Junos device (physical, VM, or cRPD container)
- `junipernetworks.junos` Ansible collection installed
- NETCONF access to the device

## Role Variables

### Required Variables

- `interfaces`: List of interface configurations
  - `name`: Interface name (will be translated to Junos format)
  - `ip`: IPv4 address with prefix (e.g., "10.1.1.0/31")
  - `description`: Interface description (optional)

### Optional Variables

- `loopback_ip`: Loopback0 IP address (for leaf devices)
- `junos_interfaces_debug`: Enable debug output (default: false)

## Interface Name Translation

The role uses the `to_junos_interface` filter to translate generic interface names to Junos format:

- `ethernet-1/1` → `ge-0/0/0`
- `ethernet-1/2` → `ge-0/0/1`
- `ethernet-1/3` → `ge-0/0/2`

## Example Inventory

```yaml
juniper_devices:
  vars:
    ansible_network_os: juniper.junos
    ansible_connection: netconf
    ansible_user: admin
    ansible_password: admin
  hosts:
    juniper-leaf1:
      ansible_host: 172.20.20.30
      router_id: 10.0.1.10
      loopback_ip: 10.0.1.10/32
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.1.1/31
          description: "to-spine1"
        - name: ethernet-1/2
          ip: 10.2.1.1/31
          description: "to-spine2"
```

## Example Playbook

```yaml
- hosts: juniper_devices
  roles:
    - junos_interfaces
```

## Dependencies

None

## License

MIT

## Author Information

Production Network Testing Lab
