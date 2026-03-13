# EVPN/VXLAN Configuration Role (gNMI-based)

This role configures EVPN/VXLAN overlay networking on SR Linux devices using gNMI with native SR Linux YANG paths.

## Overview

EVPN/VXLAN provides:
- Layer 2 extension across the data center fabric
- Multi-tenancy with MAC-VRF isolation
- Efficient MAC/IP learning via BGP EVPN control plane
- Scalable multi-homing and redundancy

## Architecture

- **Leafs**: Participate in VXLAN data plane, host MAC-VRFs, terminate VXLAN tunnels
- **Spines**: Act as BGP route reflectors for EVPN control plane (no VXLAN data plane)

## Configuration Method

Uses gNMI SET operations with SR Linux native paths (`srl_nokia:` origin prefix):
- VXLAN tunnel interfaces
- MAC-VRF network instances
- BGP-EVPN and BGP-VPN protocol configuration
- Client-facing bridged subinterfaces
- Optional L3 VNI for inter-subnet routing

## Prerequisites

1. Underlay routing (OSPF) must be configured and operational
2. BGP must be configured with EVPN address family enabled
3. System IPv4 address must be configured (used as VXLAN source IP)

## Variables

Defined in `group_vars/leafs.yml`:

```yaml
evpn_vxlan:
  enabled: true
  
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
      description: "Tenant A Web Tier"
  
  l3vni:  # Optional
    - vrf_name: "tenant-a"
      vni: 20001
      vlan_id: 3001
```

## Usage

```bash
# Configure EVPN/VXLAN on all leafs
ansible-playbook -i inventory.yml site.yml --tags evpn

# Configure only VXLAN tunnels
ansible-playbook -i inventory.yml site.yml --tags vxlan

# Skip EVPN configuration
ansible-playbook -i inventory.yml site.yml --skip-tags evpn
```

## Verification

```bash
# Check VXLAN tunnel interfaces
gnmic -a leaf1:57400 -u admin -p password --skip-verify get \
  --path 'srl_nokia:/tunnel-interface[name=vxlan1]' -e json_ietf

# Check MAC-VRF instances
gnmic -a leaf1:57400 -u admin -p password --skip-verify get \
  --path 'srl_nokia:/network-instance[name=mac-vrf-10]' -e json_ietf

# Check EVPN routes
gnmic -a leaf1:57400 -u admin -p password --skip-verify get \
  --path 'srl_nokia:/network-instance[name=mac-vrf-10]/protocols/srl_nokia-bgp-evpn:bgp-evpn' -e json_ietf
```

## Features

- **L2 VNI**: Bridged VXLAN interfaces for L2 extension
- **MAC-VRF**: Isolated MAC forwarding tables per tenant
- **BGP-EVPN**: Control plane for MAC/IP route distribution
- **Route Targets**: Automatic RT generation (ASN:VNI format)
- **L3 VNI**: Optional routed VXLAN for inter-subnet routing
- **Client Interfaces**: Bridged subinterfaces with VLAN tagging

## Limitations

- OpenConfig does not support EVPN/VXLAN configuration on SR Linux
- Must use SR Linux native YANG paths with `srl_nokia:` origin
- Client-facing interfaces (ethernet-1/3) must exist in device configuration
