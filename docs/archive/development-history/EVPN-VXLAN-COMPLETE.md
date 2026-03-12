# EVPN-VXLAN Configuration - Complete

## Status: Configured but Not Fully Operational

The Ansible playbook has been successfully updated and EVPN-VXLAN infrastructure is configured, but clients cannot yet communicate.

## ✅ What's Working

1. **Ansible Role Fixed**
   - VTEP source IP configuration now works
   - Uses SR Linux CLI via docker exec
   - Correct path: `/tunnel-interface vxlan1 vxlan-interface 100 egress source-ip use-system-ipv4-address`

2. **Configuration Applied**
   - All leafs have VXLAN tunnel interfaces
   - MAC-VRF instances created
   - Client interfaces bridged
   - BGP EVPN enabled
   - VTEP source configured to use system0 IP

3. **Client IPs Reconfigured**
   - All clients now in same subnet: 10.10.10.0/24
   - client1: 10.10.10.11
   - client2: 10.10.10.12
   - client3: 10.10.10.13
   - client4: 10.10.10.14

## ❌ What's Not Working

1. **No EVPN Routes**
   - No IMET (Inclusive Multicast Ethernet Tag) routes
   - No MAC/IP Advertisement routes
   - EVPN instance shows "originating-ip None"

2. **No Client Connectivity**
   - Clients cannot ping each other
   - ARP requests not being flooded across VXLAN

## Ansible Playbook Usage

### Deploy EVPN-VXLAN
```bash
cd ansible
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/configure-evpn.yml
```

### Verify
```bash
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/verify-evpn.yml
```

## Manual Verification Commands

### Check VTEP Configuration
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "info tunnel-interface vxlan1"
```

Expected output:
```
vxlan-interface 100 {
    type bridged
    ingress {
        vni 100
    }
    egress {
        source-ip use-system-ipv4-address
    }
}
```

### Check EVPN Instance
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1"
```

### Check EVPN Routes
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance default protocols bgp routes evpn route-type 3 summary"
```

### Test Client Connectivity
```bash
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 3 10.10.10.12
```

## Possible Issues & Next Steps

### 1. BGP EVPN Not Fully Enabled
The EVPN address family might need to be enabled on individual BGP neighbors, not just the group.

**Fix**: Add EVPN to each neighbor explicitly

### 2. Route Reflector Configuration
Spines might need to be configured as route reflectors for EVPN.

**Fix**: Configure spines as RR for EVPN AFI/SAFI

### 3. System0 Interface
The system0 interface might not be properly associated with the default network instance for VXLAN.

**Check**:
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show interface system0"
```

### 4. MAC-VRF to Default NI Association
The MAC-VRF might need explicit association with the default network instance for BGP.

### 5. EVPN Instance Restart
The EVPN instance might need to be disabled and re-enabled.

**Try**:
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli <<EOF
enter candidate
/network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1 admin-state disable
commit now
/network-instance mac-vrf-100 protocols bgp-evpn bgp-instance 1 admin-state enable
commit now
EOF
```

## Files Modified

- `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml` - Fixed VTEP configuration
  - Changed from gNMI to CLI approach
  - Correct path: `egress source-ip` (not `ingress source-ip`)
  - Uses `printf` and `docker exec -i` for reliable command execution

## Key Learning

**SR Linux VXLAN VTEP Source Configuration:**
- Path: `/tunnel-interface vxlan1 vxlan-interface 100 egress source-ip use-system-ipv4-address`
- NOT under `ingress` (that's for VNI)
- Must use system0 interface IP as VTEP source
- gNMI path not available, must use CLI

## Recommended Approach

Since gNMI doesn't support all VXLAN configuration paths, consider:

1. **Hybrid Approach**: Use gNMI for most config, CLI for VXLAN specifics
2. **Full CLI Playbook**: Create a pure CLI-based EVPN-VXLAN role
3. **SR Linux Specific Module**: Use nokia.grpc collection if available

## Related Files

- `ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/` - EVPN-VXLAN role
- `ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml` - Deployment playbook
- `ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml` - Verification playbook
- `EVPN-VXLAN-STATUS.md` - Initial status document
- `TRAFFIC-GENERATION-STATUS.md` - Traffic generation (will work after EVPN is operational)

## Next Session Tasks

1. Debug why EVPN routes aren't being generated
2. Check if route reflector configuration is needed
3. Verify BGP EVPN peering is fully established
4. Test with manual EVPN route injection if needed
5. Consider SR Linux documentation for complete EVPN-VXLAN example
