# SONiC Interfaces Role

Configures network interfaces on SONiC devices using the dellemc.enterprise_sonic collection.

## Requirements

- dellemc.enterprise_sonic collection
- SONiC device with REST API enabled
- Ansible connection: httpapi

## Role Variables

### Required Variables

- `interfaces`: List of interface configurations
  - `name`: Interface name (will be translated via to_sonic_interface filter)
  - `ip`: IP address with prefix (e.g., "10.1.1.0/31")
  - `description`: Interface description (optional)

### Optional Variables

- `loopback_ip`: Loopback0 IP address with prefix (for leaf devices)
- `sonic_interfaces_debug`: Enable debug output (default: false)

## Example Inventory

```yaml
sonic_devices:
  hosts:
    leaf3:
      ansible_host: 172.20.20.23
      ansible_network_os: dellemc.sonic
      ansible_connection: httpapi
      router_id: 10.0.1.3
      asn: 65000
      loopback_ip: 10.0.1.3/32
      interfaces:
        - name: ethernet-1/1
          ip: 10.1.3.1/31
          description: "to-spine1"
        - name: ethernet-1/2
          ip: 10.2.3.1/31
          description: "to-spine2"
```

## Dependencies

None

## Example Playbook

```yaml
- hosts: sonic_devices
  roles:
    - sonic_interfaces
```

## Interface Name Translation

The role uses the `to_sonic_interface` filter to translate generic interface names to SONiC format:
- `ethernet-1/1` → `Ethernet0`
- `ethernet-1/2` → `Ethernet1`

## License

MIT

## Author Information

Production Network Testing Lab
