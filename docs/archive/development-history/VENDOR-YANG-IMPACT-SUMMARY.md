# Impact of Using Vendor YANG Models - Summary

## Quick Answer

**Prometheus**: No changes needed - it collects whatever metrics gNMIc exposes

**Grafana**: Queries must use vendor-specific metric names instead of universal OpenConfig names

## The Difference

### With OpenConfig (Ideal)
```promql
# One query works for all vendors
rate(gnmic_interfaces_interface_state_counters_in_octets[5m]) * 8
```

### With Vendor Models (Reality)
```promql
# SR Linux
rate(gnmic_srl_interface_statistics_in_octets[5m]) * 8

# Arista (when added)
rate(gnmic_eos_interface_counters_in_octets[5m]) * 8

# SONiC (when added)
rate(gnmic_sonic_interface_counters_in_octets[5m]) * 8
```

## What Changes

### ❌ Doesn't Change
- **Prometheus setup** - Same configuration
- **gNMIc setup** - Just different paths in subscriptions
- **Data collection** - Works the same way
- **Metric storage** - Same time-series database

### ✅ Does Change
- **Metric names** - Different per vendor
- **Grafana queries** - Must account for vendor differences
- **Dashboard organization** - May need vendor-specific dashboards
- **Alert rules** - Must handle multiple metric names

## Solutions

### Solution 1: Vendor-Specific Dashboards (Simplest)

Create separate dashboards per vendor:
```
Grafana/
├── SR Linux - Interfaces
├── SR Linux - BGP
├── Arista - Interfaces
├── Arista - BGP
└── Network Overview (high-level)
```

**Pros**: Simple, clean, vendor-specific features accessible
**Cons**: Dashboard duplication, more maintenance

### Solution 2: Multi-Vendor Dashboards with Variables

Use Grafana variables to switch vendors:
```promql
# Dashboard variable: $vendor
rate(gnmic_${vendor}_interface_statistics_in_octets[5m]) * 8
```

**Pros**: Single dashboard, easy comparison
**Cons**: Complex queries, may not support all features

### Solution 3: Hybrid (Recommended)

- **Common metrics**: Unified dashboards with vendor variables
- **Vendor-specific features**: Separate dashboards

**Example**:
- "Network Overview" - All vendors, basic metrics
- "SR Linux EVPN" - SR Linux specific
- "Arista VXLAN" - Arista specific

## Current Lab Status

### What's Working Now

**SR Linux metrics being collected**:
```promql
# BGP state
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state

# BGP routes
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes

# OSPF state
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state
```

**Your existing dashboards** already use SR Linux native metrics, so they work!

### When You Add Arista

You'll need to:
1. Add Arista-specific subscriptions to gNMIc
2. Create Arista dashboards OR
3. Update existing dashboards with multi-vendor queries

## Practical Example

### Current Dashboard Query (SR Linux)
```promql
# BGP sessions established
count(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{session_state="established"})
```

### Future Multi-Vendor Query
```promql
# BGP sessions established (all vendors)
count(
  gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{session_state="established"}
  or
  gnmic_eos_bgp_neighbor_session_state{state="Established"}
)
```

## Best Practices

### 1. Add Vendor Tags in gNMIc

```yaml
targets:
  spine1:
    address: clab-gnmi-clos-spine1:57400
    tags:
      vendor: nokia
      device_type: spine
```

Then filter in Grafana:
```promql
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state{vendor="nokia"}
```

### 2. Use Dashboard Variables

```
Variable: $vendor
Values: nokia, arista, dellemc

Variable: $device
Query: label_values(gnmic_up{vendor=~"$vendor"}, source)
```

### 3. Document Metric Mappings

Keep a reference of equivalent metrics:
```
Interface Throughput:
- SR Linux: gnmic_srl_interface_statistics_in_octets
- Arista: gnmic_eos_interface_counters_in_octets
- SONiC: gnmic_sonic_interface_counters_in_octets
```

## Impact Summary

| Component | Impact | Mitigation |
|-----------|--------|------------|
| **Prometheus** | None | No changes needed |
| **gNMIc** | Different paths | Update subscriptions per vendor |
| **Grafana Queries** | High | Use variables or separate dashboards |
| **Dashboards** | Medium | Vendor-specific or multi-vendor with variables |
| **Alerts** | Medium | Handle multiple metric names |
| **Maintenance** | Higher | More queries to maintain |

## Recommendation

**For your current lab** (SR Linux only):
- ✅ Keep using SR Linux native metrics (already working)
- ✅ Your existing dashboards are fine
- ✅ No changes needed

**When adding Arista**:
1. Start with Arista-specific dashboards (simple)
2. Add vendor tags to all devices
3. Create multi-vendor overview dashboard
4. Keep vendor-specific dashboards for advanced features

**Long term**:
- Accept that vendor models = vendor-specific queries
- Use smart dashboard design to minimize duplication
- Focus on unified overview dashboards
- Keep detailed vendor-specific dashboards

## Key Takeaway

Using vendor YANG models doesn't break anything - it just means your Grafana queries need to be vendor-aware. The trade-off is:

- **Lose**: Universal queries across vendors
- **Gain**: Full access to all vendor features

Since OpenConfig doesn't work on SR Linux anyway, you're not losing anything. You're just being explicit about using vendor-specific models, which gives you complete feature access.

## Documentation

- **Detailed Guide**: `monitoring/VENDOR-SPECIFIC-DASHBOARDS-GUIDE.md`
- **Current Metrics**: `monitoring/CURRENT-METRICS-REFERENCE.md`
- **Test Results**: `OPENCONFIG-TEST-RESULTS.md`
