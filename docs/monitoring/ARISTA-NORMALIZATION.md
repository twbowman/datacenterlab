# Arista EOS Metric Normalization Configuration

## Overview

This document describes the Arista EOS metric normalization configuration implemented in `gnmic-config.yml`. The configuration transforms Arista-specific OpenConfig metric paths and labels into universal normalized metrics that work identically across SR Linux, SONiC, Juniper, and other vendors.

**Requirements**: 4.1, 4.2, 4.3

## Purpose

Enable universal queries across multi-vendor networks by normalizing Arista EOS metrics to standard names. This allows the same Grafana dashboards and Prometheus queries to work seamlessly across all vendors.

## Implementation

### Processors Configured

The gNMIc configuration includes three event processors that handle both SR Linux and Arista metrics:

1. **normalize_interface_metrics** - Transforms interface statistics paths
2. **normalize_bgp_metrics** - Transforms BGP protocol paths
3. **add_vendor_tags** - Adds vendor identification labels

### 1. Interface Metric Normalization

#### Arista OpenConfig Paths

Arista EOS has excellent OpenConfig support for interface counters. The normalization uses standard OpenConfig paths:

| Arista OpenConfig Path | Normalized Metric Name |
|------------------------|------------------------|
| `/interfaces/interface/state/counters/in-octets` | `network_interface_in_octets` |
| `/interfaces/interface/state/counters/out-octets` | `network_interface_out_octets` |
| `/interfaces/interface/state/counters/in-pkts` | `network_interface_in_packets` |
| `/interfaces/interface/state/counters/out-pkts` | `network_interface_out_packets` |
| `/interfaces/interface/state/counters/in-errors` | `network_interface_in_errors` |
| `/interfaces/interface/state/counters/out-errors` | `network_interface_out_errors` |

#### Interface Name Normalization

Arista interface names are normalized to universal format:

| Arista Format | Normalized Format | Notes |
|---------------|-------------------|-------|
| `Ethernet1/1` | `eth1_1` | Modular interfaces |
| `Ethernet1` | `eth1_0` | Fixed interfaces |
| `Ethernet49/1` | `eth49_1` | Uplink ports |

**Implementation**: Uses regex replacement on `interface_name` and `interface` labels:
```yaml
- event-convert:
    tag-names:
      - "interface_name"
      - "interface"
    transforms:
      # Arista: Ethernet1/1 -> eth1_1
      - replace:
          apply-on: "value"
          old: "^Ethernet(\\d+)/(\\d+)$"
          new: "eth${1}_${2}"
      # Arista: Ethernet1 -> eth1_0
      - replace:
          apply-on: "value"
          old: "^Ethernet(\\d+)$"
          new: "eth${1}_0"
```

#### Example Query

**Before normalization** (vendor-specific):
```promql
# Only works for Arista
gnmic_oc_interface_stats_/interfaces/interface/state/counters/in-octets{interface_name="Ethernet1/1"}
```

**After normalization** (universal):
```promql
# Works for all vendors (SR Linux, Arista, SONiC, Juniper)
gnmic_oc_interface_stats_network_interface_in_octets{interface="eth1_1"}
```

### 2. BGP Metric Normalization

#### Arista OpenConfig BGP Paths

Arista EOS has excellent OpenConfig support for BGP metrics:

| Arista OpenConfig Path | Normalized Metric Name |
|------------------------|------------------------|
| `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` | `network_bgp_session_state` |
| `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/peer-as` | `network_bgp_peer_as` |
| `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/received` | `network_bgp_received_routes` |
| `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/sent` | `network_bgp_sent_routes` |

#### BGP State Value Normalization

BGP session state values are normalized to uppercase (same as SR Linux):

| Original Value | Normalized Value |
|----------------|------------------|
| `established` | `ESTABLISHED` |
| `idle` | `IDLE` |
| `connect` | `CONNECT` |
| `active` | `ACTIVE` |

#### Example Query

**Before normalization** (vendor-specific):
```promql
# Only works for Arista
gnmic_oc_bgp_neighbors_/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state
```

**After normalization** (universal):
```promql
# Works for all vendors
gnmic_oc_bgp_neighbors_network_bgp_session_state{state="ESTABLISHED"}
```

### 3. Vendor Tag Detection

The `add_vendor_tags` processor automatically detects Arista devices and adds appropriate labels:

#### Detection Logic

Arista devices are detected by checking if the `source` label contains:
- `arista` - Device name contains "arista"
- `eos` - Device name contains "eos"

#### Tags Added

For Arista devices:
- `vendor="arista"` - Vendor identification
- `os="eos"` - Operating system identification
- `universal_metric="true"` - For normalized metrics (network_*)
- `vendor_metric="true"` - For vendor-specific metrics

#### Example

```promql
# Query all Arista devices
network_interface_in_octets{vendor="arista"}

# Query specific Arista device
network_interface_in_octets{vendor="arista",source="arista-spine1"}

# Compare SR Linux vs Arista
sum(rate(network_interface_in_octets[5m])) by (vendor)
```

## Validation

### Test Interface Normalization

```bash
# Query Prometheus to verify interface metrics are normalized
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="arista"}' | jq

# Expected: Metrics with interface labels like eth1_1, eth1_0, etc.
```

### Test BGP Normalization

```bash
# Query Prometheus to verify BGP metrics are normalized
curl -s 'http://localhost:9090/api/v1/query?query=network_bgp_session_state{vendor="arista"}' | jq

# Expected: Metrics with state values like ESTABLISHED, IDLE, etc.
```

### Test Universal Queries

```bash
# Query that works for both SR Linux and Arista
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{interface="eth1_1"}' | jq

# Expected: Metrics from both vendors with same interface name format
```

## Grafana Dashboard Queries

### Universal Interface Traffic

```promql
# Total traffic across all vendors
sum(rate(network_interface_in_octets[5m]) * 8) by (source, interface)

# Traffic by vendor
sum(rate(network_interface_in_octets[5m]) * 8) by (vendor)

# Arista-specific traffic
sum(rate(network_interface_in_octets{vendor="arista"}[5m]) * 8) by (source, interface)
```

### Universal BGP Monitoring

```promql
# Count established BGP sessions across all vendors
count(network_bgp_session_state{state="ESTABLISHED"})

# BGP sessions by vendor
count(network_bgp_session_state) by (vendor, state)

# Arista BGP sessions
count(network_bgp_session_state{vendor="arista"}) by (state)
```

## Comparison with SR Linux

### Path Differences

| Metric | SR Linux Path | Arista Path | Normalized Name |
|--------|---------------|-------------|-----------------|
| Interface In Octets | `/interface/statistics/in-octets` | `/interfaces/interface/state/counters/in-octets` | `network_interface_in_octets` |
| BGP Session State | `/network-instance/protocols/bgp/neighbor/session-state` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` | `network_bgp_session_state` |

### Interface Name Differences

| Vendor | Native Format | Normalized Format |
|--------|---------------|-------------------|
| SR Linux | `ethernet-1/1` | `eth1_1` |
| Arista | `Ethernet1/1` | `eth1_1` |
| Arista | `Ethernet1` | `eth1_0` |

### Key Observations

1. **OpenConfig Support**: Arista has excellent OpenConfig support, making normalization straightforward
2. **Path Structure**: Arista uses longer OpenConfig paths compared to SR Linux's native paths
3. **Interface Naming**: Arista supports both modular (`Ethernet1/1`) and fixed (`Ethernet1`) formats
4. **Consistency**: After normalization, metrics from both vendors are identical in structure

## Troubleshooting

### Metrics Not Appearing

**Symptom**: No Arista metrics in Prometheus

**Possible Causes**:
1. Arista devices not added to gNMIc targets
2. gNMI not enabled on Arista devices
3. OpenConfig not enabled on Arista devices

**Solutions**:
```bash
# Check gNMIc is collecting from Arista
docker logs gnmic 2>&1 | grep -i arista

# Verify Arista device is reachable
gnmic -a arista-spine1:6030 --insecure capabilities

# Check OpenConfig is enabled on Arista
# On Arista CLI:
show management api gnmi
```

### Interface Names Not Normalized

**Symptom**: Interface labels still show `Ethernet1/1` instead of `eth1_1`

**Possible Causes**:
1. Processor not applied to output
2. Label name mismatch (interface vs interface_name)
3. Regex pattern doesn't match

**Solutions**:
```bash
# Check which label contains interface name
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="arista"}' | jq '.data.result[0].metric'

# Verify processor is applied
docker logs gnmic 2>&1 | grep -i "normalize_interface"
```

### Vendor Tag Not Applied

**Symptom**: Arista metrics don't have `vendor="arista"` label

**Possible Causes**:
1. Device name doesn't contain "arista" or "eos"
2. Processor condition doesn't match
3. Processor order incorrect

**Solutions**:
```yaml
# Update add_vendor_tags processor condition to match your device names
- event-add-tag:
    tag-name: vendor
    value: "arista"
    condition: 'contains(source, "your-device-prefix")'
```

## Next Steps

After configuring Arista normalization:

1. **Add SONiC normalization** (Task 15.3) - Transform SONiC metrics
2. **Add Juniper normalization** (Task 15.4) - Transform Juniper metrics
3. **Create universal dashboards** - Build Grafana dashboards using normalized metrics
4. **Test multi-vendor queries** - Verify queries work across all vendors

## References

- [Arista OpenConfig Support](https://www.arista.com/en/um-eos/eos-openconfig)
- [gNMIc Event Processors](https://gnmic.openconfig.net/user_guide/event_processors/intro/)
- [OpenConfig Interface Model](https://github.com/openconfig/public/tree/master/release/models/interfaces)
- [OpenConfig BGP Model](https://github.com/openconfig/public/tree/master/release/models/bgp)
- `transformation-rules.yml` - Complete transformation rules documentation
- `normalization-mappings.yml` - Vendor path mapping reference
- `SR-LINUX-NORMALIZATION.md` - SR Linux normalization documentation
