# SONiC EVPN/VXLAN Role

## Overview

This role configures EVPN/VXLAN on SONiC network devices using the `dellemc.enterprise_sonic` Ansible collection. It provides data-driven configuration for L2 and L3 VPN services over a VXLAN fabric.

## Requirements

- SONiC network device (Dell Enterprise SONiC)
- `dellemc.enterprise_sonic` Ansible collection installed
- BGP underlay already configured
- Loopback interfaces configured for VTEP source

## Role Variables

All configuration is driven by the `evpn_vxlan` variable structure defined in `group_vars/leafs.yml`. See that file for complete documentation.

### Key Variables

```yaml
evpn_vxlan:
  enabled: true
  
  bgp_evpn:
    enabled: true
    advertise_all_vni: true
    advertise_default_gw: true
  
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
  
  l3vni:
    - vrf_name: "tenant-a"
      vni: 20001
      vlan_id: 3001
  
  anycast_gateway:
    enabled: true
    virtual_mac: "00:00:5e:00:01:01"
  
  arp_suppression:
    enabled: true
```

### Required Host Variables

```yaml
asn: 65000
router_id: "10.0.0.1"
bgp_neighbors:
  - peer_address: "10.0.0.11"
    peer_asn: 65000
```

## Dependencies

- `sonic_bgp` role (BGP must be configured first)
- `sonic_interfaces` role (interfaces must be configured)

## Example Playbook

```yaml
- name: Configure EVPN/VXLAN on SONiC devices
  hosts: sonic_leafs
  gather_facts: no
  roles:
    - sonic_interfaces
    - sonic_bgp
    - sonic_evpn_vxlan
```

## Features

### L2 VPN (VLAN Extension)

- VLAN to VNI mapping
- EVPN Type-2 (MAC/IP) routes
- EVPN Type-3 (IMET) routes
- ARP suppression

### L3 VPN (Inter-Subnet Routing)

- VRF-aware L3 VNI
- Symmetric IRB
- Route redistribution
- EVPN Type-5 routes

### High Availability

- Anycast gateway (shared virtual MAC)
- ECMP for VXLAN tunnels

## SONiC-Specific Notes

### VXLAN Interface

SONiC uses a single VTEP interface (`vtep1`) with multiple VNI mappings:

```yaml
sonic_vxlans:
  - name: vtep1
    source_ip: "{{ router_id }}"
    evpn_nvo: nvo1
    vlan_map:
      - vlan: 10
        vni: 10010
```

### BGP EVPN Configuration

EVPN is configured as an address family in BGP:

```yaml
sonic_bgp_af:
  - bgp_as: 65000
    address_family:
      afis:
        - afi: l2vpn
          safi: evpn
          advertise_all_vni: true
```

### VRF Configuration

L3 VNI requires VRF creation and BGP configuration per VRF:

```yaml
sonic_vrfs:
  - name: "tenant-a"

sonic_bgp:
  - bgp_as: 65000
    vrf_name: "tenant-a"
    router_id: "10.0.0.1"
```

## Verification

After running this role, verify EVPN/VXLAN configuration:

```bash
# Check VXLAN tunnels
show vxlan tunnel

# Check EVPN routes
show bgp l2vpn evpn

# Check VNI status
show vxlan vni

# Check MAC addresses learned via EVPN
show mac address-table

# Check VRF configuration
show vrf
```

## Troubleshooting

### VXLAN Tunnels Not Established

- Verify underlay routing (BGP/OSPF)
- Check loopback reachability
- Verify VTEP source IP configuration

### EVPN Routes Not Advertised

- Check BGP EVPN address family activation
- Verify BGP neighbor relationships
- Check VNI configuration

### MAC Learning Issues

- Verify ARP suppression settings
- Check VLAN to VNI mappings
- Verify EVPN Type-2 route advertisement

## License

MIT

## Author

Production Network Testing Lab Project
