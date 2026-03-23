# Juniper Junos EVPN/VXLAN Role

## Overview

This role configures EVPN/VXLAN on Juniper Junos network devices using the `junipernetworks.junos` Ansible collection. It provides data-driven configuration for L2 and L3 VPN services over a VXLAN fabric.

## Requirements

- Juniper Junos device (QFX, EX, MX series with EVPN support)
- `junipernetworks.junos` Ansible collection installed
- BGP underlay already configured
- Loopback interfaces configured for VTEP source
- Junos OS version supporting EVPN/VXLAN (15.1X53 or later)

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
  
  tunnel:
    source_interface: "lo0.0"
  
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
      gateway_ip: "10.10.1.1/24"
  
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

- `junos_bgp` role (BGP must be configured first)
- `junos_interfaces` role (interfaces must be configured)

## Example Playbook

```yaml
- name: Configure EVPN/VXLAN on Junos devices
  hosts: junos_leafs
  gather_facts: no
  roles:
    - junos_interfaces
    - junos_bgp
    - junos_evpn_vxlan
```

## Features

### L2 VPN (VLAN Extension)

- VLAN to VNI mapping
- EVPN Type-2 (MAC/IP) routes
- EVPN Type-3 (IMET) routes
- Ingress replication for BUM traffic
- ARP suppression

### L3 VPN (Inter-Subnet Routing)

- VRF-aware L3 VNI
- Symmetric IRB (Integrated Routing and Bridging)
- Route redistribution
- EVPN Type-5 routes

### High Availability

- Anycast gateway (shared virtual MAC)
- ECMP for VXLAN tunnels
- Multi-homing support (ESI)

## Junos-Specific Notes

### EVPN Protocol Configuration

Junos uses a dedicated EVPN protocol configuration:

```
set protocols evpn encapsulation vxlan
set protocols evpn extended-vni-list all
set protocols evpn multicast-mode ingress-replication
```

### VXLAN Configuration

VXLAN is configured at the VLAN level:

```
set vlans tenant-a-web vlan-id 10
set vlans tenant-a-web vxlan vni 10010
set vlans tenant-a-web vxlan ingress-node-replication
```

### VTEP Source Interface

The VTEP source is configured globally:

```
set switch-options vtep-source-interface lo0.0
```

### VRF Configuration

L3 VNI uses routing instances:

```
set routing-instances tenant-a instance-type vrf
set routing-instances tenant-a route-distinguisher 10.0.0.1:20001
set routing-instances tenant-a vrf-target target:65000:20001
set routing-instances tenant-a vrf-table-label
```

### IRB Interfaces

Anycast gateway uses IRB interfaces with virtual gateway MAC:

```
set interfaces irb unit 10 family inet address 10.10.1.1/24
set interfaces irb unit 10 virtual-gateway-v4-mac 00:00:5e:00:01:01
```

## Verification

After running this role, verify EVPN/VXLAN configuration:

```bash
# Check EVPN database
show evpn database

# Check EVPN instance
show evpn instance

# Check VXLAN tunnels
show ethernet-switching vxlan-tunnel-end-point remote

# Check MAC addresses learned via EVPN
show ethernet-switching table

# Check EVPN routes
show route table bgp.evpn.0

# Check VRF routing tables
show route table tenant-a.inet.0

# Check IRB interfaces
show interfaces irb terse
```

## Troubleshooting

### VXLAN Tunnels Not Established

- Verify underlay routing (BGP/OSPF)
- Check loopback reachability: `ping <remote-vtep-ip> source <local-vtep-ip>`
- Verify VTEP source interface: `show switch-options`

### EVPN Routes Not Advertised

- Check BGP EVPN address family: `show bgp summary`
- Verify BGP neighbor relationships: `show bgp neighbor`
- Check EVPN protocol status: `show evpn instance`

### MAC Learning Issues

- Verify VLAN to VNI mappings: `show vlans extensive`
- Check EVPN database: `show evpn database`
- Verify ingress replication: `show ethernet-switching vxlan-tunnel-end-point remote`

### IRB Gateway Issues

- Check IRB interface status: `show interfaces irb`
- Verify virtual gateway MAC: `show configuration interfaces irb`
- Check routing instance: `show route table <vrf-name>.inet.0`

## Platform Support

This role has been tested on:

- QFX5100 series
- QFX10000 series
- EX9200 series (with EVPN license)

## License

MIT

## Author

Production Network Testing Lab Project
