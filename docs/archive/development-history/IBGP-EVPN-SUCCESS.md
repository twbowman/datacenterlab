# iBGP EVPN-VXLAN Configuration - SUCCESS

## Summary

Successfully converted the datacenter fabric from eBGP to iBGP with route reflectors and achieved full EVPN-VXLAN connectivity between all clients.

## What Was Done

### 1. Updated Ansible Inventory
- Changed all devices to use AS 65000 (iBGP)
- Added `loopback_ip` for all devices (spines and leafs)
- Replaced interface-based neighbor configuration with `bgp_neighbors` list using loopback IPs
- Spines peer with leaf loopbacks: 10.0.1.1, 10.0.1.2, 10.0.1.3, 10.0.1.4
- Leafs peer with spine loopbacks: 10.0.0.1, 10.0.0.2

### 2. Updated BGP Role
- Added task to configure system0 loopback interfaces on all devices
- Modified BGP neighbor configuration to use `bgp_neighbors` list instead of interface-based neighbors
- BGP now peers using loopback IPs (required for iBGP)
- Route reflector configuration updated to use new neighbor structure

### 3. Updated OSPF Role
- Changed loopback OSPF configuration to apply to all devices (not just leafs)
- Spines now advertise their loopbacks via OSPF
- This provides reachability for iBGP next-hops

### 4. Deployed Configuration
- Ran `site.yml` playbook to configure interfaces, LLDP, OSPF, and BGP
- Ran `configure-evpn.yml` playbook to configure EVPN-VXLAN overlay
- All tasks completed successfully

### 5. Reconfigured Clients
- Changed all clients to use the same subnet (10.10.100.0/24)
- client1: 10.10.100.1/24
- client2: 10.10.100.2/24
- client3: 10.10.100.3/24
- client4: 10.10.100.4/24

## Current Status - ALL WORKING ✅

### OSPF Underlay ✅
- All OSPF neighbors in "full" state
- All loopbacks advertised and reachable
- Provides next-hop reachability for BGP

### iBGP Sessions ✅
- All BGP sessions established
- Leafs peer with both spines using loopback IPs
- Spines act as route reflectors

### EVPN Route Exchange ✅
- EVPN routes being advertised from leafs
- Route reflectors receiving and reflecting routes
- All leafs receiving EVPN routes from all other leafs

### VXLAN Tunnels ✅
- VXLAN tunnels established between all leafs
- VNI 100 operational
- VTEP source IPs configured correctly

### MAC Learning ✅
- Local MACs learned from connected clients
- Remote MACs learned via EVPN
- MAC table populated correctly on all leafs

### Client Connectivity ✅
- All clients can ping each other
- Layer 2 connectivity across the fabric
- EVPN-VXLAN overlay fully operational

## Verification Commands

### Check BGP Sessions
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor"
```

### Check EVPN Routes
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp routes evpn route-type summary"
```

### Check MAC Table
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance mac-vrf-100 bridge-table mac-table all"
```

### Test Client Connectivity
```bash
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 3 10.10.100.2
```

## Key Technical Insights

### Why iBGP Was Required
1. **EVPN Standard Practice**: EVPN is typically deployed with iBGP, not eBGP
2. **Route Reflection**: Allows spines to reflect EVPN routes between leafs without full mesh
3. **Simplified AS Design**: All devices in same AS simplifies policy and troubleshooting

### Why Loopback Peering Was Required
1. **iBGP Best Practice**: iBGP should peer using loopback IPs, not interface IPs
2. **Path Independence**: BGP session survives if one physical link fails (ECMP)
3. **Next-Hop Stability**: Loopback IPs provide stable next-hops for EVPN routes

### Why OSPF Was Required
1. **Underlay Routing**: Provides reachability between loopback IPs
2. **BGP Next-Hop Resolution**: BGP needs IGP to resolve next-hops
3. **Fast Convergence**: OSPF provides sub-second convergence for link failures

## Architecture

```
Topology:
                    spine1 (10.0.0.1)    spine2 (10.0.0.2)
                         |     |              |     |
                         |     +------+-------+     |
                         |            |             |
                    +----+----+  +----+----+  +-----+---+
                    |         |  |         |  |         |
                leaf1       leaf2       leaf3       leaf4
             (10.0.1.1)  (10.0.1.2)  (10.0.1.3)  (10.0.1.4)
                  |           |           |           |
              client1     client2     client3     client4
           (10.10.100.1)(10.10.100.2)(10.10.100.3)(10.10.100.4)

Underlay: OSPF (point-to-point /31 links + loopbacks)
Overlay: iBGP with EVPN (AS 65000, spines as route reflectors)
L2 Overlay: VXLAN (VNI 100, MAC-VRF)
```

## Files Modified

- `ansible/inventory.yml` - Updated for iBGP with loopback peering
- `ansible/methods/srlinux_gnmi/roles/gnmi_bgp/tasks/main.yml` - Added loopback config, updated for iBGP
- `ansible/methods/srlinux_gnmi/roles/gnmi_ospf/tasks/main.yml` - Updated to configure loopbacks on all devices
- `ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml` - Fixed role path

## Next Steps (Optional)

1. **Add Layer 3 Gateway**: Configure IRB interfaces for inter-subnet routing
2. **Add More VLANs**: Create additional MAC-VRFs for different tenant networks
3. **Add BFD**: Enable BFD for faster failure detection
4. **Add BGP Authentication**: Secure BGP sessions with MD5 authentication
5. **Monitor with Telemetry**: Verify gNMI telemetry is collecting EVPN metrics

## Conclusion

The datacenter fabric is now fully operational with:
- iBGP underlay using OSPF for reachability
- EVPN-VXLAN overlay providing Layer 2 connectivity
- Route reflectors on spines for scalable EVPN route distribution
- Full client connectivity across the fabric

All configuration is managed via Ansible and can be redeployed on a fresh lab with:
```bash
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/site.yml
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml
```
