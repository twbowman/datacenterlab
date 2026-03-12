# SR Linux EVPN/VXLAN Role

This role configures EVPN/VXLAN overlay networks on Nokia SR Linux devices using gNMI.

## Overview

The role implements a data-driven EVPN/VXLAN fabric configuration that supports:

- Multiple VLAN-to-VNI mappings for L2 VPN services
- L3 VNI configuration for inter-subnet routing
- BGP EVPN address family configuration
- Route reflector configuration for spines
- VXLAN tunnel interfaces with VTEP source configuration
- MAC-VRF network instances for L2 services
- IP-VRF network instances for L3 services
- BGP-EVPN and BGP-VPN instance configuration
- Route advertisement for MAC-IP and inclusive multicast routes

## Requirements

- SR Linux devices with gNMI enabled
- BGP already configured (use `gnmi_bgp` role first)
- OSPF underlay for reachability (use `gnmi_ospf` role first)
- System loopback (system0) configured with IP address

## Variables

All configuration is driven by the `evpn_vxlan` variable structure defined in group_vars:

### For Leaf Switches (group_vars/leafs.yml)

```yaml
evpn_vxlan:
  enabled: true
  
  # VNI ranges
  vni:
    l2vpn_start: 10000
    l2vpn_end: 19999
    l3vpn_start: 20000
    l3vpn_end: 29999
  
  # VXLAN tunnel configuration
  tunnel:
    source_interface: "loopback0"
    udp_port: 4789
    ttl: 64
  
  # VLAN to VNI mappings (L2 VPN)
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
      description: "Tenant A Web Tier"
    - vlan_id: 20
      vni: 10020
      name: "tenant-a-app"
      description: "Tenant A Application Tier"
  
  # L3 VNI configuration (inter-subnet routing)
  l3vni:
    - vrf_name: "tenant-a"
      vni: 20001
      vlan_id: 3001
  
  # BGP EVPN configuration
  bgp_evpn:
    enabled: true
    advertise_all_vni: true
    advertise_default_gw: true
    route_reflector_client: true
```

### For Spine Switches (group_vars/spines.yml)

```yaml
evpn_vxlan:
  enabled: false  # Spines don't participate in VXLAN data plane
  
  bgp_evpn:
    enabled: true
    route_reflector: true
    cluster_id: "auto"  # Uses router_id
```

## Usage

### Basic Usage

```yaml
- hosts: all
  roles:
    - gnmi_interfaces  # Configure physical interfaces first
    - gnmi_ospf        # Configure underlay routing
    - gnmi_bgp         # Configure BGP
    - gnmi_evpn_vxlan  # Configure EVPN/VXLAN overlay
```

### Verification

Use the verification playbook to check EVPN/VXLAN status:

```bash
ansible-playbook -i ansible/inventory.yml \
  ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml
```

The verification playbook checks:
- EVPN address family is enabled in BGP
- EVPN routes are advertised (Type 2 MAC-IP, Type 3 IMET)
- VXLAN tunnels are established
- VNI to VLAN mappings are correct
- MAC-VRF operational status
- L3 VNI IP-VRF status

## Implementation Details

### Configuration Flow

1. **BGP EVPN Address Family** (All devices)
   - Enable EVPN address family in BGP
   - Enable EVPN in iBGP peer group

2. **Route Reflector** (Spines only)
   - Configure route reflector cluster ID for EVPN

3. **VXLAN Tunnels** (Leafs only)
   - Create VXLAN tunnel interfaces for each VNI
   - Configure VTEP source IP (uses system0 loopback)

4. **MAC-VRF Network Instances** (Leafs only)
   - Create MAC-VRF for each VLAN
   - Associate VXLAN interfaces with MAC-VRFs

5. **BGP-EVPN Instances** (Leafs only)
   - Configure BGP-EVPN instance in each MAC-VRF
   - Configure BGP-VPN instance for route exchange

6. **Route Advertisement** (Leafs only)
   - Enable MAC-IP route advertisement
   - Enable inclusive multicast route advertisement

7. **L3 VNI** (Leafs only, if configured)
   - Create routed VXLAN interfaces for L3 VNI
   - Create IP-VRF network instances
   - Associate L3 VNI with IP-VRF

### gNMI vs CLI

The role uses a hybrid approach:
- **gNMI**: Used for most configuration (interfaces, network instances, BGP-EVPN)
- **CLI**: Used for configurations not fully supported via gNMI (VTEP source, BGP-VPN, route advertisement)

### Idempotency

All tasks are idempotent and can be run multiple times safely:
- gNMI set operations update existing configuration
- CLI commands use `commit now` which only commits if changes exist
- Tasks use `changed_when` to accurately report changes

## Architecture

### EVPN/VXLAN Fabric Architecture

```
Spines (Route Reflectors)
  ├── BGP EVPN address family enabled
  ├── Route reflector for EVPN routes
  └── No VXLAN data plane participation

Leafs (VTEP Endpoints)
  ├── BGP EVPN address family enabled
  ├── Route reflector clients
  ├── VXLAN tunnel interface (vxlan1)
  │   ├── Multiple VNI sub-interfaces (one per VLAN)
  │   └── VTEP source: system0 loopback IP
  ├── MAC-VRF network instances (L2 VPN)
  │   ├── One per VLAN
  │   ├── Associated with VXLAN interface
  │   ├── BGP-EVPN instance for control plane
  │   └── BGP-VPN instance for route exchange
  └── IP-VRF network instances (L3 VPN)
      ├── One per tenant/VRF
      ├── Associated with L3 VNI
      └── Enables inter-subnet routing
```

### Data Flow

1. **Control Plane** (BGP EVPN)
   - Leafs advertise MAC-IP routes (Type 2) to spines
   - Leafs advertise inclusive multicast routes (Type 3) to spines
   - Spines reflect routes to all other leafs
   - Leafs learn remote MAC addresses via BGP

2. **Data Plane** (VXLAN)
   - Traffic enters leaf on access interface
   - Leaf looks up destination MAC in MAC-VRF
   - If remote, encapsulates in VXLAN and sends to remote VTEP
   - Remote leaf decapsulates and forwards to local access interface

## Troubleshooting

### Check EVPN BGP Status

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp neighbor"
```

### Check EVPN Routes

```bash
# Summary
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp routes evpn route-type summary"

# Type 2 (MAC-IP) routes
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp routes evpn route-type 2"

# Type 3 (IMET) routes
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp routes evpn route-type 3"
```

### Check VXLAN Tunnels

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show tunnel-interface vxlan1 vxlan-interface * detail"
```

### Check MAC-VRF Status

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance mac-vrf-10"
```

### Check MAC Table

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance mac-vrf-10 bridge-table mac-table all"
```

### Check VTEP Status

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show tunnel vxlan-tunnel vtep"
```

## Dependencies

- `gnmi_interfaces` role (for physical interface configuration)
- `gnmi_ospf` role (for underlay routing)
- `gnmi_bgp` role (for BGP and iBGP configuration)

## Tags

None currently defined.

## Author

Generated for production-network-testing-lab project.
