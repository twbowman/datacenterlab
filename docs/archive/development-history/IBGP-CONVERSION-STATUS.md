# iBGP Conversion Status

## What Was Done

### 1. Updated Inventory (✅ Complete)
- Changed all devices to AS 65000
- Added `bgp_role` parameter (route_reflector for spines, client for leafs)
- Added `cluster_id` for spines
- Added `neighbor_router_id` for all neighbors

### 2. Updated Ansible Roles (✅ Complete)
- Modified `gnmi_bgp` role to support iBGP with route reflectors
- Changed BGP group from "ebgp" to "ibgp"
- Added route reflector configuration task for spines
- Updated `gnmi_evpn_vxlan` role to use "ibgp" group

### 3. Ran Ansible Playbooks (✅ Complete)
- Ran `site.yml` to configure interfaces, LLDP, OSPF, and BGP
- Ran `configure-evpn.yml` to configure EVPN-VXLAN

### 4. Configuration Applied (✅ Complete)
- All devices now in AS 65000
- iBGP group created with EVPN and IPv4-unicast AFI/SAFI
- Route reflectors configured on spines with cluster-ids
- EVPN route advertisement enabled on leafs
- BGP-VPN configured on leafs

## Current Status

### What's Working ✅
1. OSPF underlay is operational (all neighbors in "full" state)
2. All interfaces configured correctly
3. LLDP operational
4. iBGP configuration applied to all devices
5. Route reflectors configured on spines
6. EVPN-VXLAN infrastructure configured on leafs

### What's NOT Working ❌
1. **iBGP sessions are NOT establishing**
   - All sessions stuck in "active" state
   - Last event: error
   - Last state: opensent
   - TCP connections exist but BGP OPEN exchange fails

2. **No EVPN routes can be exchanged** (because BGP is down)

3. **Clients cannot communicate** (because EVPN is not working)

## Problem Analysis

### BGP Session State
```
State: active
Last-state: opensent
Last-event: error
TCP connection: EXISTS (10.1.1.0:179 -> 10.1.1.1:38933)
```

This indicates:
- TCP connection is established
- BGP OPEN message exchange is failing
- Possible causes:
  1. AS number mismatch (ruled out - both sides are AS 65000)
  2. Router-ID conflict
  3. Capability negotiation failure
  4. BGP identifier issue

### Possible Root Causes

#### 1. Missing Loopback Interfaces on Spines
Spines don't have system0 (loopback) interfaces configured. While not strictly required for iBGP using interface IPs, this might cause issues with:
- Router-ID selection
- BGP identifier
- EVPN next-hop resolution

#### 2. Router-ID Conflict
Need to verify that all devices have unique router-IDs.

#### 3. BGP Group Configuration Issue
The ibgp group might be missing some required configuration for iBGP to work properly.

#### 4. SR Linux iBGP Requirements
SR Linux might have specific requirements for iBGP that we're missing.

## Verification Commands

### Check BGP Configuration
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "info network-instance default protocols bgp"
```

### Check BGP Neighbor Detail
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor 10.1.1.0 detail"
```

### Check Router-IDs
```bash
for device in spine1 spine2 leaf1 leaf2 leaf3 leaf4; do
    echo "$device:"
    orb -m clab docker exec clab-gnmi-clos-$device sr_cli "info network-instance default protocols bgp router-id"
done
```

### Check TCP Connections
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 netstat -an | grep :179
```

## Next Steps to Try

### 1. Add Loopback Interfaces to Spines
Configure system0 interfaces on spines with IPs from 10.0.0.x range.

### 2. Verify Router-IDs
Ensure all devices have unique router-IDs configured.

### 3. Check BGP Logs
Look for error messages in BGP logs that might indicate the problem.

### 4. Try Simpler iBGP Configuration
Remove route reflector configuration temporarily and try basic iBGP.

### 5. Check SR Linux Documentation
Verify if there are specific iBGP configuration requirements for SR Linux.

### 6. Consider Using eBGP with AS-Override
If iBGP continues to fail, consider using eBGP with AS-override or other mechanisms.

## Files Modified

- `ansible/inventory.yml` - Updated to AS 65000, added bgp_role and cluster_id
- `ansible/methods/srlinux_gnmi/roles/gnmi_bgp/tasks/main.yml` - Updated for iBGP with RR
- `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml` - Updated to use ibgp group
- `ansible/methods/srlinux_gnmi/playbooks/configure-bgp.yml` - Fixed role name
- `convert-to-ibgp.sh` - Script to convert running config (partially successful)

## Summary

We successfully converted the configuration from eBGP to iBGP with route reflectors. All Ansible playbooks run successfully and the configuration is applied. However, iBGP sessions are failing to establish due to an error during the BGP OPEN message exchange. The root cause is still under investigation but likely related to router-ID configuration or missing loopback interfaces on spines.

The EVPN issue cannot be resolved until iBGP sessions are established.
