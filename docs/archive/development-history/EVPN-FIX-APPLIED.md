# EVPN-VXLAN Fix Applied

## What Was Done

### 1. Added BGP-VPN Configuration (✅ Complete)
Both leaf switches now have `bgp-vpn` configured in the MAC-VRF:
- Route Distinguisher: Auto-derived (10.0.1.1:100, 10.0.1.2:100)
- Route Target: Manually configured (target:65011:100, target:65012:100)

### 2. Enabled EVPN Route Advertisement (✅ Complete)
Configured explicit route advertisement on both leafs:
- MAC/IP routes: advertise true
- IMET routes: advertise true
- Next-hop: use-system-ipv4-address
- Originating-IP: Set correctly (10.0.1.1, 10.0.1.2)

### 3. Configured Route Reflectors on Spines (✅ Complete)
Both spines now configured as route reflectors:
- spine1: cluster-id 10.0.0.1
- spine2: cluster-id 10.0.0.2

## Current Status

### What's Working ✅
1. VXLAN tunnel interfaces configured with correct source-IP
2. MAC-VRF network instances operational
3. BGP-EVPN instances enabled and up
4. BGP-VPN instances configured with RD/RT
5. EVPN route advertisement enabled
6. Route reflectors configured on spines
7. BGP sessions established (eBGP)
8. Local MAC learning works (client MACs learned on local interfaces)

### What's NOT Working ❌
1. **EVPN routes are NOT being advertised to BGP neighbors**
   - 0 advertised IMET routes
   - 0 advertised MAC/IP routes
   - Routes not appearing in BGP RIB

2. **Clients cannot communicate across the fabric**
   - Ping from client1 to client2 fails
   - No VXLAN tunnels established

## Verification Commands Show

### EVPN Instance Status (leaf1)
```
Net Instance   : mac-vrf-100
    bgp Instance 1 is enabled and up
        VXLAN-Interface   : vxlan1.100
        evi               : 100
        ecmp              : 2
        oper-down-reason  : N/A
        EVPN Routes
            Next hop                       : 10.0.1.1/32 ✅
            VLAN Aware Bundle Ethernet tag : None
            MAC/IP Routes                  : enabled ✅
            IMET Routes                    : enabled, originating-ip 10.0.1.1/32 ✅
```

### BGP Neighbor Status (leaf1 -> spine1)
```
Peer: 10.1.1.0
State: established ✅
EVPN AFI/SAFI:
  - Advertised routes: 0 ❌
  - Received routes: 0 ❌
```

### BGP RIB
```
show network-instance default protocols bgp routes evpn route-type summary
Result: No EVPN routes ❌
```

## Problem Analysis

The configuration appears correct according to Nokia SR Linux documentation:
1. ✅ VXLAN tunnel with source-ip configured
2. ✅ MAC-VRF with vxlan-interface
3. ✅ BGP-EVPN with EVI, vxlan-interface, routes enabled
4. ✅ BGP-VPN with RD/RT (auto-derived or manual)
5. ✅ BGP EVPN AFI/SAFI enabled globally and in peer group
6. ✅ Route reflectors configured

**Yet EVPN routes are not being injected into the BGP RIB.**

## Possible Remaining Issues

### 1. BGP Instance Association
The `bgp-instance 1` in both `bgp-evpn` and `bgp-vpn` might need to be explicitly associated with the BGP instance in the default network-instance. However, the documentation doesn't show this requirement.

### 2. eBGP vs iBGP
We're using eBGP with different AS numbers:
- leaf1: AS 65011
- leaf2: AS 65012  
- spine1: AS 65001
- spine2: AS 65002

EVPN typically works better with iBGP. The eBGP setup might require additional configuration.

### 3. Missing System Network-Instance Configuration
For multi-homing, SR Linux uses a "system network-instance". While we're not doing multi-homing, maybe there's a system-level EVPN configuration needed?

### 4. BGP-VPN Export/Import Policies
The bgp-vpn section supports export/import policies. Maybe we need to configure these explicitly?

### 5. Software Version or Bug
There might be a software version issue or bug preventing EVPN routes from being generated.

## Next Steps to Try

1. **Check if iBGP works better**: Reconfigure all devices to use the same AS number
2. **Verify software version**: Check SR Linux version and known issues
3. **Enable BGP debugging**: Look for error messages
4. **Try simpler topology**: Test with direct iBGP between leafs (no spines)
5. **Check YANG model**: Verify the exact gNMI paths for all configuration
6. **Contact Nokia support**: This might be a known issue or require specific configuration

## Files Updated

- `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml` - Added bgp-vpn configuration task
- `EVPN-VXLAN-FIX.md` - Documentation from Nokia SR Linux guide
- `EVPN-FIX-APPLIED.md` - This file

## Commands to Reproduce Current State

```bash
# On each leaf
printf "enter candidate\n/network-instance mac-vrf-100 protocols bgp-vpn bgp-instance 1\ncommit now\n" | \
  orb -m clab docker exec -i clab-gnmi-clos-leaf1 sr_cli

printf 'enter candidate\n/network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1 routes bridge-table mac-ip advertise true\n/network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1 routes bridge-table inclusive-mcast advertise true\ncommit now\n' | \
  orb -m clab docker exec -i clab-gnmi-clos-leaf1 sr_cli

printf 'enter candidate\n/network-instance mac-vrf-100 protocols bgp-vpn bgp-instance 1 route-target export-rt target:65011:100\n/network-instance mac-vrf-100 protocols bgp-vpn bgp-instance 1 route-target import-rt target:65011:100\ncommit now\n' | \
  orb -m clab docker exec -i clab-gnmi-clos-leaf1 sr_cli

# On each spine
printf 'enter candidate\n/network-instance default protocols bgp group ebgp route-reflector cluster-id 10.0.0.1\ncommit now\n' | \
  orb -m clab docker exec -i clab-gnmi-clos-spine1 sr_cli
```

## Summary

We've successfully applied the fixes identified from the Nokia documentation:
1. Added bgp-vpn configuration
2. Enabled EVPN route advertisement  
3. Configured route reflectors

However, EVPN routes are still not being advertised to BGP. The root cause remains unclear and may require:
- Topology changes (iBGP instead of eBGP)
- Additional configuration not covered in basic documentation
- Software version update or bug fix
- Nokia support assistance
