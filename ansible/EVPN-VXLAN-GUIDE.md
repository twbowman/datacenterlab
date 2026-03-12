# EVPN/VXLAN Configuration Guide

## Overview

This guide explains how to configure EVPN/VXLAN fabrics using the vendor-agnostic
data model defined in this project.

## Architecture

### EVPN/VXLAN Fabric Components

1. **Underlay Network**: IP fabric using OSPF or BGP for reachability
2. **Overlay Network**: VXLAN tunnels for L2/L3 extension
3. **Control Plane**: BGP EVPN for MAC/IP advertisement
4. **Data Plane**: VXLAN encapsulation for traffic forwarding

### Topology

```
         Spine1 (RR)          Spine2 (RR)
            |  \              /  |
            |   \            /   |
            |    \          /    |
            |     \        /     |
         Leaf1   Leaf2   Leaf3   Leaf4
          |       |       |       |
        Host1   Host2   Host3   Host4
```

- **Spines**: BGP route reflectors for EVPN control plane
- **Leafs**: VTEP (VXLAN Tunnel Endpoints) with L2/L3 VNI
- **Hosts**: Connected to leafs via access ports



## Configuration Steps

### Step 1: Define EVPN/VXLAN Variables

Edit `group_vars/leafs.yml` to define your EVPN/VXLAN configuration:

```yaml
evpn_vxlan:
  enabled: true
  vni:
    l2vpn_start: 10000
    l2vpn_end: 19999
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
```

### Step 2: Configure Underlay Network

Ensure IP reachability between all VTEPs:

```bash
ansible-playbook -i inventory.yml playbooks/configure-interfaces.yml
ansible-playbook -i inventory.yml playbooks/configure-ospf.yml
```

### Step 3: Configure BGP EVPN

Configure BGP with EVPN address family:

```bash
ansible-playbook -i inventory.yml playbooks/configure-bgp.yml
```

### Step 4: Configure EVPN/VXLAN

Apply EVPN/VXLAN configuration (to be implemented in Phase 3):

```bash
ansible-playbook -i inventory.yml playbooks/configure-evpn-vxlan.yml
```

### Step 5: Verify Configuration

Verify EVPN routes and VXLAN tunnels:

```bash
ansible-playbook -i inventory.yml playbooks/verify-evpn.yml
```



## Data Model Reference

### VLAN to VNI Mapping

Each VLAN is mapped to a unique VNI for L2 extension:

| VLAN ID | VNI   | Name           | Description              |
|---------|-------|----------------|--------------------------|
| 10      | 10010 | tenant-a-web   | Tenant A Web Tier        |
| 20      | 10020 | tenant-a-app   | Tenant A Application     |
| 30      | 10030 | tenant-a-db    | Tenant A Database        |
| 40      | 10040 | tenant-b-web   | Tenant B Web Tier        |
| 50      | 10050 | tenant-b-app   | Tenant B Application     |

### L3 VNI Configuration

L3 VNIs provide inter-subnet routing within a VRF:

| VRF Name | VNI   | VLAN ID | Route Target  |
|----------|-------|---------|---------------|
| tenant-a | 20001 | 3001    | 65000:20001   |
| tenant-b | 20002 | 3002    | 65000:20002   |

### Route Distinguisher Format

Auto-generated as: `<router_id>:<vni>`

Example: `10.0.1.1:10010`

### Route Target Format

Auto-generated as: `<asn>:<vni>`

Example: `65000:10010`



## Vendor-Specific Implementation

### SR Linux

SR Linux uses network instances for L2/L3 VPNs:

- **mac-vrf**: L2 VPN (VLAN extension)
- **ip-vrf**: L3 VPN (inter-subnet routing)

Configuration path: `/network-instance[name=*]/protocols/bgp-evpn`

### Arista EOS

Arista uses Vxlan1 interface for all VNI mappings:

```
interface Vxlan1
   vxlan source-interface Loopback0
   vxlan udp-port 4789
   vxlan vlan 10 vni 10010
   vxlan vrf tenant-a vni 20001
```

### SONiC

SONiC uses VLAN configuration with VNI attributes:

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

### Juniper

Juniper uses routing instances for VRFs:

```
routing-instances {
    tenant-a {
        instance-type vrf;
        vrf-target target:65000:20001;
    }
}
```



## Troubleshooting

### Common Issues

#### 1. EVPN Routes Not Advertised

**Symptoms**: No EVPN routes in BGP table

**Checks**:
- Verify BGP EVPN address family is configured
- Check BGP neighbor relationships are established
- Verify VNI configuration is correct

**Commands**:
```bash
# SR Linux
show network-instance default protocols bgp neighbor
show network-instance default protocols bgp-evpn bgp-instance 1 routes

# Arista EOS
show bgp evpn summary
show bgp evpn route-type mac-ip
```

#### 2. VXLAN Tunnels Not Established

**Symptoms**: No VXLAN tunnels between VTEPs

**Checks**:
- Verify underlay IP reachability (ping loopback IPs)
- Check VXLAN source interface is configured
- Verify UDP port 4789 is not blocked

**Commands**:
```bash
# SR Linux
show tunnel-interface vxlan1 vxlan-interface * detail

# Arista EOS
show vxlan vtep
show vxlan vni
```

#### 3. MAC Addresses Not Learning

**Symptoms**: Hosts cannot communicate across fabric

**Checks**:
- Verify EVPN routes include MAC addresses
- Check ARP suppression configuration
- Verify VLAN-VNI mappings are correct

**Commands**:
```bash
# SR Linux
show network-instance mac-vrf-10010 bridge-table mac-table all

# Arista EOS
show vxlan address-table
show mac address-table vlan 10
```



## Best Practices

### 1. VNI Allocation

- Use separate ranges for L2 and L3 VNIs
- Document VNI assignments
- Avoid VNI reuse across different services

### 2. Route Target Design

- Use consistent RT format across fabric
- Consider RT filtering for multi-tenant isolation
- Document RT assignments per VRF

### 3. Anycast Gateway

- Use consistent virtual MAC across all leafs
- Configure same gateway IP on all leafs for a VLAN
- Enable ARP suppression to reduce flooding

### 4. Underlay Network

- Ensure low latency between VTEPs
- Use equal-cost multipath (ECMP) for load balancing
- Monitor underlay link utilization

### 5. BGP Configuration

- Use route reflectors to reduce BGP peering complexity
- Configure BGP timers appropriately
- Enable BFD for fast failure detection

### 6. Monitoring

- Monitor EVPN route counts
- Track VXLAN tunnel status
- Alert on MAC table size limits



## Next Steps

After completing the EVPN/VXLAN data model definition:

1. **Implement SR Linux EVPN/VXLAN role** (Task 10)
   - Create `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/`
   - Implement configuration templates
   - Add verification tasks

2. **Implement Arista EVPN/VXLAN role** (Task 11)
   - Create `ansible/roles/eos_evpn_vxlan/`
   - Implement configuration templates
   - Add verification tasks

3. **Implement SONiC and Juniper roles** (Task 12)
   - Create vendor-specific roles
   - Implement configuration templates

4. **Create verification playbooks**
   - Verify EVPN routes
   - Verify VXLAN tunnels
   - Verify MAC learning

## References

- [RFC 7432: BGP MPLS-Based Ethernet VPN](https://datatracker.ietf.org/doc/html/rfc7432)
- [RFC 8365: A Network Virtualization Overlay Solution Using EVPN](https://datatracker.ietf.org/doc/html/rfc8365)
- [VXLAN RFC 7348](https://datatracker.ietf.org/doc/html/rfc7348)

