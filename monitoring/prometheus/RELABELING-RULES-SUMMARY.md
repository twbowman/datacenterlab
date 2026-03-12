# Prometheus Relabeling Rules Summary

## Quick Reference

### Labels Added by Relabeling Rules

| Label | Values | Source | Description |
|-------|--------|--------|-------------|
| `vendor` | nokia, arista, dellemc, juniper | gNMIc (preserved) | Device vendor |
| `os` | srlinux, eos, sonic, junos | gNMIc (preserved) | Operating system |
| `role` | spine, leaf | Prometheus | Device role in topology |
| `topology` | gnmi-clos | Prometheus | Topology name |
| `fabric_type` | clos | Prometheus | Network fabric architecture |
| `layer` | layer3, layer2_layer3 | Prometheus | Network layer function |

### Device Role Mapping

| Device Name Pattern | Role | Layer | Fabric Type |
|---------------------|------|-------|-------------|
| spine1, spine2 | spine | layer3 | clos |
| leaf1, leaf2, leaf3, leaf4 | leaf | layer2_layer3 | clos |

### Common Query Patterns

```promql
# Filter by role
{role="spine"}
{role="leaf"}

# Filter by vendor
{vendor="nokia"}
{vendor="arista"}

# Filter by topology
{topology="gnmi-clos"}

# Filter by layer
{layer="layer3"}
{layer="layer2_layer3"}

# Combine filters
{role="spine", vendor="nokia"}
{role="leaf", topology="gnmi-clos"}
```

### Aggregation Patterns

```promql
# Aggregate by role
sum by (role) (network_interface_in_octets)

# Aggregate by vendor
sum by (vendor) (network_interface_in_octets)

# Aggregate by topology
sum by (topology) (network_interface_in_octets)

# Multi-level aggregation
sum by (topology, role, vendor) (network_interface_in_octets)
```

## Configuration Location

**File**: `monitoring/prometheus/prometheus.yml`

**Section**: `scrape_configs[0].metric_relabel_configs`

## Validation

```bash
# Run validation script
./monitoring/prometheus/validate-relabeling.sh

# Check label values
curl -s 'http://localhost:9090/api/v1/label/role/values' | jq '.data'
curl -s 'http://localhost:9090/api/v1/label/topology/values' | jq '.data'
curl -s 'http://localhost:9090/api/v1/label/vendor/values' | jq '.data'
```

## Documentation

- **VENDOR-RELABELING-GUIDE.md**: Comprehensive guide with examples
- **TASK-16.2-IMPLEMENTATION.md**: Implementation details and testing
- **prometheus.yml**: Configuration with inline comments

## Requirements Satisfied

✅ **Requirement 4.2**: Transform vendor-specific label names to OpenConfig conventions
- Vendor labels preserved from gNMIc
- Device role labels added
- Topology labels added
- Layer labels added
- All labels consistent across vendors
