# OpenConfig Metrics Reference

## Currently Collecting OpenConfig Metrics

### Interface Metrics ✅

All interface metrics are successfully collecting from all 6 devices.

#### Admin and Operational Status
```prometheus
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_admin_status
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status
```

**Labels**: `interface_name`, `source`, `subscription_name`, `admin_status`, `oper_status`

**Example Query**:
```promql
# Show all UP interfaces
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="UP"}

# Show all DOWN interfaces
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_admin_status{admin_status="DOWN"}
```

#### Traffic Counters
```prometheus
# Bytes
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_octets

# Packets
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_pkts
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_pkts

# Unicast
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_unicast_pkts
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_unicast_pkts

# Multicast
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_multicast_pkts
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_multicast_pkts

# Broadcast
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_broadcast_pkts
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_broadcast_pkts
```

**Example Query**:
```promql
# Interface bandwidth in bits per second
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets[5m]) * 8

# Total packets per second
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_pkts[5m])
```

#### Error Counters
```prometheus
# Errors
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_errors
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_errors

# Discards
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_discards
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_discards

# FCS Errors
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_fcs_errors

# Carrier Transitions
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_carrier_transitions
```

**Example Query**:
```promql
# Error rate
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_errors[5m])

# Discard rate
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_discards[5m])

# Flapping interfaces (carrier transitions)
increase(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_carrier_transitions[1h]) > 5
```

### LLDP Metrics ✅

LLDP neighbor information is successfully collecting.

```prometheus
# Neighbor identification
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_id
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_chassis_id
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_chassis_id_type
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_port_id
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_port_id_type

# Neighbor information
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_description
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_port_description

# Timing
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_age
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_last_update
```

**Labels**: `id`, `interface_name`, `source`, `subscription_name`, plus neighbor details as label values

**Example Query**:
```promql
# Show all LLDP neighbors
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name

# Find stale LLDP entries (age > 300 seconds)
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_age > 300
```

### BGP Metrics ⚠️

BGP OpenConfig metrics are configured but may not be collecting. This is expected as SR Linux has better support for native BGP paths.

**Configured subscription**:
```yaml
oc_bgp_neighbors:
  paths:
    - /network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state
```

**Recommendation**: Use native SR Linux BGP metrics instead:
```prometheus
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state
```

## Metric Naming Convention

### OpenConfig Metrics Pattern
```
gnmic_<subscription>_openconfig_<module>_<path>_<leaf>
```

**Example**:
```
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets
│      │                 │                                                          │
│      │                 │                                                          └─ Leaf (metric)
│      │                 └─ OpenConfig path
│      └─ Subscription name
└─ Collector prefix
```

### Native SR Linux Metrics Pattern
```
gnmic_<subscription>_srl_nokia_<module>_<path>_<leaf>
```

## Useful Grafana Queries

### Interface Bandwidth Dashboard

```promql
# Inbound bandwidth in Mbps
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets{interface_name=~"ethernet.*"}[5m]) * 8 / 1000000

# Outbound bandwidth in Mbps
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_octets{interface_name=~"ethernet.*"}[5m]) * 8 / 1000000

# Total bandwidth (in + out)
(rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets{interface_name=~"ethernet.*"}[5m]) + 
 rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_out_octets{interface_name=~"ethernet.*"}[5m])) * 8 / 1000000
```

### Interface Status Dashboard

```promql
# Count of UP interfaces per device
count by (source) (gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="UP"})

# Count of DOWN interfaces per device
count by (source) (gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="DOWN"})

# Interface status (1=UP, 0=DOWN)
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="UP"} * 1 or
gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="DOWN"} * 0
```

### Interface Errors Dashboard

```promql
# Error rate per interface
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_errors[5m])

# Discard rate per interface
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_discards[5m])

# Error percentage (errors / total packets)
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_errors[5m]) / 
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_pkts[5m]) * 100
```

### LLDP Topology Dashboard

```promql
# LLDP neighbor count per device
count by (source) (gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name)

# LLDP neighbor details (use as table)
gnmic_oc_lldp_openconfig_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name
```

## Comparison: OpenConfig vs Native SR Linux

### Interface Metrics

| Metric | OpenConfig | Native SR Linux |
|--------|-----------|-----------------|
| In Octets | ✅ `counters_in_octets` | ✅ `statistics_in_octets` |
| Out Octets | ✅ `counters_out_octets` | ✅ `statistics_out_octets` |
| In Packets | ✅ `counters_in_pkts` | ✅ `statistics_in_packets` |
| Errors | ✅ `counters_in_errors` | ✅ `statistics_in_error_packets` |
| Discards | ✅ `counters_in_discards` | ✅ `statistics_in_discarded_packets` |
| Admin Status | ✅ `state_admin_status` | ✅ `admin_state` |
| Oper Status | ✅ `state_oper_status` | ✅ `oper_state` |

**Recommendation**: Use OpenConfig for interface metrics - it's vendor-agnostic and works well.

### BGP Metrics

| Metric | OpenConfig | Native SR Linux |
|--------|-----------|-----------------|
| Session State | ⚠️ Limited | ✅ Full support |
| Prefix Counts | ⚠️ Limited | ✅ Per AFI/SAFI |
| EVPN Routes | ❌ Not available | ✅ Full support |
| Route Details | ⚠️ Limited | ✅ Full support |

**Recommendation**: Use native SR Linux for BGP metrics - much more detailed.

### LLDP Metrics

| Metric | OpenConfig | Native SR Linux |
|--------|-----------|-----------------|
| Neighbor Info | ✅ Good support | ✅ Good support |
| System Name | ✅ Available | ✅ Available |
| Port ID | ✅ Available | ✅ Available |
| Capabilities | ⚠️ Limited | ✅ Full support |

**Recommendation**: Use OpenConfig for LLDP - vendor-agnostic and sufficient.

## Metric Collection Performance

### Current Configuration

```yaml
subscriptions:
  oc_interface_stats:
    sample-interval: 10s  # Every 10 seconds
  
  oc_bgp_neighbors:
    sample-interval: 30s  # Every 30 seconds
  
  oc_lldp:
    sample-interval: 60s  # Every 60 seconds
```

### Resource Usage

- **gNMIc CPU**: <5%
- **gNMIc Memory**: ~50MB
- **Network per device**: <100KB/s
- **Prometheus storage**: ~10MB/day per device

### Metric Counts

- **Interface metrics**: ~18 metrics × ~10 interfaces × 6 devices = ~1,080 metrics
- **LLDP metrics**: ~10 metrics × ~8 neighbors × 6 devices = ~480 metrics
- **Total OpenConfig**: ~1,560 metrics

## Testing Commands

### Check Specific Metric
```bash
# Interface counters
docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
  grep "counters_in_octets" | grep "ethernet-1/49"

# LLDP neighbors
docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
  grep "lldp.*system_name"
```

### Query Prometheus
```bash
# Interface bandwidth
curl -s 'http://172.20.20.3:9090/api/v1/query?query=rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets[5m])' | jq

# Interface status
curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status' | jq
```

### Test OpenConfig Path Directly
```bash
# Get interface counters
docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interfaces/interface[name=ethernet-1/49]/state/counters"

# Get LLDP neighbors
docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/lldp/interfaces/interface[name=ethernet-1/49]/neighbors"
```

## Next Steps

### 1. Create OpenConfig Dashboards

Use the queries above to create Grafana dashboards that work across vendors.

### 2. Implement Metric Normalization

Transform OpenConfig metrics to universal names:
```promql
# Before
rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets[5m]) * 8

# After normalization
rate(network_interface_in_octets[5m]) * 8
```

See: `monitoring/METRIC-NORMALIZATION-GUIDE.md`

### 3. Add Multi-Vendor Support

When adding Arista or SONiC:
- OpenConfig interface metrics will work immediately
- OpenConfig LLDP metrics will work immediately
- May need vendor-specific subscriptions for BGP/OSPF

### 4. Set Up Alerts

```yaml
# Example alert rules
groups:
  - name: interface_alerts
    rules:
      - alert: InterfaceDown
        expr: gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_oper_status{oper_status="DOWN"} == 1
        for: 5m
        
      - alert: HighErrorRate
        expr: rate(gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_errors[5m]) > 100
        for: 5m
```

## Summary

### ✅ Working Well
- Interface counters (bytes, packets, errors)
- Interface status (admin, operational)
- LLDP neighbor information
- Real-time updates
- Low resource usage

### ⚠️ Limited Support
- BGP metrics (use native SR Linux instead)
- OSPF metrics (use native SR Linux instead)

### ✅ Ready For
- Multi-vendor deployments
- Vendor-agnostic dashboards
- Metric normalization
- Production monitoring

---

**Status**: OpenConfig metrics collecting successfully
**Devices**: 6 SR Linux (spine1, spine2, leaf1-4)
**Metrics**: ~1,560 OpenConfig metrics
**Performance**: <5% CPU, ~50MB memory
**Next**: Create dashboards or implement normalization
