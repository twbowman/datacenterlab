# Traffic Generation Script Status

## Summary

The `generate-traffic.sh` script has been updated and is now functional, but with limitations due to the current network configuration.

## Issues Found

### 1. Wrong IP Addresses
**Problem**: Script used incorrect IP addresses
- Script had: `192.168.x.1`
- Actual IPs: `10.10.x.10`

**Fixed**: Updated to use correct client IPs and gateway addresses.

### 2. No Inter-Client Routing
**Problem**: Clients cannot reach each other across the fabric
- Client networks (10.10.x.0/24) are NOT advertised via BGP
- BGP only advertises:
  - Loopback addresses (10.0.x.x/32)
  - Point-to-point links (10.1.x.0/31)

**Current Behavior**: 
- ✅ Clients can reach their local gateway (leaf switch)
- ❌ Clients cannot reach other clients across spines

## Current Script Functionality

### What It Does
Generates traffic from each client to its local gateway:
- client1 (10.10.1.10) → leaf1 gateway (10.10.1.1)
- client2 (10.10.2.10) → leaf2 gateway (10.10.2.1)
- client3 (10.10.3.10) → leaf3 gateway (10.10.3.1)
- client4 (10.10.4.10) → leaf4 gateway (10.10.4.1)

### What It Generates
- Traffic on client-facing interfaces (ethernet-1/3 on leafs)
- Ping packets with 1400-byte payload
- 100 packets per second for 60 seconds
- ~1.12 Mbps per client

### What It Doesn't Do
- ❌ Generate spine-leaf traffic (clients can't reach each other)
- ❌ Test ECMP load balancing (no cross-fabric traffic)
- ❌ Create realistic datacenter traffic patterns

## Usage

```bash
# Generate traffic (runs for 60 seconds)
./generate-traffic.sh

# Or via lab script
./lab generate-traffic

# Then analyze
./lab analyze-links
```

## Expected Output

### During Execution
```
🚦 Generating test traffic between clients...
🔍 Checking client connectivity...
⚠️  WARNING: Clients cannot reach each other!
...
✅ Traffic generation started
```

### In Metrics
You should see traffic on client-facing interfaces:
- leaf1 ethernet-1/3 (client1)
- leaf2 ethernet-1/3 (client2)
- leaf3 ethernet-1/3 (client3)
- leaf4 ethernet-1/3 (client4)

But NOT on spine-facing interfaces (ethernet-1/1, ethernet-1/2).

## Enabling Full Traffic Generation

To enable client-to-client traffic across the fabric, you need to:

### Option 1: Advertise Client Networks via BGP

1. **Configure client-facing interfaces** on leafs:
```bash
# Example for leaf1
gnmic -a clab-gnmi-clos-leaf1:57400 -u admin -p 'NokiaSrl1!' --skip-verify set \
  --update-path /interface[name=ethernet-1/3]/subinterface[index=0]/ipv4/address[ip-prefix=10.10.1.1/24] \
  --update-value '{}'
```

2. **Update BGP export policy** to include client networks:
```bash
# Add policy to export connected routes
gnmic set \
  --update-path /routing-policy/policy[name=export-local]/statement[name=20]/match/protocol \
  --update-value connected \
  --update-path /routing-policy/policy[name=export-local]/statement[name=20]/action/policy-result \
  --update-value accept
```

3. **Apply to BGP**:
```bash
# Policy is already applied via export-local
```

### Option 2: Use Static Routes with Redistribution

1. Add static routes on each leaf for remote client networks
2. Redistribute static routes into BGP
3. More manual but gives fine-grained control

### Option 3: Use OSPF for Client Networks

1. Enable OSPF on client-facing interfaces
2. Redistribute OSPF into BGP
3. More complex but provides dynamic routing

## Current Lab Design

The lab is designed to demonstrate:
- ✅ OSPF underlay for infrastructure routing
- ✅ BGP overlay for loopback reachability
- ✅ Telemetry and monitoring
- ✅ Automation with Ansible

It is NOT currently configured for:
- ❌ Client-to-client traffic
- ❌ Application workload simulation
- ❌ ECMP load balancing demonstration

This is intentional to keep the lab focused on the core networking and automation concepts.

## Workaround for Testing

If you want to see traffic on spine-leaf links without configuring client routing:

### Manual Traffic Generation

```bash
# From leaf1 to spine1 (direct ping)
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "ping 10.1.1.0 count 1000 size 1400 interval 0.01"

# From leaf1 to leaf2 via loopback (uses spine)
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "ping 10.0.1.2 count 1000 size 1400 interval 0.01"
```

### Using iperf3 Between Switches

```bash
# Start iperf3 server on leaf2
orb -m clab docker exec -d clab-gnmi-clos-leaf2 \
  iperf3 -s -B 10.0.1.2

# Run iperf3 client from leaf1
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  iperf3 -c 10.0.1.2 -t 60 -b 1G
```

## Verification

### Check Client Connectivity
```bash
# From client1, try to reach client2
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 2 10.10.2.10

# Expected: 100% packet loss (no route)
```

### Check Gateway Connectivity
```bash
# From client1, reach its gateway
orb -m clab docker exec clab-gnmi-clos-client1 ping -c 2 10.10.1.1

# Expected: Success
```

### Check BGP Routes
```bash
# See what's being advertised
orb -m clab docker exec clab-gnmi-clos-leaf1 \
  sr_cli "show network-instance default protocols bgp routes ipv4 summary"

# Should see: 10.0.x.x/32 and 10.1.x.0/31
# Should NOT see: 10.10.x.0/24
```

## Related Files

- `generate-traffic.sh` - Traffic generation script
- `analyze-link-utilization.py` - Link analysis tool
- `lab` - Lab management script (includes `./lab generate-traffic`)
- `LINK-UTILIZATION-TESTING.md` - Testing documentation

## Future Enhancements

To make this a full traffic generation lab:

1. Add Ansible playbook to configure client networks
2. Update BGP export policy to include connected routes
3. Add iperf3 server mode to clients
4. Create realistic traffic patterns (north-south, east-west)
5. Add traffic shaping and QoS testing
6. Implement elephant flow detection

For now, the script serves as a basic traffic generator for interface-level metrics.
