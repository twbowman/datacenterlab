# Configuration Guide

This guide explains how to define topologies, structure device inventories, and configure network devices in the Production Network Testing Lab.

## Overview

The lab uses a three-layer configuration approach:

1. **Topology Definition** (Containerlab YAML) - Defines physical topology and device types
2. **Device Inventory** (Ansible YAML) - Defines device variables and configuration parameters
3. **Configuration Roles** (Ansible) - Applies vendor-specific configurations

## Topology Definition

### Topology File Structure

Topology files use Containerlab's YAML format:

```yaml
name: lab-name

topology:
  defaults:
    kind: linux  # Default for nodes without explicit kind
  
  groups:
    # Define reusable device groups
    srlinux-router:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixr-d2
  
  nodes:
    # Define individual devices
    spine1:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.10
      labels:
        vendor: nokia
        role: spine
  
  links:
    # Define connections between devices
    - endpoints: ["spine1:ethernet-1/1", "leaf1:ethernet-1/1"]

mgmt:
  network: lab-mgmt
  ipv4-subnet: 172.20.20.0/24
```

### Supported Vendors

#### SR Linux (Nokia)

```yaml
nodes:
  spine1:
    kind: nokia_srlinux
    image: ghcr.io/nokia/srlinux:latest
    type: ixr-d2  # or ixr-d3, ixr-d5
    mgmt-ipv4: 172.20.20.10
    startup-config: configs/spine1/srlinux/config.json
    labels:
      vendor: nokia
      os: srlinux
      role: spine
```

**Interface Naming**: `ethernet-1/1`, `ethernet-1/2`, etc.
**gNMI Port**: 57400
**Default Credentials**: admin / NokiaSrl1!

#### Arista cEOS

```yaml
nodes:
  spine1:
    kind: arista_ceos
    image: ceos:4.28.0F
    mgmt-ipv4: 172.20.20.10
    labels:
      vendor: arista
      os: eos
      role: spine
```

**Interface Naming**: `Ethernet1`, `Ethernet2`, etc.
**gNMI Port**: 57400
**Default Credentials**: admin / admin

#### SONiC

```yaml
nodes:
  leaf1:
    kind: sonic-vs
    image: docker-sonic-vs:latest
    mgmt-ipv4: 172.20.20.21
    labels:
      vendor: dell
      os: sonic
      role: leaf
```

**Interface Naming**: `Ethernet0`, `Ethernet1`, etc.
**gNMI Port**: 57400
**Default Credentials**: admin / YourPaSsWoRd

#### Juniper cRPD

```yaml
nodes:
  leaf1:
    kind: juniper_crpd
    image: crpd:23.2R1
    mgmt-ipv4: 172.20.20.21
    labels:
      vendor: juniper
      os: junos
      role: leaf
```

**Interface Naming**: `eth1`, `eth2`, etc.
**gNMI Port**: 57400
**Default Credentials**: root / (no password)

### Groups and Reusability

Use groups to define common settings:

```yaml
groups:
  srlinux-router:
    kind: nokia_srlinux
    image: ghcr.io/nokia/srlinux:latest
    type: ixr-d2
  
  arista-router:
    kind: arista_ceos
    image: ceos:4.28.0F

nodes:
  spine1:
    group: srlinux-router  # Inherits all group settings
    mgmt-ipv4: 172.20.20.10
  
  spine2:
    group: arista-router
    mgmt-ipv4: 172.20.20.11
```

### Links and Connections

Define point-to-point links between devices:

```yaml
links:
  # Simple link
  - endpoints: ["spine1:ethernet-1/1", "leaf1:ethernet-1/1"]
  
  # Multiple links
  - endpoints: ["spine1:ethernet-1/2", "leaf2:ethernet-1/1"]
  - endpoints: ["spine1:ethernet-1/3", "leaf3:ethernet-1/1"]
```

**Important**: Interface names must match vendor conventions:
- SR Linux: `ethernet-1/1`
- Arista: `Ethernet1`
- SONiC: `Ethernet0`
- Juniper: `eth1`

### Management Network

Configure the management network for device access:

```yaml
mgmt:
  network: lab-mgmt          # Docker network name
  ipv4-subnet: 172.20.20.0/24  # Management subnet
```

All devices get management IPs from this subnet via `mgmt-ipv4` parameter.

### Startup Configurations

Provide minimal startup configs for devices:

```yaml
nodes:
  spine1:
    kind: nokia_srlinux
    startup-config: configs/spine1/srlinux/config.json
    binds:
      - ./configs/spine1:/config
```

**Minimal Config Example** (SR Linux):
```json
{
  "system": {
    "name": {
      "host-name": "spine1"
    },
    "gnmi-server": {
      "admin-state": "enable",
      "network-instance": [
        {
          "name": "mgmt"
        }
      ]
    }
  }
}
```

## Device Inventory

### Inventory File Structure

Ansible inventory defines device variables and configuration parameters:

```yaml
all:
  children:
    spines:
      hosts:
        spine1:
          ansible_host: 172.20.20.10
          router_id: 10.0.0.1
          asn: 65000
          # ... device-specific variables
    
    leafs:
      hosts:
        leaf1:
          ansible_host: 172.20.20.21
          router_id: 10.0.1.1
          asn: 65000
          # ... device-specific variables
  
  vars:
    # Global variables for all devices
    ansible_connection: local
    ansible_user: admin
    ansible_password: NokiaSrl1!
```

### Device Variables

#### Common Variables

All devices should define:

```yaml
spine1:
  ansible_host: 172.20.20.10      # Management IP
  ansible_network_os: srlinux     # OS type for dispatcher
  router_id: 10.0.0.1             # Router ID for BGP/OSPF
  loopback_ip: 10.0.0.1/32        # Loopback interface IP
```

#### Interface Configuration

Define interfaces with IPs and descriptions:

```yaml
spine1:
  interfaces:
    - name: ethernet-1/1
      ip: 10.1.1.0/31
      description: "to leaf1"
    - name: ethernet-1/2
      ip: 10.1.2.0/31
      description: "to leaf2"
```

#### BGP Configuration

Define BGP parameters:

```yaml
spine1:
  asn: 65000
  router_id: 10.0.0.1
  bgp_role: route_reflector  # or 'client'
  cluster_id: 10.0.0.1       # For route reflectors
  bgp_neighbors:
    - peer_address: 10.0.1.1
      peer_asn: 65000
      description: "leaf1"
    - peer_address: 10.0.1.2
      peer_asn: 65000
      description: "leaf2"
```

#### OSPF Configuration

Define OSPF parameters:

```yaml
spine1:
  ospf_process_id: 1
  ospf_router_id: 10.0.0.1
  ospf_area: 0.0.0.0
  ospf_interfaces:
    - name: ethernet-1/1
      network_type: point-to-point
      cost: 100
```

#### EVPN/VXLAN Configuration

Define EVPN/VXLAN parameters for leafs:

```yaml
leaf1:
  evpn_vxlan:
    vni_range:
      start: 10000
      end: 10999
    route_distinguisher: "10.0.1.1:1"
    route_targets:
      import: ["65000:10"]
      export: ["65000:10"]
    vlans:
      - vlan_id: 10
        vni: 10010
        description: "client1"
```

### Group Variables

Use group_vars for common settings:

```yaml
# group_vars/spines.yml
---
bgp_role: route_reflector
ospf_area: 0.0.0.0

# group_vars/leafs.yml
---
bgp_role: client
ospf_area: 0.0.0.0
```

### Connection Variables

Define how Ansible connects to devices:

```yaml
all:
  vars:
    # For gNMI-based configuration
    ansible_connection: local
    ansible_network_os: srlinux
    gnmi_port: 57400
    gnmi_username: admin
    gnmi_password: NokiaSrl1!
    gnmi_skip_verify: true
```

## Configuration Deployment

### Using Ansible Playbooks

Deploy configurations using Ansible:

```bash
# macOS ARM
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Linux
ansible-playbook -i ansible/inventory.yml ansible/site.yml
```

### Configuration Stages

The main playbook (`ansible/site.yml`) configures devices in stages:

1. **Interfaces** - IP addressing and interface configuration
2. **LLDP** - Neighbor discovery
3. **OSPF** - Underlay routing
4. **BGP** - Overlay routing
5. **EVPN/VXLAN** - L2VPN fabric (optional)

### Selective Configuration

Use tags to configure specific components:

```bash
# Configure only interfaces
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags interfaces

# Configure only BGP
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags bgp

# Configure OSPF and BGP
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags ospf,bgp
```

### Vendor-Specific Configuration

The dispatcher pattern automatically routes to vendor-specific roles:

```yaml
# ansible/site.yml
- name: Configure network devices
  hosts: all
  tasks:
    - name: Configure SR Linux devices
      include_role:
        name: gnmi_{{ item }}
      loop:
        - interfaces
        - bgp
        - ospf
      when: ansible_network_os == 'srlinux'
    
    - name: Configure Arista devices
      include_role:
        name: eos_{{ item }}
      loop:
        - interfaces
        - bgp
        - ospf
      when: ansible_network_os == 'eos'
```

## Configuration Examples

### Example 1: Simple 2-Spine, 4-Leaf Topology

**Topology** (`topology-simple.yml`):
```yaml
name: simple-clos

topology:
  groups:
    srlinux-router:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixr-d2

  nodes:
    spine1:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.10
    spine2:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.11
    leaf1:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.21
    leaf2:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.22
    leaf3:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.23
    leaf4:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.24

  links:
    - endpoints: ["spine1:ethernet-1/1", "leaf1:ethernet-1/1"]
    - endpoints: ["spine1:ethernet-1/2", "leaf2:ethernet-1/1"]
    - endpoints: ["spine1:ethernet-1/3", "leaf3:ethernet-1/1"]
    - endpoints: ["spine1:ethernet-1/4", "leaf4:ethernet-1/1"]
    - endpoints: ["spine2:ethernet-1/1", "leaf1:ethernet-1/2"]
    - endpoints: ["spine2:ethernet-1/2", "leaf2:ethernet-1/2"]
    - endpoints: ["spine2:ethernet-1/3", "leaf3:ethernet-1/2"]
    - endpoints: ["spine2:ethernet-1/4", "leaf4:ethernet-1/2"]

mgmt:
  network: simple-mgmt
  ipv4-subnet: 172.20.20.0/24
```

**Inventory** (`ansible/inventory-simple.yml`):
```yaml
all:
  children:
    spines:
      hosts:
        spine1:
          ansible_host: 172.20.20.10
          router_id: 10.0.0.1
          asn: 65000
          bgp_role: route_reflector
          interfaces:
            - name: ethernet-1/1
              ip: 10.1.1.0/31
            - name: ethernet-1/2
              ip: 10.1.2.0/31
            - name: ethernet-1/3
              ip: 10.1.3.0/31
            - name: ethernet-1/4
              ip: 10.1.4.0/31
```

### Example 2: Multi-Vendor Topology

**Topology** (`topologies/topology-multi-vendor.yml`):
```yaml
name: multi-vendor

topology:
  groups:
    srlinux-router:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
    arista-router:
      kind: arista_ceos
      image: ceos:4.28.0F

  nodes:
    srl-spine1:
      group: srlinux-router
      mgmt-ipv4: 172.20.20.10
      labels:
        vendor: nokia
        os: srlinux
    
    arista-leaf1:
      group: arista-router
      mgmt-ipv4: 172.20.20.21
      labels:
        vendor: arista
        os: eos

  links:
    - endpoints: ["srl-spine1:ethernet-1/1", "arista-leaf1:Ethernet1"]
```

**Inventory** (`ansible/inventory-multi-vendor.yml`):
```yaml
all:
  children:
    spines:
      hosts:
        srl-spine1:
          ansible_host: 172.20.20.10
          ansible_network_os: srlinux
          router_id: 10.0.0.1
    
    leafs:
      hosts:
        arista-leaf1:
          ansible_host: 172.20.20.21
          ansible_network_os: eos
          router_id: 10.0.1.1
```

### Example 3: EVPN/VXLAN Fabric

**Inventory** (`ansible/inventory-evpn.yml`):
```yaml
all:
  children:
    leafs:
      hosts:
        leaf1:
          ansible_host: 172.20.20.21
          router_id: 10.0.1.1
          asn: 65000
          evpn_vxlan:
            vni_range:
              start: 10000
              end: 10999
            route_distinguisher: "10.0.1.1:1"
            route_targets:
              import: ["65000:10", "65000:20"]
              export: ["65000:10", "65000:20"]
            vlans:
              - vlan_id: 10
                vni: 10010
                description: "tenant1"
              - vlan_id: 20
                vni: 10020
                description: "tenant2"
```

## Verification

### Verify Topology Deployment

```bash
# Check all containers are running
docker ps --filter "name=clab-"

# Verify device reachability
ping -c 3 172.20.20.10
```

### Verify Configuration

```bash
# Run verification playbook
ansible-playbook -i ansible/inventory.yml ansible/playbooks/verify.yml

# Check specific device
docker exec clab-lab-name-spine1 sr_cli "show network-instance default protocols bgp neighbor"
```

### Common Verification Commands

**SR Linux**:
```bash
# BGP neighbors
docker exec clab-lab-name-spine1 sr_cli "show network-instance default protocols bgp neighbor"

# OSPF neighbors
docker exec clab-lab-name-spine1 sr_cli "show network-instance default protocols ospf neighbor"

# Interfaces
docker exec clab-lab-name-spine1 sr_cli "show interface brief"

# LLDP neighbors
docker exec clab-lab-name-spine1 sr_cli "show system lldp neighbor"
```

**Arista cEOS**:
```bash
# BGP neighbors
docker exec clab-lab-name-spine1 Cli -c "show ip bgp summary"

# OSPF neighbors
docker exec clab-lab-name-spine1 Cli -c "show ip ospf neighbor"

# Interfaces
docker exec clab-lab-name-spine1 Cli -c "show ip interface brief"
```

## Best Practices

### Topology Design

1. **Use Groups**: Define common settings in groups for reusability
2. **Label Devices**: Add vendor, os, and role labels for monitoring
3. **Management IPs**: Use consistent IP addressing scheme (e.g., .10-.19 for spines, .20-.29 for leafs)
4. **Startup Configs**: Keep minimal - only hostname and gNMI/SSH access

### Inventory Structure

1. **Group by Role**: Separate spines, leafs, borders, etc.
2. **Use group_vars**: Common settings in group_vars files
3. **Document Variables**: Add comments explaining non-obvious variables
4. **Version Control**: Keep inventory in git for change tracking

### Configuration Management

1. **Test in Lab First**: Always test configurations in lab before production
2. **Use Tags**: Deploy incrementally with tags during development
3. **Verify After Changes**: Run verification playbooks after configuration
4. **Idempotency**: Ensure configurations can be reapplied safely

### Multi-Vendor Considerations

1. **Interface Names**: Use vendor-specific interface naming in topology
2. **OS Detection**: Set `ansible_network_os` in inventory for dispatcher
3. **Feature Parity**: Not all features available on all vendors
4. **Test Interoperability**: Verify BGP/OSPF between different vendors

## Troubleshooting

### Topology Deployment Issues

**Problem**: Devices fail to start

**Solution**: Check container logs
```bash
docker logs clab-lab-name-spine1
```

**Problem**: Invalid topology definition

**Solution**: Validate topology before deployment
```bash
python3 scripts/validate-topology.py topology.yml
```

### Configuration Issues

**Problem**: Ansible cannot connect to device

**Solution**: Verify gNMI is enabled and reachable
```bash
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities
```

**Problem**: Configuration fails with syntax error

**Solution**: Check device logs and Ansible verbose output
```bash
ansible-playbook -i ansible/inventory.yml ansible/site.yml -vvv
```

### Interface Naming Issues

**Problem**: Links don't come up

**Solution**: Verify interface names match vendor conventions
- SR Linux: `ethernet-1/1`
- Arista: `Ethernet1`
- SONiC: `Ethernet0`
- Juniper: `eth1`

## Next Steps

- **Monitoring Guide**: Learn how to collect telemetry and visualize metrics
- **Troubleshooting Guide**: Detailed troubleshooting procedures
- **Example Topologies**: Pre-built topology examples in `topologies/examples/`
