# Vendor-Specific Dashboards Guide

## Impact of Using Vendor YANG Models

When using vendor-specific YANG models instead of OpenConfig, your Grafana dashboards and Prometheus queries need to account for different metric names and structures per vendor.

## The Challenge

### OpenConfig (Ideal but Not Always Available)

**Single query works across all vendors**:
```promql
# Interface throughput - works on SR Linux, Arista, SONiC
rate(gnmic_interfaces_interface_state_counters_in_octets[5m]) * 8
```

### Vendor-Specific (Reality)

**Different query per vendor**:
```promql
# SR Linux
rate(gnmic_srl_interface_statistics_in_octets[5m]) * 8

# Arista EOS
rate(gnmic_eos_interface_counters_in_octets[5m]) * 8

# SONiC
rate(gnmic_sonic_interface_counters_in_octets[5m]) * 8
```

## Solution Strategies

### Strategy 1: Vendor-Specific Dashboards

Create separate dashboards per vendor.

**Pros**:
- Simple to implement
- Vendor-specific features easily accessible
- No query complexity

**Cons**:
- Dashboard duplication
- More maintenance
- Can't compare vendors side-by-side

**Example Structure**:
```
Grafana Dashboards/
├── SR Linux/
│   ├── SR Linux - Interfaces
│   ├── SR Linux - BGP
│   └── SR Linux - EVPN
├── Arista EOS/
│   ├── Arista - Interfaces
│   ├── Arista - BGP
│   └── Arista - VXLAN
└── Multi-Vendor/
    └── Network Overview (high-level only)
```

### Strategy 2: Unified Dashboards with Variables

Use Grafana variables to switch between vendors.

**Pros**:
- Single dashboard for all vendors
- Easy vendor comparison
- Centralized maintenance

**Cons**:
- Complex queries
- Requires careful metric naming
- May not support all vendor-specific features

**Implementation**:
```
Dashboard Variable: $vendor
Values: srlinux, arista, sonic

Query:
rate(gnmic_${vendor}_interface_statistics_in_octets[5m]) * 8
```

### Strategy 3: Hybrid Approach (Recommended)

Combine both strategies based on use case.

**Common Metrics**: Unified dashboards
- Interface throughput
- Interface status
- Basic BGP neighbor state

**Vendor-Specific Features**: Separate dashboards
- EVPN details
- Advanced routing protocols
- Platform-specific features

## Prometheus Metric Naming

### Current SR Linux Metrics

```promql
# Interface statistics
gnmic_srl_interface_statistics_in_octets{interface="ethernet-1/1",source="spine1"}
gnmic_srl_interface_statistics_out_octets{interface="ethernet-1/1",source="spine1"}

# BGP state
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state{source="spine1"}

# OSPF state
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state{source="spine1"}
```

### Expected Arista Metrics (When Added)

```promql
# Interface statistics
gnmic_eos_interface_counters_in_octets{interface="Ethernet1",source="arista-spine1"}
gnmic_eos_interface_counters_out_octets{interface="Ethernet1",source="arista-spine1"}

# BGP state
gnmic_eos_bgp_neighbor_state{neighbor="10.0.1.1",source="arista-spine1"}
```

## Grafana Dashboard Examples

### Example 1: Vendor-Specific Dashboard (SR Linux)

**Dashboard**: "SR Linux - Interface Statistics"

**Panel**: Interface Throughput
```promql
# Query
rate(gnmic_srl_interface_statistics_in_octets{source=~"$device",interface=~"$interface"}[5m]) * 8

# Variables
$device: spine1, spine2, leaf1, leaf2, leaf3, leaf4
$interface: ethernet-1/1, ethernet-1/2, ethernet-1/3, ethernet-1/4

# Legend
{{source}} - {{interface}} - In
```

**Panel**: Interface Errors
```promql
# Query
rate(gnmic_srl_interface_statistics_in_error_packets{source=~"$device",interface=~"$interface"}[5m])

# Alert
> 0 for 5m
```

### Example 2: Multi-Vendor Dashboard with Tags

**Dashboard**: "Network - Interface Overview"

**Panel**: Interface Throughput (All Vendors)
```promql
# Query A: SR Linux
rate(gnmic_srl_interface_statistics_in_octets{vendor="nokia"}[5m]) * 8

# Query B: Arista (when added)
rate(gnmic_eos_interface_counters_in_octets{vendor="arista"}[5m]) * 8

# Query C: SONiC (when added)
rate(gnmic_sonic_interface_counters_in_octets{vendor="dellemc"}[5m]) * 8

# Legend
{{vendor}} - {{source}} - {{interface}}
```

**Key**: Use vendor tags added in gNMIc config!

### Example 3: Unified Dashboard with Metric Relabeling

Use Prometheus relabeling to normalize metric names.

**Prometheus Config** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'gnmic'
    static_configs:
      - targets: ['clab-monitoring-gnmic:9273']
    metric_relabel_configs:
      # Normalize SR Linux interface metrics
      - source_labels: [__name__]
        regex: 'gnmic_srl_interface_statistics_(.*)'
        target_label: __name__
        replacement: 'interface_${1}'
      
      # Normalize Arista interface metrics
      - source_labels: [__name__]
        regex: 'gnmic_eos_interface_counters_(.*)'
        target_label: __name__
        replacement: 'interface_${1}'
      
      # Add vendor label
      - source_labels: [__name__]
        regex: 'gnmic_srl_.*'
        target_label: vendor
        replacement: 'nokia'
      
      - source_labels: [__name__]
        regex: 'gnmic_eos_.*'
        target_label: vendor
        replacement: 'arista'
```

**Grafana Query** (after relabeling):
```promql
# Now works for all vendors!
rate(interface_in_octets{vendor=~"$vendor"}[5m]) * 8
```

## Practical Implementation

### Step 1: Add Vendor Tags in gNMIc

**File**: `monitoring/gnmic/gnmic-config.yml`

```yaml
targets:
  spine1:
    address: clab-gnmi-clos-spine1:57400
    username: admin
    password: NokiaSrl1!
    tags:
      vendor: nokia
      os: srlinux
      device_type: spine
      site: dc1
  
  arista-spine1:
    address: arista-spine1:6030
    username: admin
    password: admin
    tags:
      vendor: arista
      os: eos
      device_type: spine
      site: dc1
```

### Step 2: Create Dashboard Variables

**Grafana Dashboard Variables**:
```
Name: vendor
Type: Query
Query: label_values(vendor)
Multi-value: Yes
Include All: Yes

Name: device
Type: Query
Query: label_values(gnmic_up{vendor=~"$vendor"}, source)
Multi-value: Yes
Include All: Yes

Name: interface
Type: Query
Query: label_values(gnmic_srl_interface_statistics_in_octets{source=~"$device"}, interface)
Multi-value: Yes
Include All: Yes
```

### Step 3: Write Vendor-Aware Queries

**Option A: Separate Queries per Vendor**
```promql
# Panel with multiple queries
Query A (SR Linux):
rate(gnmic_srl_interface_statistics_in_octets{vendor="nokia",source=~"$device"}[5m]) * 8

Query B (Arista):
rate(gnmic_eos_interface_counters_in_octets{vendor="arista",source=~"$device"}[5m]) * 8
```

**Option B: Union with OR**
```promql
# Single query (if metric names align)
rate(
  gnmic_srl_interface_statistics_in_octets{vendor="nokia",source=~"$device"}[5m] or
  gnmic_eos_interface_counters_in_octets{vendor="arista",source=~"$device"}[5m]
) * 8
```

**Option C: Use label_replace**
```promql
# Normalize on the fly
label_replace(
  rate(gnmic_srl_interface_statistics_in_octets[5m]) * 8,
  "metric_type", "interface_throughput", "", ""
) or
label_replace(
  rate(gnmic_eos_interface_counters_in_octets[5m]) * 8,
  "metric_type", "interface_throughput", "", ""
)
```

## Dashboard Organization

### Recommended Structure

```
Grafana/
├── 📊 Network Overview (Multi-Vendor)
│   ├── Device Status (all vendors)
│   ├── Interface Status Summary
│   └── BGP Session Summary
│
├── 📁 SR Linux/
│   ├── SR Linux - Interfaces
│   ├── SR Linux - BGP
│   ├── SR Linux - OSPF
│   └── SR Linux - EVPN
│
├── 📁 Arista EOS/
│   ├── Arista - Interfaces
│   ├── Arista - BGP
│   └── Arista - VXLAN
│
└── 📁 Comparison/
    ├── Interface Performance (all vendors)
    ├── BGP Stability (all vendors)
    └── Vendor Comparison
```

### Dashboard Templates

**Template 1: Vendor-Specific Interface Dashboard**

Variables:
- `$device` - Device name
- `$interface` - Interface name

Panels:
1. Interface Throughput (In/Out)
2. Interface Packet Rate
3. Interface Errors
4. Interface Status
5. Interface Utilization %

**Template 2: Multi-Vendor Overview Dashboard**

Variables:
- `$vendor` - Vendor filter
- `$site` - Site filter

Panels:
1. Device Count by Vendor
2. Total Interface Count
3. BGP Sessions Up/Down
4. Top 10 Interfaces by Traffic
5. Alert Summary

## Query Examples by Use Case

### Use Case 1: Interface Throughput

**SR Linux Only**:
```promql
rate(gnmic_srl_interface_statistics_in_octets{source="spine1",interface="ethernet-1/1"}[5m]) * 8
```

**Multi-Vendor**:
```promql
# SR Linux
rate(gnmic_srl_interface_statistics_in_octets{vendor="nokia"}[5m]) * 8
or
# Arista
rate(gnmic_eos_interface_counters_in_octets{vendor="arista"}[5m]) * 8
```

### Use Case 2: BGP Session State

**SR Linux**:
```promql
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{
  source="spine1",
  neighbor_address="10.0.1.1"
}
```

**Arista** (expected):
```promql
gnmic_eos_bgp_neighbor_session_state{
  source="arista-spine1",
  neighbor="10.0.1.1"
}
```

**Multi-Vendor Alert**:
```promql
# Alert when any BGP session is down
(
  gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state != 1
  or
  gnmic_eos_bgp_neighbor_session_state != 1
) > 0
```

### Use Case 3: Interface Errors

**SR Linux**:
```promql
rate(gnmic_srl_interface_statistics_in_error_packets{source=~"$device"}[5m])
```

**Multi-Vendor with Threshold**:
```promql
(
  rate(gnmic_srl_interface_statistics_in_error_packets{vendor="nokia"}[5m])
  or
  rate(gnmic_eos_interface_counters_in_errors{vendor="arista"}[5m])
) > 0
```

## Best Practices

### 1. Consistent Tagging

Always add these tags in gNMIc config:
```yaml
tags:
  vendor: nokia|arista|dellemc
  os: srlinux|eos|sonic
  device_type: spine|leaf|border
  site: dc1|dc2|dc3
  role: production|staging|lab
```

### 2. Naming Conventions

Use consistent dashboard naming:
- `{Vendor} - {Feature}` for vendor-specific
- `Network - {Feature}` for multi-vendor
- `Comparison - {Feature}` for vendor comparison

### 3. Documentation

Document metric mappings:
```
Interface Throughput:
- SR Linux: gnmic_srl_interface_statistics_in_octets
- Arista: gnmic_eos_interface_counters_in_octets
- SONiC: gnmic_sonic_interface_counters_in_octets
```

### 4. Alert Consistency

Create vendor-agnostic alerts:
```yaml
# Alert rule
- alert: InterfaceDown
  expr: |
    (
      gnmic_srl_interface_oper_state{vendor="nokia"} == 0
      or
      gnmic_eos_interface_oper_status{vendor="arista"} == 0
    )
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Interface {{ $labels.interface }} on {{ $labels.source }} is down"
```

## Migration Path

### Phase 1: Vendor-Specific (Current)
- Create SR Linux dashboards
- Use native SR Linux metrics
- Get comfortable with queries

### Phase 2: Add Second Vendor
- Add Arista devices
- Create Arista dashboards
- Identify common metrics

### Phase 3: Unification
- Create multi-vendor overview dashboards
- Implement metric relabeling if needed
- Build comparison dashboards

### Phase 4: Optimization
- Consolidate where possible
- Keep vendor-specific for advanced features
- Document metric mappings

## Tools and Helpers

### Prometheus Query Builder

```python
# Helper to build multi-vendor queries
def build_multi_vendor_query(metric_map, labels=None):
    """
    metric_map = {
        'nokia': 'gnmic_srl_interface_statistics_in_octets',
        'arista': 'gnmic_eos_interface_counters_in_octets'
    }
    """
    queries = []
    for vendor, metric in metric_map.items():
        label_str = f'vendor="{vendor}"'
        if labels:
            label_str += ',' + ','.join([f'{k}="{v}"' for k, v in labels.items()])
        queries.append(f'{metric}{{{label_str}}}')
    
    return ' or '.join(queries)

# Usage
query = build_multi_vendor_query({
    'nokia': 'gnmic_srl_interface_statistics_in_octets',
    'arista': 'gnmic_eos_interface_counters_in_octets'
}, {'source': 'spine1'})

print(f"rate({query}[5m]) * 8")
```

## Summary

### Prometheus Changes
- ✅ No changes needed - collects all metrics
- ⚠️ Metric names differ per vendor
- ✅ Use tags to identify vendors

### Grafana Changes
- ⚠️ Queries must account for different metric names
- ✅ Use variables for flexibility
- ✅ Create vendor-specific dashboards for advanced features
- ✅ Create unified dashboards for common metrics

### Recommended Approach
1. Start with vendor-specific dashboards (simple)
2. Add vendor tags in gNMIc config
3. Create multi-vendor overview dashboards
4. Use Prometheus relabeling for normalization (optional)
5. Keep vendor-specific dashboards for advanced features

The key is **accepting that vendor-specific models require vendor-specific queries**, but using smart dashboard design and tagging to minimize duplication and enable cross-vendor visibility.
