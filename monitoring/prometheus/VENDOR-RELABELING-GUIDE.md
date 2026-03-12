# Prometheus Vendor-Specific Relabeling Guide

## Overview

This guide documents the vendor-specific relabeling rules implemented in Prometheus to enrich metrics with device role, topology, and vendor information. These rules work in conjunction with gNMIc metric normalization to provide comprehensive labeling for multi-vendor network monitoring.

## Architecture

The labeling strategy uses a two-stage approach:

1. **Stage 1 (gNMIc)**: Basic metric normalization and vendor detection
   - Transforms vendor-specific metric paths to universal names
   - Adds `vendor` and `os` labels based on device detection
   - Normalizes interface names and BGP states

2. **Stage 2 (Prometheus)**: Enrichment with topology and role information
   - Adds `role` labels (spine, leaf) based on device names
   - Adds `topology` labels from external labels
   - Adds `fabric_type` and `layer` labels for network architecture context

## Relabeling Rules

### 1. Vendor Label Preservation

**Purpose**: Preserve vendor and OS labels added by gNMIc processors

**Labels Preserved**:
- `vendor`: Device vendor (nokia, arista, dellemc, juniper)
- `os`: Operating system (srlinux, eos, sonic, junos)

**Source**: These labels are added by gNMIc's `add_vendor_tags` processor and automatically preserved by Prometheus.

**Example**:
```promql
gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{vendor="nokia", os="srlinux"}
```

### 2. Device Role Labels

**Purpose**: Identify the role of each device in the network topology

**Configuration**:
```yaml
# Spine devices: spine1, spine2
- source_labels: [source]
  target_label: role
  regex: '(spine\d+)'
  replacement: 'spine'

# Leaf devices: leaf1, leaf2, leaf3, leaf4
- source_labels: [source]
  target_label: role
  regex: '(leaf\d+)'
  replacement: 'leaf'
```

**Labels Added**:
- `role`: Device role (spine, leaf)

**Use Cases**:
- Filter metrics by device role: `{role="spine"}`
- Aggregate metrics by role: `sum by (role) (...)`
- Create role-specific dashboards

**Example Queries**:
```promql
# All spine interface metrics
rate(network_interface_in_octets{role="spine"}[5m])

# Leaf device BGP sessions
network_bgp_session_state{role="leaf"}

# Count devices by role
count by (role) (up)
```

### 3. Topology Labels

**Purpose**: Identify the network topology and fabric architecture

**Configuration**:
```yaml
# Topology name from external label
- source_labels: [cluster]
  target_label: topology
  regex: '(.*)'
  replacement: '$1'

# Add fabric type label (EVPN/VXLAN Clos fabric)
- source_labels: [role]
  target_label: fabric_type
  regex: '(spine|leaf)'
  replacement: 'clos'
```

**Labels Added**:
- `topology`: Topology name (e.g., gnmi-clos)
- `fabric_type`: Network fabric architecture (clos)

**Use Cases**:
- Multi-topology monitoring (when running multiple labs)
- Fabric-specific queries and dashboards
- Topology comparison and analysis

**Example Queries**:
```promql
# All metrics from gnmi-clos topology
{topology="gnmi-clos"}

# Clos fabric interface metrics
network_interface_in_octets{fabric_type="clos"}

# Compare topologies
sum by (topology) (network_interface_in_octets)
```

### 4. Layer Labels

**Purpose**: Identify the network layer function of each device

**Configuration**:
```yaml
# Add layer label (spine = layer3, leaf = layer2/layer3)
- source_labels: [role]
  target_label: layer
  regex: 'spine'
  replacement: 'layer3'

- source_labels: [role]
  target_label: layer
  regex: 'leaf'
  replacement: 'layer2_layer3'
```

**Labels Added**:
- `layer`: Network layer function
  - `layer3`: Pure layer 3 routing (spines)
  - `layer2_layer3`: Layer 2 switching + layer 3 routing (leafs)

**Use Cases**:
- Layer-specific monitoring and alerting
- Routing vs switching metrics separation
- Network architecture documentation

**Example Queries**:
```promql
# Layer 3 routing metrics
network_bgp_session_state{layer="layer3"}

# Layer 2/3 interface metrics
network_interface_in_octets{layer="layer2_layer3"}
```

## Complete Label Set

After both gNMIc and Prometheus processing, metrics have the following labels:

| Label | Source | Values | Description |
|-------|--------|--------|-------------|
| `source` | gNMIc | spine1, spine2, leaf1-4 | Device hostname |
| `name` | Prometheus | Same as source | Dashboard compatibility |
| `vendor` | gNMIc | nokia, arista, dellemc, juniper | Device vendor |
| `os` | gNMIc | srlinux, eos, sonic, junos | Operating system |
| `role` | Prometheus | spine, leaf | Device role in topology |
| `topology` | Prometheus | gnmi-clos | Topology name |
| `fabric_type` | Prometheus | clos | Network fabric architecture |
| `layer` | Prometheus | layer3, layer2_layer3 | Network layer function |
| `interface_normalized` | Prometheus | eth1_1, eth0_0 | Normalized interface name |

## Example Metric with All Labels

```promql
gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{
  source="spine1",
  name="spine1",
  vendor="nokia",
  os="srlinux",
  role="spine",
  topology="gnmi-clos",
  fabric_type="clos",
  layer="layer3",
  interface_normalized="eth1_1",
  interface_name="ethernet-1/1"
}
```

## Dashboard Query Patterns

### Universal Queries (Work Across All Vendors)

```promql
# Interface bandwidth by role
rate(network_interface_in_octets{role="spine"}[5m]) * 8

# BGP sessions by vendor
count by (vendor) (network_bgp_session_state == 1)

# Interface errors by topology
sum by (topology, role) (rate(network_interface_in_errors[5m]))
```

### Role-Based Queries

```promql
# Spine uplink utilization
rate(network_interface_in_octets{role="spine", interface_normalized=~"eth1_.*"}[5m]) * 8

# Leaf access port statistics
rate(network_interface_in_octets{role="leaf", interface_normalized=~"eth1_3"}[5m]) * 8
```

### Topology-Based Queries

```promql
# Total fabric bandwidth
sum(rate(network_interface_in_octets{fabric_type="clos"}[5m])) * 8

# Topology health score
(
  count(network_bgp_session_state{topology="gnmi-clos"} == 1) /
  count(network_bgp_session_state{topology="gnmi-clos"})
) * 100
```

### Layer-Based Queries

```promql
# Layer 3 routing metrics
sum by (source) (network_bgp_received_routes{layer="layer3"})

# Layer 2/3 switching metrics
rate(network_interface_in_octets{layer="layer2_layer3"}[5m]) * 8
```

## Validation

Use the validation script to verify relabeling rules are working correctly:

```bash
./monitoring/prometheus/validate-relabeling.sh
```

The script validates:
- ✓ Vendor labels are preserved from gNMIc
- ✓ Device role labels are correctly applied
- ✓ Topology labels are present
- ✓ Layer labels match device roles
- ✓ Label combinations are consistent

## Adding New Device Roles

To add support for new device roles (e.g., border, superspine):

1. **Update Prometheus relabeling rules**:
```yaml
# Border routers
- source_labels: [source]
  target_label: role
  regex: '(border\d+)'
  replacement: 'border'
```

2. **Add layer label mapping**:
```yaml
- source_labels: [role]
  target_label: layer
  regex: 'border'
  replacement: 'layer3'
```

3. **Update fabric_type regex** (if needed):
```yaml
- source_labels: [role]
  target_label: fabric_type
  regex: '(spine|leaf|border)'
  replacement: 'clos'
```

4. **Update validation script** to test new role

## Adding New Topologies

To support multiple topologies:

1. **Deploy with different cluster name**:
```yaml
# prometheus.yml
global:
  external_labels:
    cluster: 'production-dc1'  # Different topology name
```

2. **Queries automatically work**:
```promql
# Compare topologies
sum by (topology) (network_interface_in_octets)

# Filter by topology
network_bgp_session_state{topology="production-dc1"}
```

## Production Considerations

### Cardinality Management

Each label increases metric cardinality. Current labels add:
- `role`: 2 values (spine, leaf) → 2x cardinality
- `topology`: 1 value per deployment → Nx cardinality
- `fabric_type`: 1 value (clos) → 1x cardinality
- `layer`: 2 values (layer3, layer2_layer3) → 2x cardinality

**Total cardinality multiplier**: ~4x per topology

**Recommendation**: For large deployments (1000+ devices), consider:
- Using recording rules to pre-aggregate by role
- Limiting topology labels to essential values
- Using separate Prometheus instances per topology

### Label Consistency

Ensure label values are consistent across:
- Containerlab topology definitions
- gNMIc target configurations
- Prometheus relabeling rules
- Grafana dashboard queries

**Best Practice**: Use a configuration management system (Ansible, Terraform) to generate consistent labels across all components.

### Performance Impact

Relabeling rules are evaluated for every scraped metric. Current rules:
- 10 relabeling rules per metric
- Regex evaluation: ~1-2ms per rule
- Total overhead: ~10-20ms per scrape

**Impact**: Negligible for typical deployments (<100 devices, <10k metrics/device)

## Troubleshooting

### Labels Not Appearing

1. **Check gNMIc is adding vendor labels**:
```bash
curl http://localhost:9273/metrics | grep vendor
```

2. **Check Prometheus relabeling**:
```bash
curl http://localhost:9090/api/v1/query?query=up | jq '.data.result[0].metric'
```

3. **Verify regex patterns match device names**:
```bash
# Test regex
echo "spine1" | grep -E '(spine\d+)'
```

### Incorrect Label Values

1. **Check source label**:
```promql
{__name__=~".+", source!=""}
```

2. **Verify external labels**:
```bash
curl http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep external_labels -A 5
```

3. **Test relabeling rules**:
```bash
# Use Prometheus relabel debug endpoint (if available)
curl -X POST http://localhost:9090/api/v1/relabel \
  -d 'metric=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets' \
  -d 'source=spine1'
```

## References

- [Prometheus Relabeling Documentation](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#relabel_config)
- [gNMIc Event Processors](https://gnmic.openconfig.net/user_guide/event_processors/intro/)
- Task 16.1: Interface Name Normalization Rules
- Task 15: gNMIc Metric Normalization (all vendors)
- Design Document: Phase 4 - Telemetry Normalization
- Requirements: 4.2 (vendor-agnostic metric paths)
