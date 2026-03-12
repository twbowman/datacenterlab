## EVPN-VXLAN Configuration Status

## Summary

EVPN-VXLAN overlay has been partially configured. The basic infrastructure is in place, but VTEP (VXLAN Tunnel Endpoint) source configuration needs completion.

## What's Been Configured

### ✅ Completed

1. **VXLAN Tunnel Interfaces** (leafs only)
   - Created `vxlan1` tunnel interface
   - Configured VNI 100 for VLAN 100
   - Type: bridged

2. **MAC-VRF Network Instance** (leafs only)
   - Created `mac-vrf-100` for Layer 2 overlay
   - Type: mac-vrf
   - Admin state: enabled

3. **VXLAN-MAC-VRF Association** (leafs only)
   - Associated vxlan1.100 with mac-vrf-100

4. **Client-Facing Interfaces** (leafs only)
   - Configured ethernet-1/3 as bridged (not routed)
   - Removed VLAN tagging
   - Associated with mac-vrf-100

5. **BGP EVPN Address Family** (all devices)
   - Enabled EVPN AFI/SAFI in BGP
   - Enabled in eBGP peer group
   - Rapid update enabled

6. **EVPN Instance** (leafs only)
   - Created BGP-EVPN instance ID 1
   - EVI: 100
   - ECMP: 2
   - Associated with vxlan1.100

### ⚠️ Incomplete

1. **VTEP Source IP Configuration**
   - System0 interface has loopback IP (10.0.1.x/32)
   - VXLAN tunnel needs to use this as source
   - Currently showing "originating-ip None"
   - No IMET routes being generated

## Current Status

### What Works
- ✅ BGP EVPN peering is established
- ✅ MAC learning on local interfaces
- ✅ MAC-VRF is operational
- ✅ Client interfaces are bridged

### What Doesn't Work
- ❌ No EVPN routes being advertised (IMET, MAC/IP)
- ❌ No VXLAN tunnels established
- ❌ Clients cannot reach each other across fabric
- ❌ VTEP source IP not configured

## Verification Commands

### Check EVPN BGP Status
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance default protocols bgp neighbor 10.1.1.0 advertised-routes evpn"
```

Expected: Should show IMET and MAC/IP routes (currently shows 0)

### Check MAC-VRF Status
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1"
```

Current output shows:
- IMET Routes: None, originating-ip None ❌
- MAC/IP Routes: None ❌

### Check MAC Table
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance mac-vrf-100 bridge-table mac-table all"
```

Shows: 1 learnt MAC (client1) ✅

### Check VXLAN Tunnel
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show tunnel-interface vxlan1 vxlan-interface 100"
```

### Test Client Connectivity
```bash
# Should work after EVPN is fully operational
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 3 10.10.2.10
```

Currently: Destination Host Unreachable ❌

## Next Steps to Complete EVPN-VXLAN

### Option 1: Use SR Linux CLI (Quick Test)
```bash
# On each leaf, configure VTEP source
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli <<EOF
enter candidate
/tunnel-interface vxlan1 vxlan-interface 100 ingress source-ip use-system-ipv4-address
commit now
EOF
```

### Option 2: Fix Ansible Role (Production)
The correct gNMI path needs to be determined. SR Linux VXLAN configuration may require:
1. Checking SR Linux YANG model for correct path
2. Using JSON payload for complex nested configuration
3. Or using SR Linux native CLI via Ansible

### Option 3: Alternative VXLAN Configuration
Some platforms require explicit VTEP configuration:
```yaml
/tunnel-interface[name=vxlan1]/source-address: 10.0.1.1
```

## Files Created

- `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/` - EVPN-VXLAN role
  - `tasks/main.yml` - Configuration tasks
  - `defaults/main.yml` - Default variables
- `ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml` - Deployment playbook
- `ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml` - Verification playbook

## Usage

### Deploy EVPN-VXLAN
```bash
cd ansible
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/configure-evpn.yml
```

### Verify Configuration
```bash
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/verify-evpn.yml
```

### Test Connectivity
```bash
# After EVPN is fully working
./generate-traffic.sh
```

## Architecture

```
Client1 (10.10.1.10)          Client2 (10.10.2.10)
       |                             |
   ethernet-1/3               ethernet-1/3
       |                             |
    [Leaf1]                       [Leaf2]
  VTEP: 10.0.1.1              VTEP: 10.0.1.2
  MAC-VRF-100                 MAC-VRF-100
  VNI: 100                    VNI: 100
       |                             |
       +-------- VXLAN Tunnel -------+
       |      (over IP fabric)       |
       |                             |
    [Spine1/Spine2]
    (EVPN Route Reflectors)
```

## EVPN-VXLAN Benefits

Once fully operational:
- ✅ Layer 2 connectivity across the fabric
- ✅ All clients in same broadcast domain
- ✅ MAC learning via BGP EVPN
- ✅ Optimal forwarding (no flooding)
- ✅ Multi-tenancy support (multiple VNIs)
- ✅ ECMP for load balancing

## Troubleshooting

### No EVPN Routes
**Symptom**: `0 advertised MAC-IP Advertisement routes`

**Cause**: VTEP source IP not configured

**Fix**: Configure VTEP source to use system0 IP

### Clients Can't Communicate
**Symptom**: `Destination Host Unreachable`

**Possible Causes**:
1. EVPN routes not being advertised
2. VXLAN tunnels not established
3. MAC addresses not learned
4. BGP EVPN not enabled

**Check**:
```bash
# Verify BGP EVPN is enabled
show network-instance default protocols bgp afi-safi evpn

# Verify EVPN instance
show network-instance mac-vrf-100 protocols bgp-evpn

# Verify MAC learning
show network-instance mac-vrf-100 bridge-table mac-table all
```

## Related Documentation

- `TRAFFIC-GENERATION-STATUS.md` - Traffic generation (will work after EVPN is complete)
- `ansible/methods/srlinux_gnmi/README.md` - SR Linux gNMI method
- `TELEMETRY-STRATEGY.md` - Overall strategy

## References

- [Nokia SR Linux EVPN-VXLAN Guide](https://documentation.nokia.com/srlinux/)
- [RFC 7432 - BGP MPLS-Based Ethernet VPN](https://datatracker.ietf.org/doc/html/rfc7432)
- [RFC 8365 - A Network Virtualization Overlay Solution Using Ethernet VPN (EVPN)](https://datatracker.ietf.org/doc/html/rfc8365)
