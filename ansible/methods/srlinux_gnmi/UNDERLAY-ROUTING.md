# Production Datacenter Underlay Routing Architecture

## Overview
This implementation uses the traditional enterprise/datacenter approach with separate underlay and overlay routing protocols:

- **OSPF Underlay**: Provides IP reachability and next-hop resolution
- **BGP Overlay**: Distributes application prefixes (loopbacks, VLANs, etc.)

## Why This Approach?

This is one of the most common production datacenter architectures because:

1. **Clear separation of concerns**: OSPF handles infrastructure routing, BGP handles application routing
2. **Fast convergence**: OSPF provides sub-second convergence for link failures
3. **Scalability**: BGP can carry thousands of application prefixes without impacting underlay
4. **Proven technology**: Used in enterprise datacenters for decades
5. **Troubleshooting**: Easy to separate underlay vs overlay issues

## Architecture Details

### OSPF Configuration
- All point-to-point interfaces in area 0.0.0.0
- Interface type: point-to-point (no DR/BDR election needed)
- Loopback interfaces advertised as passive
- Provides reachability for all /31 point-to-point subnets and /32 loopbacks

### BGP Configuration
- eBGP peering using /31 point-to-point interface IPs
- Each spine/leaf has unique ASN (standard eBGP fabric design)
- Export policy: Only advertise loopback addresses (10.0.0.0/16 with /32 mask)
- OSPF provides next-hop reachability, so no eBGP multihop needed
- BGP sessions peer directly on connected interfaces

### Route Flow
1. OSPF advertises all point-to-point /31 subnets and loopback /32s
2. BGP peers establish sessions using /31 interface IPs
3. BGP advertises only loopback /32 addresses
4. BGP next-hops are resolved via OSPF-learned routes
5. Result: Full IP reachability across the fabric

## Alternative Approaches

### BGP Unnumbered (Modern Hyperscale)
- Uses IPv6 link-local addresses for peering
- No IP addressing on point-to-point links
- Most common in modern hyperscale datacenters (Facebook, AWS, etc.)
- Requires IPv6 support and more complex configuration

### Pure eBGP (No IGP)
- BGP advertises both infrastructure and application routes
- Requires careful next-hop resolution (static routes or recursive lookups)
- Common in cloud-native environments
- Can have convergence issues without proper tuning

### IGP Only (No BGP)
- OSPF or ISIS carries all routes
- Simple but doesn't scale well
- No policy control or route filtering
- Not recommended for production datacenters

## Verification Commands

Check OSPF neighbors:
```bash
gnmic -a <device>:57400 -u admin -p NokiaSrl1! --skip-verify \
  get --path /network-instance[name=default]/protocols/ospf/instance[name=main]/neighbor
```

Check OSPF routes:
```bash
gnmic -a <device>:57400 -u admin -p NokiaSrl1! --skip-verify \
  get --path /network-instance[name=default]/route-table/ipv4-unicast/route
```

Check BGP sessions:
```bash
gnmic -a <device>:57400 -u admin -p NokiaSrl1! --skip-verify \
  get --path /network-instance[name=default]/protocols/bgp/neighbor
```

Check BGP routes:
```bash
gnmic -a <device>:57400 -u admin -p NokiaSrl1! --skip-verify \
  get --path /network-instance[name=default]/protocols/bgp/rib
```
