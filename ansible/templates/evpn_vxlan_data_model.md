# EVPN/VXLAN Vendor-Agnostic Data Model

## Overview

This document defines the vendor-agnostic data model for EVPN/VXLAN configuration.
The model is designed to be consumed by vendor-specific roles that translate it
into native configuration commands.

## Data Model Structure

The EVPN/VXLAN data model is defined in `group_vars/leafs.yml` and `group_vars/spines.yml`.

### Core Components

1. **VNI Management**: VNI ranges and VLAN-to-VNI mappings
2. **Route Distinguishers**: Auto-generated or explicit RD values
3. **Route Targets**: Import/export route target configuration
4. **VXLAN Tunnels**: Tunnel source, UDP port, TTL settings
5. **BGP EVPN**: EVPN address family configuration
6. **Anycast Gateway**: Shared gateway configuration for hosts
7. **L3 VNI**: VRF-aware VXLAN for inter-subnet routing



## Vendor-Specific Template Structure

Each vendor role should implement the following template structure:

### SR Linux Template Structure

```
roles/srlinux_evpn_vxlan/
├── tasks/
│   └── main.yml
├── templates/
│   ├── evpn_bgp.j2          # BGP EVPN address family config
│   ├── vxlan_interface.j2   # VXLAN tunnel interface config
│   ├── network_instance.j2  # L2/L3 VPN network instances
│   └── vlan_vni_map.j2      # VLAN to VNI mappings
└── defaults/
    └── main.yml
```

### Arista EOS Template Structure

```
roles/eos_evpn_vxlan/
├── tasks/
│   └── main.yml
├── templates/
│   ├── evpn_bgp.j2          # BGP EVPN configuration
│   ├── vxlan_interface.j2   # Vxlan1 interface config
│   ├── vlan_config.j2       # VLAN definitions
│   └── vrf_config.j2        # VRF configuration for L3VNI
└── defaults/
    └── main.yml
```

### SONiC Template Structure

```
roles/sonic_evpn_vxlan/
├── tasks/
│   └── main.yml
├── templates/
│   ├── evpn_bgp.j2          # BGP EVPN configuration
│   ├── vxlan_config.j2      # VXLAN tunnel configuration
│   └── vlan_vni_map.j2      # VLAN to VNI mappings
└── defaults/
    └── main.yml
```

### Juniper Template Structure

```
roles/junos_evpn_vxlan/
├── tasks/
│   └── main.yml
├── templates/
│   ├── evpn_bgp.j2          # BGP EVPN configuration
│   ├── vxlan_config.j2      # VXLAN configuration
│   └── routing_instance.j2  # Routing instance for VRFs
└── defaults/
    └── main.yml
```



## Template Variable Reference

### Common Variables (Available to All Templates)

```yaml
# From inventory
router_id: "10.0.1.1"           # Device router ID
asn: 65000                       # BGP AS number
loopback_ip: "10.0.1.1/32"      # Loopback IP address

# From group_vars/leafs.yml
evpn_vxlan:
  enabled: true
  vni:
    l2vpn_start: 10000
    l2vpn_end: 19999
    l3vpn_start: 20000
    l3vpn_end: 29999
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
  l3vni:
    - vrf_name: "tenant-a"
      vni: 20001
      vlan_id: 3001
  bgp_evpn:
    enabled: true
    advertise_all_vni: true
```

### Auto-Generated Variables

Templates can use these computed values:

```jinja2
{# Route Distinguisher: router_id:vni #}
{{ router_id }}:{{ item.vni }}

{# Route Target: asn:vni #}
{{ asn }}:{{ item.vni }}

{# VXLAN Source: loopback interface #}
{{ evpn_vxlan.tunnel.source_interface }}
```



## Configuration Mapping Examples

### L2 VNI Configuration

**Data Model:**
```yaml
vlan_vni_mappings:
  - vlan_id: 10
    vni: 10010
    name: "tenant-a-web"
```

**SR Linux Output:**
```json
{
  "network-instance": [
    {
      "name": "vxlan-10010",
      "type": "mac-vrf",
      "vxlan-interface": [{"name": "vxlan1.10010"}],
      "protocols": {
        "bgp-evpn": {
          "bgp-instance": [{"id": 1, "vxlan-interface": "vxlan1.10010"}]
        }
      }
    }
  ]
}
```

**Arista EOS Output:**
```
vlan 10
   name tenant-a-web
!
interface Vxlan1
   vxlan vlan 10 vni 10010
!
router bgp 65000
   vlan 10
      rd 10.0.1.1:10010
      route-target both 65000:10010
```

**SONiC Output:**
```json
{
  "VLAN": {
    "Vlan10": {
      "vlanid": "10",
      "vni": "10010"
    }
  }
}
```



### L3 VNI Configuration

**Data Model:**
```yaml
l3vni:
  - vrf_name: "tenant-a"
    vni: 20001
    vlan_id: 3001
    route_target:
      import: ["65000:20001"]
      export: ["65000:20001"]
```

**SR Linux Output:**
```json
{
  "network-instance": [
    {
      "name": "tenant-a",
      "type": "ip-vrf",
      "interface": [{"name": "irb1.3001"}],
      "protocols": {
        "bgp-evpn": {
          "bgp-instance": [{"id": 1, "vxlan-interface": "vxlan1.20001"}]
        }
      }
    }
  ]
}
```

**Arista EOS Output:**
```
vrf instance tenant-a
!
vlan 3001
   name L3VNI-tenant-a
!
interface Vxlan1
   vxlan vrf tenant-a vni 20001
!
router bgp 65000
   vrf tenant-a
      rd 10.0.1.1:20001
      route-target import evpn 65000:20001
      route-target export evpn 65000:20001
```



### BGP EVPN Address Family

**Data Model:**
```yaml
bgp_evpn:
  enabled: true
  advertise_all_vni: true
  route_reflector_client: true
```

**SR Linux Output:**
```json
{
  "network-instance": [
    {
      "name": "default",
      "protocols": {
        "bgp": {
          "group": [
            {
              "group-name": "evpn-overlay",
              "afi-safi": [
                {
                  "afi-safi-name": "evpn",
                  "evpn": {"advertise-ipv4-unicast": true}
                }
              ]
            }
          ]
        }
      }
    }
  ]
}
```

**Arista EOS Output:**
```
router bgp 65000
   neighbor evpn-overlay peer group
   neighbor evpn-overlay send-community extended
   !
   address-family evpn
      neighbor evpn-overlay activate
```



## Template Implementation Guidelines

### 1. Use Vendor-Agnostic Data Model

All templates should consume the same `evpn_vxlan` data structure from group_vars.

### 2. Handle Auto-Generation

Templates should support auto-generated values:
- Route Distinguisher: `{{ router_id }}:{{ vni }}`
- Route Target: `{{ asn }}:{{ vni }}`
- Cluster ID: `{{ cluster_id | default(router_id) }}`

### 3. Support Overrides

Allow per-device overrides via `evpn_vxlan_overrides` variable.

### 4. Validate Required Variables

Check for required variables and fail with clear error messages:
```yaml
- name: Validate EVPN/VXLAN configuration
  assert:
    that:
      - router_id is defined
      - asn is defined
      - evpn_vxlan.vlan_vni_mappings is defined
    fail_msg: "Missing required EVPN/VXLAN variables"
```

### 5. Idempotency

Ensure templates produce idempotent configurations that can be applied multiple times.

### 6. Documentation

Each template should include comments explaining the configuration purpose.



## Testing the Data Model

### Validation Checklist

- [ ] All required variables are defined in group_vars
- [ ] VNI ranges do not overlap between L2 and L3 VPNs
- [ ] VLAN IDs are unique across mappings
- [ ] Route targets follow consistent format
- [ ] Loopback interfaces exist for VXLAN source
- [ ] BGP EVPN address family is configured on all devices

### Example Test Playbook

```yaml
---
- name: Validate EVPN/VXLAN Data Model
  hosts: leafs
  gather_facts: no
  tasks:
    - name: Check EVPN/VXLAN is enabled
      assert:
        that:
          - evpn_vxlan.enabled | default(false)
        fail_msg: "EVPN/VXLAN not enabled for {{ inventory_hostname }}"
    
    - name: Validate VNI ranges
      assert:
        that:
          - evpn_vxlan.vni.l2vpn_start < evpn_vxlan.vni.l2vpn_end
          - evpn_vxlan.vni.l3vpn_start < evpn_vxlan.vni.l3vpn_end
          - evpn_vxlan.vni.l2vpn_end < evpn_vxlan.vni.l3vpn_start
        fail_msg: "Invalid VNI ranges"
    
    - name: Display VLAN-VNI mappings
      debug:
        msg: "VLAN {{ item.vlan_id }} -> VNI {{ item.vni }} ({{ item.name }})"
      loop: "{{ evpn_vxlan.vlan_vni_mappings }}"
```

