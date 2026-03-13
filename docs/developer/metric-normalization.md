# Metric Normalization Documentation

## Overview

This document provides comprehensive documentation of all metric normalization mappings, transformation rules, and examples for each supported vendor. Metric normalization enables vendor-agnostic queries across multi-vendor network topologies.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 13.4**

## Goals

1. **Universal Queries**: Single PromQL query works across all vendors
2. **Consistent Naming**: All metrics use `network_*` prefix
3. **Preserve Values**: Metric values and timestamps unchanged
4. **Vendor Transparency**: Users don't need to know vendor-specific paths
5. **Debugging Support**: Original metrics available for troubleshooting

## Normalization Architecture

```
Device (Vendor-Specific) → gNMIc Collector → Processors → Prometheus → Grafana
                                                  ↓
                                          Normalization
                                          (vendor → universal)
```

### Two-Stage Normalization

**Stage 1: gNMIc Event Processors**
- Transform metric names
- Normalize labels
- Add vendor tags
- Translate interface names

**Stage 2: Prometheus Relabeling**
- Final metric name standardization
- Additional label normalization
- Metric filtering
- Cardinality reduction

## Universal Metric Naming Convention

### Prefix Standard

All normalized metrics use the `network_` prefix:

```
network_<component>_<metric>_<unit>

Examples:
- network_interface_in_octets
- network_interface_out_packets
- network_bgp_session_state
- network_ospf_neighbor_count
```

### Component Categories

- `interface` - Interface statistics
- `bgp` - BGP protocol metrics
- `ospf` - OSPF protocol metrics
- `lldp` - LLDP neighbor information
- `system` - System-level metrics
- `cpu` - CPU utilization
- `memory` - Memory utilization

## Universal Metrics Reference

### Interface Counter Metrics

| Universal Metric | Description | Unit | Type |
|------------------|-------------|------|------|
| `network_interface_in_octets` | Bytes received | bytes | counter |
| `network_interface_out_octets` | Bytes transmitted | bytes | counter |
| `network_interface_in_packets` | Packets received | packets | counter |
| `network_interface_out_packets` | Packets transmitted | packets | counter |
| `network_interface_in_errors` | Input errors | errors | counter |
| `network_interface_out_errors` | Output errors | errors | counter |
| `network_interface_in_discards` | Input discards | packets | counter |
| `network_interface_out_discards` | Output discards | packets | counter |

### Interface State Metrics

| Universal Metric | Description | Values | Type |
|------------------|-------------|--------|------|
| `network_interface_admin_status` | Admin state | 1=up, 0=down | gauge |
| `network_interface_oper_status` | Operational state | 1=up, 0=down | gauge |
| `network_interface_speed` | Interface speed | bits/sec | gauge |
| `network_interface_mtu` | MTU size | bytes | gauge |

### BGP Metrics

| Universal Metric | Description | Values | Type |
|------------------|-------------|--------|------|
| `network_bgp_session_state` | BGP session state | 1-6 (IDLE to ESTABLISHED) | gauge |
| `network_bgp_established_transitions` | Session flap count | count | counter |
| `network_bgp_received_routes` | Routes received from peer | count | gauge |
| `network_bgp_sent_routes` | Routes sent to peer | count | gauge |
| `network_bgp_peer_as` | Peer AS number | ASN | gauge |
| `network_bgp_last_established` | Last established timestamp | unix timestamp | gauge |

### LLDP Metrics

| Universal Metric | Description | Type |
|------------------|-------------|------|
| `network_lldp_neighbor_system_name` | Neighbor system name | info |
| `network_lldp_neighbor_port_id` | Neighbor port ID | info |
| `network_lldp_neighbor_chassis_id` | Neighbor chassis ID | info |
| `network_lldp_neighbor_port_description` | Neighbor port description | info |

### OSPF Metrics

| Universal Metric | Description | Values | Type |
|------------------|-------------|--------|------|
| `network_ospf_neighbor_state` | OSPF neighbor state | 1-8 (DOWN to FULL) | gauge |
| `network_ospf_neighbor_priority` | Neighbor priority | 0-255 | gauge |
| `network_ospf_neighbor_dead_timer` | Dead timer value | seconds | gauge |
| `network_ospf_area_lsa_count` | LSA count in area | count | gauge |
| `network_ospf_interface_cost` | Interface cost | cost | gauge |

## Vendor-Specific Mappings

### Nokia SR Linux

#### Interface Metrics

**OpenConfig Support**: ✅ Excellent

| Universal Metric | SR Linux OpenConfig Path | SR Linux Native Path |
|------------------|-------------------------|---------------------|
| `network_interface_in_octets` | `/interfaces/interface/state/counters/in-octets` | `/interface/statistics/in-octets` |
| `network_interface_out_octets` | `/interfaces/interface/state/counters/out-octets` | `/interface/statistics/out-octets` |
| `network_interface_in_packets` | `/interfaces/interface/state/counters/in-pkts` | `/interface/statistics/in-packets` |
| `network_interface_out_packets` | `/interfaces/interface/state/counters/out-pkts` | `/interface/statistics/out-packets` |
| `network_interface_in_errors` | `/interfaces/interface/state/counters/in-errors` | `/interface/statistics/in-error-packets` |
| `network_interface_out_errors` | `/interfaces/interface/state/counters/out-errors` | `/interface/statistics/out-error-packets` |

**Interface Name Normalization**:
- `ethernet-1/1` → `eth1_1`
- `ethernet-1/49` → `eth1_49`
- Pattern: `^ethernet-(\d+)/(\d+)$` → `eth${1}_${2}`

**Vendor Tags**:
- `vendor=nokia`
- `os=srlinux`

#### BGP Metrics

**OpenConfig Support**: ⚠️ Partial (use native paths for full features)

| Universal Metric | SR Linux OpenConfig Path | SR Linux Native Path |
|------------------|-------------------------|---------------------|
| `network_bgp_session_state` | `/network-instances/.../bgp/neighbors/neighbor/state/session-state` | `/network-instance/protocols/bgp/neighbor/session-state` |
| `network_bgp_established_transitions` | `/network-instances/.../state/established-transitions` | `/network-instance/protocols/bgp/neighbor/statistics/established-transitions` |
| `network_bgp_received_routes` | `/network-instances/.../afi-safis/afi-safi/state/received` | `/network-instance/protocols/bgp/neighbor/received-routes` |
| `network_bgp_sent_routes` | `/network-instances/.../afi-safis/afi-safi/state/sent` | `/network-instance/protocols/bgp/neighbor/sent-routes` |

**Recommendation**: Use OpenConfig for basic state, native paths for EVPN details.

### Arista cEOS

#### Interface Metrics

**OpenConfig Support**: ✅ Excellent

| Universal Metric | Arista OpenConfig Path | Arista Native Path |
|------------------|----------------------|-------------------|
| `network_interface_in_octets` | `/interfaces/interface/state/counters/in-octets` | `/Sysdb/.../inOctets` |
| `network_interface_out_octets` | `/interfaces/interface/state/counters/out-octets` | `/Sysdb/.../outOctets` |
| `network_interface_in_packets` | `/interfaces/interface/state/counters/in-pkts` | `/Sysdb/.../inUcastPkts` |
| `network_interface_out_packets` | `/interfaces/interface/state/counters/out-pkts` | `/Sysdb/.../outUcastPkts` |
| `network_interface_in_errors` | `/interfaces/interface/state/counters/in-errors` | `/Sysdb/.../inErrors` |
| `network_interface_out_errors` | `/interfaces/interface/state/counters/out-errors` | `/Sysdb/.../outErrors` |

**Interface Name Normalization**:
- `Ethernet1/1` → `eth1_1` (modular)
- `Ethernet1` → `eth1_0` (fixed)
- Pattern: `^Ethernet(\d+)/(\d+)$` → `eth${1}_${2}`
- Pattern: `^Ethernet(\d+)$` → `eth${1}_0`

**Vendor Tags**:
- `vendor=arista`
- `os=eos`

#### BGP Metrics

**OpenConfig Support**: ✅ Excellent

| Universal Metric | Arista OpenConfig Path |
|------------------|----------------------|
| `network_bgp_session_state` | `/network-instances/.../bgp/neighbors/neighbor/state/session-state` |
| `network_bgp_established_transitions` | `/network-instances/.../state/established-transitions` |
| `network_bgp_received_routes` | `/network-instances/.../afi-safis/afi-safi/state/received` |
| `network_bgp_sent_routes` | `/network-instances/.../afi-safis/afi-safi/state/sent` |

**Recommendation**: Use OpenConfig paths - excellent support.

### Dell EMC SONiC

#### Interface Metrics

**OpenConfig Support**: ⚠️ Good for basic metrics

| Universal Metric | SONiC OpenConfig Path | SONiC Native Path |
|------------------|---------------------|------------------|
| `network_interface_in_octets` | `/interfaces/interface/state/counters/in-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets` |
| `network_interface_out_octets` | `/interfaces/interface/state/counters/out-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets` |
| `network_interface_in_packets` | `/interfaces/interface/state/counters/in-pkts` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-pkts` |
| `network_interface_out_packets` | `/interfaces/interface/state/counters/out-pkts` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-pkts` |
| `network_interface_in_errors` | `/interfaces/interface/state/counters/in-errors` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-errors` |
| `network_interface_out_errors` | `/interfaces/interface/state/counters/out-errors` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-errors` |

**Interface Name Normalization**:
- `Ethernet0` → `eth0_0`
- `Ethernet48` → `eth48_0`
- Pattern: `^Ethernet(\d+)$` → `eth${1}_0`

**Vendor Tags**:
- `vendor=dellemc`
- `os=sonic`

#### BGP Metrics

**OpenConfig Support**: ⚠️ Limited (use native paths)

| Universal Metric | SONiC OpenConfig Path | SONiC Native Path |
|------------------|---------------------|------------------|
| `network_bgp_session_state` | `/network-instances/.../bgp/neighbors/neighbor/state/session-state` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state` |
| `network_bgp_established_transitions` | `/network-instances/.../state/established-transitions` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/established-transitions` |
| `network_bgp_received_routes` | `/network-instances/.../afi-safis/afi-safi/state/received` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/received-routes` |
| `network_bgp_sent_routes` | `/network-instances/.../afi-safis/afi-safi/state/sent` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/sent-routes` |

**Recommendation**: Use native paths for better reliability.

### Juniper Junos

#### Interface Metrics

**OpenConfig Support**: ✅ Good

| Universal Metric | Juniper OpenConfig Path | Juniper Native Path |
|------------------|------------------------|-------------------|
| `network_interface_in_octets` | `/interfaces/interface/state/counters/in-octets` | `/junos/system/linecard/interface/logical/usage/in-octets` |
| `network_interface_out_octets` | `/interfaces/interface/state/counters/out-octets` | `/junos/system/linecard/interface/logical/usage/out-octets` |
| `network_interface_in_packets` | `/interfaces/interface/state/counters/in-pkts` | `/junos/system/linecard/interface/logical/usage/in-pkts` |
| `network_interface_out_packets` | `/interfaces/interface/state/counters/out-pkts` | `/junos/system/linecard/interface/logical/usage/out-pkts` |
| `network_interface_in_errors` | `/interfaces/interface/state/counters/in-errors` | `/junos/system/linecard/interface/logical/usage/in-errors` |
| `network_interface_out_errors` | `/interfaces/interface/state/counters/out-errors` | `/junos/system/linecard/interface/logical/usage/out-errors` |

**Interface Name Normalization**:
- `ge-0/0/0` → `eth0_0_0` (gigabit)
- `xe-0/0/0` → `eth0_0_0` (10G)
- `et-0/0/0` → `eth0_0_0` (40G/100G)
- Pattern: `^(ge|xe|et)-(\d+)/(\d+)/(\d+)$` → `eth${2}_${3}_${4}`

**Vendor Tags**:
- `vendor=juniper`
- `os=junos`

#### BGP Metrics

**OpenConfig Support**: ⚠️ Good for basic state

| Universal Metric | Juniper OpenConfig Path | Juniper Native Path |
|------------------|------------------------|-------------------|
| `network_bgp_session_state` | `/network-instances/.../bgp/neighbors/neighbor/state/session-state` | `/junos/routing/bgp/neighbor/state` |
| `network_bgp_established_transitions` | `/network-instances/.../state/established-transitions` | `/junos/routing/bgp/neighbor/flap-count` |
| `network_bgp_received_routes` | `/network-instances/.../afi-safis/afi-safi/state/received` | `/junos/routing/bgp/neighbor/received-routes` |
| `network_bgp_sent_routes` | `/network-instances/.../afi-safis/afi-safi/state/sent` | `/junos/routing/bgp/neighbor/advertised-routes` |

**Recommendation**: Use OpenConfig where available, native for advanced features.

## Cross-Vendor Comparison

### Interface Name Formats

| Vendor | Native Format | Normalized Format | Levels |
|--------|---------------|-------------------|--------|
| SR Linux | `ethernet-1/1` | `eth1_1` | 2 |
| Arista | `Ethernet1` or `Ethernet1/1` | `eth1_0` or `eth1_1` | 1-2 |
| SONiC | `Ethernet0` | `eth0_0` | 1 |
| Juniper | `ge-0/0/0` | `eth0_0_0` | 3 |

### OpenConfig Support Matrix

| Feature | SR Linux | Arista | SONiC | Juniper |
|---------|----------|--------|-------|---------|
| Interface Counters | ✅ Full | ✅ Full | ⚠️ Good | ✅ Good |
| BGP Basic State | ⚠️ Partial | ✅ Full | ⚠️ Limited | ⚠️ Good |
| LLDP | ✅ Full | ✅ Full | ⚠️ Limited | ⚠️ Good |
| OSPF | ⚠️ Partial | ⚠️ Limited | ❌ Poor | ⚠️ Limited |

**Legend**:
- ✅ Full: Complete OpenConfig support
- ⚠️ Good/Partial/Limited: Some features supported
- ❌ Poor: Minimal or no OpenConfig support

## Transformation Rules

### gNMIc Processor Configuration

The normalization is implemented using three gNMIc event processors:

1. **normalize_interface_metrics**: Transforms interface paths and names
2. **normalize_bgp_metrics**: Transforms BGP paths and state values
3. **add_vendor_tags**: Adds vendor identification labels

**Example Configuration**:

```yaml
processors:
  normalize_interface_metrics:
    event-processors:
      # Transform metric names
      - event-convert:
          value-names:
            - "^/interface/statistics/in-octets$"
            - "^/interfaces/interface/state/counters/in-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: ".*/in-octets$"
                new: "network_interface_in_octets"
      
      # Normalize interface names
      - event-convert:
          tag-names:
            - "interface_name"
            - "interface"
          transforms:
            # Juniper (must come first - 3 levels)
            - replace:
                apply-on: "value"
                old: "^(ge|xe|et)-(\\d+)/(\\d+)/(\\d+)$"
                new: "eth${2}_${3}_${4}"
            # SR Linux (2 levels)
            - replace:
                apply-on: "value"
                old: "^ethernet-(\\d+)/(\\d+)$"
                new: "eth${1}_${2}"
            # Arista modular (2 levels)
            - replace:
                apply-on: "value"
                old: "^Ethernet(\\d+)/(\\d+)$"
                new: "eth${1}_${2}"
            # Arista/SONiC fixed (1 level)
            - replace:
                apply-on: "value"
                old: "^Ethernet(\\d+)$"
                new: "eth${1}_0"
  
  add_vendor_tags:
    event-processors:
      # SR Linux
      - event-add-tag:
          tag-name: vendor
          value: "nokia"
          condition: 'contains(source, "srlinux") || contains(source, "nokia")'
      
      # Arista
      - event-add-tag:
          tag-name: vendor
          value: "arista"
          condition: 'contains(source, "arista") || contains(source, "eos")'
      
      # SONiC
      - event-add-tag:
          tag-name: vendor
          value: "dellemc"
          condition: 'contains(source, "sonic") || contains(source, "dell")'
      
      # Juniper
      - event-add-tag:
          tag-name: vendor
          value: "juniper"
          condition: 'contains(source, "juniper") || contains(source, "junos") || contains(source, "vmx") || contains(source, "crpd")'

outputs:
  prom:
    type: prometheus
    listen: :9273
    path: /metrics
    event-processors:
      - normalize_interface_metrics
      - normalize_bgp_metrics
      - add_vendor_tags
```

### Prometheus Relabeling

Additional normalization at Prometheus level:

```yaml
scrape_configs:
  - job_name: 'gnmic'
    static_configs:
      - targets: ['gnmic:9273']
    
    metric_relabel_configs:
      # Drop old metric names (optional)
      - source_labels: [__name__]
        regex: '.*/interface/statistics/.*'
        action: drop
      
      # Ensure vendor label exists
      - source_labels: [source]
        regex: '(.*-)(nokia|arista|sonic|juniper)(-.*)' 
        target_label: vendor
        replacement: '${2}'
```

## Universal Query Examples

### Interface Bandwidth (All Vendors)

```promql
# Total bandwidth across all vendors
sum(rate(network_interface_in_octets[5m]) * 8) by (vendor)

# Specific interface across all vendors
rate(network_interface_in_octets{interface="eth1_1"}[5m]) * 8

# Compare vendors
sum(rate(network_interface_in_octets[5m]) * 8) by (vendor, source)
```

### BGP Session Monitoring (All Vendors)

```promql
# Count established sessions
count(network_bgp_session_state == 6) by (vendor)

# Session flap rate
rate(network_bgp_established_transitions[5m])

# Sessions by state
count(network_bgp_session_state) by (state, vendor)
```

### Interface Errors (All Vendors)

```promql
# Error rate by vendor
sum(rate(network_interface_in_errors[5m])) by (vendor)

# Top 10 interfaces by errors
topk(10, rate(network_interface_in_errors[5m]))

# Error percentage
(rate(network_interface_in_errors[5m]) / rate(network_interface_in_packets[5m])) * 100
```

### Multi-Vendor Comparison

```promql
# Interface utilization by vendor
(rate(network_interface_in_octets[5m]) * 8 / network_interface_speed) * 100

# BGP route count by vendor
sum(network_bgp_received_routes) by (vendor)

# LLDP neighbor count by vendor
count(network_lldp_neighbor_system_name) by (vendor)
```

## Validation

### Automated Validation Scripts

Each vendor has a validation script:

```bash
# Validate SR Linux normalization
./monitoring/gnmic/validate-normalization.sh

# Validate Arista normalization
./monitoring/gnmic/validate-arista-normalization.sh

# Validate SONiC normalization
./monitoring/gnmic/validate-sonic-normalization.sh

# Validate Juniper normalization
./monitoring/gnmic/validate-juniper-normalization.sh
```

### Manual Validation

```bash
# Check normalized metrics exist
curl -s http://localhost:9273/metrics | grep network_interface_in_octets

# Check vendor tags
curl -s http://localhost:9273/metrics | grep 'vendor="nokia"'

# Check interface name normalization
curl -s http://localhost:9273/metrics | grep 'interface="eth1_1"'

# Query Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets' | jq
```

## Troubleshooting

### Common Issues

**Issue**: Metrics still have vendor-specific names

**Solution**:
1. Verify processors are configured in `gnmic-config.yml`
2. Check processor order in outputs section
3. Restart gNMIc container

**Issue**: Interface names not normalized

**Solution**:
1. Check regex patterns match your interface format
2. Verify correct label name (interface vs interface_name)
3. Ensure Juniper pattern comes first (3-level before 2-level)

**Issue**: Vendor tags missing

**Solution**:
1. Verify device name contains vendor identifier
2. Check add_vendor_tags processor conditions
3. Update conditions to match your naming convention

**Issue**: Old and new metric names both present

**Solution**:
- This is expected behavior (processors add, don't remove)
- Use Prometheus relabeling to drop old names if needed

## Performance Considerations

### Processor Overhead

- **CPU Impact**: <1% per processor
- **Memory Impact**: <10MB additional
- **Latency Impact**: <1ms per metric

### Metric Volume

- **Before normalization**: ~500 metrics per device
- **After normalization**: ~500 metrics per device (same count)
- **With vendor labels**: ~500 metrics per device (labels don't increase count)

### Recommendations

1. Keep processors in logical order
2. Use simple regex patterns
3. Use conditions to avoid unnecessary tag additions
4. Monitor gNMIc CPU/memory usage

## Related Documentation

- **Vendor-Specific Normalization**:
  - `monitoring/gnmic/SR-LINUX-NORMALIZATION.md`
  - `monitoring/gnmic/ARISTA-NORMALIZATION.md`
  - `monitoring/gnmic/SONIC-NORMALIZATION.md`
  - `monitoring/gnmic/JUNIPER-NORMALIZATION.md`
- **Normalization Mappings**: `monitoring/gnmic/normalization-mappings.yml`
- **Transformation Rules**: `monitoring/gnmic/transformation-rules.yml`
- **Vendor Requirements**: `docs/developer/vendor-requirements.md`
- **Architecture Guide**: `docs/developer/architecture.md`

## Summary

Metric normalization enables:
- **Universal queries** that work across all 4 vendors
- **Consistent naming** with `network_*` prefix
- **Vendor transparency** - users don't need vendor-specific knowledge
- **Preserved values** - only names/labels change, not data
- **Debugging support** - original metrics available when needed

With normalization complete, a single Grafana dashboard can monitor SR Linux, Arista, SONiC, and Juniper devices using identical queries.
