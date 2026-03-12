# EVPN-VXLAN Configuration Fix

## Source
[Nokia SR Linux EVPN-VXLAN Layer 2 Guide](https://documentation.nokia.com/srlinux/22-3/SR_Linux_Book_Files/EVPN-VXLAN_Guide/services-evpn-vxlan-l2.html)

## Key Finding: Missing Configuration

Based on the official Nokia documentation, the basic EVPN-VXLAN L2 configuration requires:

### 1. VXLAN Tunnel Interface (✅ Already Configured)
```
tunnel-interface vxlan1 {
    vxlan-interface 1 {
        type bridged
        ingress {
            vni 10
        }
        egress {
            source-ip use-system-ipv4-address  # ✅ We have this
        }
    }
}
```

### 2. MAC-VRF Network Instance (✅ Already Configured)
```
network-instance blue {
    type mac-vrf
    admin-state enable
    interface ethernet-1/2.1 {
    }
    vxlan-interface vxlan1.1 {
    }
    protocols {
        bgp-evpn {
            bgp-instance 1 {
                admin-state enable
                vxlan-interface vxlan1.1
                evi 10
            }
        }
        bgp-vpn {
            bgp-instance 1 {
                # Optional: rd and rt are auto-derived from evi if not configured
                route-distinguisher {
                    route-distinguisher 64490:200
                }
                route-target {
                    export-rt target:64490:200
                    import-rt target:64490:100
                }
            }
        }
    }
}
```

## ❌ Missing Component: BGP-VPN Configuration

**The documentation shows that EVPN-VXLAN requires BOTH:**
1. `bgp-evpn` configuration (✅ we have this)
2. `bgp-vpn` configuration (❌ we're missing this!)

The `bgp-vpn` section handles:
- Route distinguisher (RD) - auto-derived as `<ip-address:evi>`
- Route target (RT) - auto-derived as `<asn:evi>`
- Import/export policies

## The Fix

Add the `bgp-vpn` configuration to the MAC-VRF network instance on all leafs:

```bash
# On each leaf
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli <<EOF
enter candidate
/network-instance mac-vrf-100 protocols bgp-vpn bgp-instance 1
commit now
EOF
```

This will:
- Auto-derive RD from system0 IP and EVI (e.g., `10.0.1.1:100`)
- Auto-derive RT from ASN and EVI (e.g., `65001:100`)
- Enable proper EVPN route advertisement

## Alternative: Use gNMI

```bash
gnmic -a leaf1:57400 \
  -u admin -p NokiaSrl1! \
  --skip-verify \
  set \
  --update-path /network-instance[name=mac-vrf-100]/protocols/bgp-vpn/bgp-instance[id=1] \
  --update-value '{}'
```

## Why This Matters

From the documentation:

> "BGP-EVPN is also enabled in the same MAC-VRF with a minimum configuration of the EVI and the network-instance vxlan-interface associated with it. The BGP instance under BGP-EVPN has an encapsulation-type leaf, which is VXLAN by default."

> "If the route-distinguisher or route-target/policies are not configured, the required values are automatically derived from the configured EVI."

The `bgp-vpn` context is where the RD/RT derivation happens. Without it, EVPN routes cannot be properly advertised or imported.

## Verification After Fix

### Check BGP-VPN Configuration
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "info network-instance mac-vrf-100 protocols bgp-vpn"
```

Expected output:
```
bgp-vpn {
    bgp-instance 1 {
        route-distinguisher {
            route-distinguisher 10.0.1.1:100
        }
        route-target {
            export-rt target:65001:100
            import-rt target:65001:100
        }
    }
}
```

### Check EVPN Routes
```bash
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance default protocols bgp neighbor 10.1.1.0 advertised-routes evpn"
```

Should now show:
- IMET routes (type 3)
- MAC/IP routes (type 2)

### Test Client Connectivity
```bash
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 3 10.10.10.12
```

Should now work!

## Update Ansible Role

The `gnmi_evpn_vxlan` role needs to add this task:

```yaml
- name: Configure BGP-VPN instance in MAC-VRF
  ansible.builtin.shell: |
    gnmic -a {{ ansible_host }}:{{ gnmi_port }} \
      -u {{ gnmi_username }} \
      -p {{ gnmi_password }} \
      --skip-verify \
      set \
      --update-path /network-instance[name=mac-vrf-100]/protocols/bgp-vpn/bgp-instance[id=1] \
      --update-value '{}'
  delegate_to: localhost
  register: bgp_vpn_result
  changed_when: "'UPDATE' in bgp_vpn_result.stdout"
  failed_when: bgp_vpn_result.rc != 0
  when: "'leaf' in inventory_hostname"
```

## Summary

The issue is that we configured `bgp-evpn` but forgot the companion `bgp-vpn` configuration. Both are required for EVPN-VXLAN to work properly. The `bgp-vpn` context handles the RD/RT derivation that enables proper route advertisement and import.

This is a simple one-line fix that should immediately enable EVPN route advertisement and client connectivity.
