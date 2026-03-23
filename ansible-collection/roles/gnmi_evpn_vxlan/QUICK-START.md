# EVPN/VXLAN Quick Start Guide

## Prerequisites

1. Lab deployed with SR Linux devices
2. Underlay configured (interfaces, OSPF)
3. BGP configured (iBGP with route reflectors)
4. System loopback (system0) configured

## Configuration Steps

### Step 1: Configure EVPN/VXLAN

```bash
ansible-playbook -i ansible/inventory.yml \
  ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml
```

This will:
- Enable EVPN address family in BGP on all devices
- Configure route reflectors on spines
- Create VXLAN tunnels on leafs for each VNI
- Create MAC-VRF network instances for each VLAN
- Enable BGP-EVPN and BGP-VPN instances
- Enable route advertisement

### Step 2: Verify EVPN/VXLAN

```bash
ansible-playbook -i ansible/inventory.yml \
  ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml
```

This will check:
- EVPN address family is enabled
- EVPN routes are advertised
- VXLAN tunnels are established
- VNI to VLAN mappings are correct
- MAC-VRF operational status

### Step 3: Check EVPN Routes

```bash
# On any device
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp routes evpn route-type summary"
```

Expected output:
- Type 2 (MAC-IP) routes from all leafs
- Type 3 (Inclusive Multicast) routes from all leafs

### Step 4: Check VXLAN Tunnels

```bash
# On leaf devices
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show tunnel-interface vxlan1 vxlan-interface * detail"
```

Expected output:
- VXLAN interfaces for each VNI
- VTEP source IP (system0 loopback)
- Operational status: up

### Step 5: Check MAC Tables

```bash
# On leaf devices
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance mac-vrf-10 bridge-table mac-table all"
```

Expected output:
- Local MAC addresses (learned from access interfaces)
- Remote MAC addresses (learned via BGP EVPN)

## Data Model

### Leaf Configuration (group_vars/leafs.yml)

```yaml
evpn_vxlan:
  enabled: true
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
      description: "Tenant A Web Tier"
    # Add more mappings as needed
  bgp_evpn:
    enabled: true
    route_reflector_client: true
```

### Spine Configuration (group_vars/spines.yml)

```yaml
evpn_vxlan:
  enabled: false  # No VXLAN data plane
  bgp_evpn:
    enabled: true
    route_reflector: true
```

## Troubleshooting

### EVPN Routes Not Advertised

Check BGP EVPN status:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp neighbor"
```

Verify EVPN address family is enabled:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp afi-safi evpn"
```

### VXLAN Tunnels Not Established

Check VTEP configuration:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show tunnel vxlan-tunnel vtep"
```

Verify system0 loopback is reachable:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "ping network-instance default 10.0.1.2"
```

### MAC Addresses Not Learning

Check BGP-EVPN instance:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance mac-vrf-10 protocols bgp-evpn"
```

Check EVPN routes:
```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp routes evpn route-type 2"
```

## Common Commands

### Show All MAC-VRFs

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance * type mac-vrf"
```

### Show All VXLAN Interfaces

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show tunnel-interface vxlan1"
```

### Show EVPN Statistics

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp statistics"
```

### Show BGP EVPN Summary

```bash
docker exec clab-gnmi-clos-leaf1 sr_cli \
  "show network-instance default protocols bgp summary"
```

## Architecture

```
Control Plane (BGP EVPN)
  Spines (Route Reflectors)
    ├── Receive EVPN routes from leafs
    ├── Reflect routes to all other leafs
    └── No VXLAN data plane

  Leafs (VTEP Endpoints)
    ├── Advertise MAC-IP routes (Type 2)
    ├── Advertise IMET routes (Type 3)
    └── Learn remote MACs via BGP

Data Plane (VXLAN)
  Leaf Switch
    ├── Access Interface → MAC-VRF
    ├── MAC-VRF → VXLAN Interface
    └── VXLAN Interface → Remote VTEP
```

## Performance

Expected configuration time:
- Per device: ~10-15 seconds
- Full fabric (2 spines + 4 leafs): ~60-90 seconds

Expected verification time:
- Per device: ~5-10 seconds
- Full fabric: ~30-60 seconds

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the implementation summary in ansible/TASK-10-EVPN-VXLAN-IMPLEMENTATION.md
3. Check device logs: `docker logs clab-gnmi-clos-<device>`
4. Review Ansible output for error messages
