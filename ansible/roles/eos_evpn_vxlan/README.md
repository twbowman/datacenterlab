# Arista EOS EVPN/VXLAN Role

This role configures EVPN/VXLAN on Arista EOS devices using the `arista.eos` collection. It supports L2 VPN services with VLAN-to-VNI mappings and L3 VPN services with L3 VNI for inter-subnet routing.

## Requirements

- Ansible 2.9 or higher
- `arista.eos` collection installed
- Arista EOS devices with VXLAN support
- BGP already configured (use `eos_bgp` role first)

## Role Variables

### Required Variables

These variables should be defined in `group_vars/leafs.yml` or `host_vars/`:

```yaml
# BGP configuration (from eos_bgp role)
asn: 65000
router_id: "10.0.0.1"
bgp_neighbors:
  - peer_address: "10.0.0.11"
    peer_asn: 65000

# EVPN/VXLAN configuration
evpn_vxlan:
  enabled: true
  
  tunnel:
    source_interface: "Loopback0"
    udp_port: 4789
  
  vlan_vni_mappings:
    - vlan_id: 10
      vni: 10010
      name: "tenant-a-web"
    - vlan_id: 20
      vni: 10020
      name: "tenant-a-app"
  
  bgp_evpn:
    enabled: true
    route_reflector: false  # true for spines
  
  l3vni:
    - vrf_name: "tenant-a"
      vni: 20001
      vlan_id: 3001
      route_target:
        import: ["65000:20001"]
        export: ["65000:20001"]
  
  anycast_gateway:
    enabled: true
    virtual_mac: "00:00:5e:00:01:01"
```

### Optional Variables

```yaml
# Debug mode
eos_evpn_debug: false
```

## Dependencies

This role depends on:
- `eos_bgp` - BGP must be configured before EVPN/VXLAN

## Example Playbook

### Basic Usage

```yaml
- name: Configure EVPN/VXLAN on Arista devices
  hosts: leafs
  gather_facts: no
  roles:
    - role: eos_bgp
    - role: eos_evpn_vxlan
```

### With Dispatcher Pattern

```yaml
- name: Configure network devices
  hosts: all
  gather_facts: no
  tasks:
    - name: Configure EVPN/VXLAN on Arista devices
      include_role:
        name: eos_evpn_vxlan
      when: ansible_network_os == 'eos'
```

## Configuration Details

### BGP EVPN Address Family

The role configures:
- L2VPN EVPN address family in BGP
- Activates EVPN for all BGP neighbors
- Configures route reflector clients (spines only)

### VXLAN Interface

The role creates and configures:
- Vxlan1 interface
- Source interface (typically Loopback0)
- UDP port (default 4789)

### VLAN to VNI Mapping

For each VLAN-to-VNI mapping:
- Creates VLAN
- Maps VLAN to VNI
- Configures EVPN instance with route distinguisher and route targets
- Route distinguisher format: `<router_id>:<vni>`
- Route target format: `<asn>:<vni>`

### L3 VNI Configuration

For each L3 VNI:
- Creates VRF
- Creates L3 VNI VLAN
- Maps L3 VNI to VRF
- Configures BGP in VRF context
- Redistributes connected routes
- Configures EVPN route distinguisher and route targets

### Anycast Gateway

When enabled:
- Configures virtual router MAC address
- Provides first-hop redundancy for hosts

## Architecture

### Control Plane (BGP EVPN)

```
Spines (Route Reflectors)
  ├── Receive EVPN routes from leafs
  ├── Reflect routes to all other leafs
  └── No VXLAN data plane participation

Leafs (VTEP Endpoints)
  ├── Advertise MAC-IP routes (Type 2)
  ├── Advertise inclusive multicast routes (Type 3)
  ├── Learn remote MAC addresses via BGP
  └── Build VXLAN tunnels to remote VTEPs
```

### Data Plane (VXLAN)

```
Leaf Switch
  ├── Access Interface (Ethernet1)
  │   └── Receives untagged traffic
  ├── VLAN (VLAN 10)
  │   ├── MAC learning via BGP EVPN
  │   └── Forwarding decision
  └── VXLAN Interface (Vxlan1)
      ├── Encapsulates traffic with VNI 10010
      ├── Source: Loopback0 IP
      └── Destination: Remote VTEP IP
```

## Verification

### Check EVPN Address Family

```bash
show bgp evpn summary
```

### Check VXLAN Interface

```bash
show interfaces vxlan1
```

### Check VLAN to VNI Mappings

```bash
show vxlan vni
```

### Check EVPN Routes

```bash
show bgp evpn route-type mac-ip
show bgp evpn route-type imet
```

### Check MAC Address Table

```bash
show mac address-table
```

### Check VRF Configuration

```bash
show vrf
show ip route vrf <vrf_name>
```

## Idempotency

All tasks in this role are idempotent:
- Can be run multiple times without errors
- Only applies changes when configuration differs
- Uses `arista.eos` collection modules which handle idempotency

## Production Compatibility

This role is designed for direct production use:
- Same configuration works for lab (containers) and production (physical/VM)
- Only inventory changes between environments
- No lab-specific conditionals
- Production-grade error handling

## Troubleshooting

### EVPN Routes Not Advertised

1. Check BGP EVPN address family is enabled:
   ```bash
   show bgp evpn summary
   ```

2. Check VXLAN interface is up:
   ```bash
   show interfaces vxlan1
   ```

3. Check VLAN to VNI mappings:
   ```bash
   show vxlan vni
   ```

### VXLAN Tunnels Not Established

1. Check source interface (Loopback0) is reachable:
   ```bash
   ping <remote-loopback-ip> source Loopback0
   ```

2. Check BGP sessions are established:
   ```bash
   show bgp summary
   ```

3. Check EVPN routes are received:
   ```bash
   show bgp evpn route-type imet
   ```

### MAC Addresses Not Learning

1. Check EVPN MAC-IP routes:
   ```bash
   show bgp evpn route-type mac-ip
   ```

2. Check MAC address table:
   ```bash
   show mac address-table
   ```

3. Check VXLAN flood list:
   ```bash
   show vxlan flood vtep
   ```

## References

- [Arista EVPN Configuration Guide](https://www.arista.com/en/um-eos/eos-section-36-3-configuring-vxlan)
- [RFC 7432: BGP MPLS-Based Ethernet VPN](https://datatracker.ietf.org/doc/html/rfc7432)
- [RFC 8365: A Network Virtualization Overlay Solution Using EVPN](https://datatracker.ietf.org/doc/html/rfc8365)

## License

MIT

## Author Information

Production Network Testing Lab - Network Automation Team
