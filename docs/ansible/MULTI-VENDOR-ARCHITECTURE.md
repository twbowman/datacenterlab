# Multi-Vendor Ansible Architecture

## Overview

This architecture allows a single Ansible codebase to deploy datacenter networks across multiple vendor platforms (SR Linux, Arista EOS, SONiC) by abstracting vendor-specific implementations behind common roles.

## Design Principles

1. **Vendor-Agnostic Data Model**: Common variables define the network intent (topology, IPs, BGP config)
2. **OS-Specific Implementations**: Each role dispatches to vendor-specific tasks based on `ansible_network_os`
3. **Native YANG Models**: Use each vendor's native models for full feature support
4. **Single Source of Truth**: Inventory and group_vars define the network, not the implementation

## Directory Structure

```
ansible/
├── inventory.yml                    # Multi-vendor inventory
├── group_vars/
│   ├── all.yml                     # Common topology variables
│   ├── srlinux.yml                 # SR Linux connection/module settings
│   ├── arista_eos.yml              # Arista EOS connection/module settings
│   └── sonic.yml                   # SONiC connection/module settings
├── host_vars/                      # Per-device overrides if needed
├── roles/
│   ├── interfaces/
│   │   ├── tasks/
│   │   │   ├── main.yml           # Dispatcher
│   │   │   ├── srlinux.yml        # SR Linux gNMI implementation
│   │   │   ├── arista_eos.yml     # Arista gNMI/eAPI implementation
│   │   │   └── sonic.yml          # SONiC implementation
│   │   └── templates/             # Vendor-specific templates if needed
│   ├── bgp_underlay/
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── srlinux.yml
│   │       ├── arista_eos.yml
│   │       └── sonic.yml
│   ├── evpn_overlay/
│   │   └── tasks/
│   │       ├── main.yml
│   │       ├── srlinux.yml
│   │       └── arista_eos.yml
│   └── verification/
│       └── tasks/
│           ├── main.yml
│           ├── srlinux.yml
│           └── arista_eos.yml
└── site.yml                        # Main playbook
```

## Implementation Pattern

### 1. Inventory with OS Detection

```yaml
all:
  children:
    srlinux_devices:
      vars:
        ansible_network_os: nokia.srlinux
        ansible_connection: local
        gnmi_port: 57400
      hosts:
        spine1:
          ansible_host: 172.20.20.10
          
    arista_devices:
      vars:
        ansible_network_os: arista.eos
        ansible_connection: httpapi
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
      hosts:
        spine2:
          ansible_host: 172.20.20.11
          
    sonic_devices:
      vars:
        ansible_network_os: dellemc.sonic
        ansible_connection: httpapi
      hosts:
        leaf1:
          ansible_host: 172.20.20.21
```

### 2. Role Dispatcher Pattern

Each role's `tasks/main.yml` dispatches based on OS:

```yaml
---
# roles/interfaces/tasks/main.yml
- name: Configure interfaces on SR Linux
  include_tasks: srlinux.yml
  when: ansible_network_os == 'nokia.srlinux'

- name: Configure interfaces on Arista EOS
  include_tasks: arista_eos.yml
  when: ansible_network_os == 'arista.eos'

- name: Configure interfaces on SONiC
  include_tasks: sonic.yml
  when: ansible_network_os == 'dellemc.sonic'
```

### 3. Vendor-Specific Implementation

Each vendor file uses native modules and models:

**SR Linux** (`roles/interfaces/tasks/srlinux.yml`):
```yaml
---
- name: Configure interfaces via gNMI (SR Linux native model)
  nokia.srlinux.gnmi_set:
    host: "{{ ansible_host }}"
    port: "{{ gnmi_port }}"
    username: "{{ gnmi_username }}"
    password: "{{ gnmi_password }}"
    insecure: "{{ gnmi_skip_verify }}"
    update:
      - path: "/interface[name={{ item.name }}]/subinterface[index=0]/ipv4/address[ip-prefix={{ item.ip }}]"
        val:
          ip-prefix: "{{ item.ip }}"
  loop: "{{ interfaces }}"
```

**Arista EOS** (`roles/interfaces/tasks/arista_eos.yml`):
```yaml
---
- name: Configure interfaces via gNMI (Arista native model)
  arista.eos.eos_interfaces:
    config:
      - name: "{{ item.name }}"
        description: "{{ item.description | default(omit) }}"
        enabled: true
    state: merged
  loop: "{{ interfaces }}"

- name: Configure IP addresses
  arista.eos.eos_l3_interfaces:
    config:
      - name: "{{ item.name }}"
        ipv4:
          - address: "{{ item.ip }}"
    state: merged
  loop: "{{ interfaces }}"
  when: item.ip is defined
```

### 4. Common Data Model

All vendors use the same variable structure from inventory:

```yaml
interfaces:
  - name: ethernet-1/1
    ip: 10.1.1.0/31
    description: "to-leaf1"
  - name: ethernet-1/2
    ip: 10.1.2.0/31
    description: "to-leaf2"
```

## Testing Multiple Vendors

### Mixed Vendor Topology

```
        [Arista Spine1] ---- [SR Linux Leaf1]
              |    |              |
              |    |              |
        [SONiC Spine2] ----- [Arista Leaf2]
```

### Selective Deployment

```bash
# Deploy only SR Linux devices
ansible-playbook site.yml --limit srlinux_devices

# Deploy only Arista devices
ansible-playbook site.yml --limit arista_devices

# Deploy specific device
ansible-playbook site.yml --limit spine1

# Deploy all
ansible-playbook site.yml
```

## Advantages

1. **Single Source of Truth**: Network design in one place
2. **Vendor Flexibility**: Easy to swap vendors per device
3. **Feature Parity**: Use native models for full feature access
4. **Testability**: Compare vendor implementations with same config
5. **Maintainability**: Vendor changes isolated to specific files

## Trade-offs

1. **Code Duplication**: Similar logic repeated per vendor
2. **Maintenance**: Must update multiple implementations for new features
3. **Testing Complexity**: Need to test each vendor path
4. **Naming Differences**: Must map interface names (ethernet-1/1 vs Ethernet1)

## Best Practices

1. **Interface Name Mapping**: Create filters to translate names
2. **Feature Detection**: Check capabilities before deploying
3. **Verification**: Always verify post-deployment across vendors
4. **Documentation**: Document vendor-specific quirks
5. **Version Pinning**: Lock module versions for stability

## Next Steps

1. Create interface name translation filters
2. Build vendor capability matrix
3. Implement common verification role
4. Add CI/CD testing per vendor
5. Document vendor-specific limitations
