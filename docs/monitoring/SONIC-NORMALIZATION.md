# SONiC Metric Normalization Implementation

**Task**: 15.3 Configure SONiC metric normalization  
**Requirements**: 4.1, 4.2, 4.3  
**Status**: Implemented

## Overview

This document describes the SONiC (Dell EMC) metric normalization implementation that transforms vendor-specific telemetry paths into universal OpenConfig-based metric names. This enables cross-vendor monitoring queries and dashboards.

## Implementation Summary

### What Was Configured

1. **Extended `normalize_interface_metrics` processor**
   - Added SONiC OpenConfig path transformations
   - Added SONiC native path transformations (`/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/*`)
   - Extended interface name normalization to handle SONiC naming (Ethernet0 → eth0_0)

2. **Extended `normalize_bgp_metrics` processor**
   - Added SONiC OpenConfig BGP path transformations
   - Added SONiC native BGP path transformations (`/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/*`)

3. **Extended `add_vendor_tags` processor**
   - Added SONiC device detection (matches "sonic" or "dell" in source name)
   - Tags SONiC metrics with `vendor=dellemc` and `os=sonic`

### Files Modified

- `monitoring/gnmic/gnmic-config.yml` - Main gNMIc configuration with processors

### Files Created

- `monitoring/gnmic/validate-sonic-normalization.sh` - Validation script
- `monitoring/gnmic/SONIC-NORMALIZATION.md` - This documentation

## SONiC Path Mappings

### Interface Metrics

| Metric Type | SONiC OpenConfig Path | SONiC Native Path | Normalized Name |
|-------------|----------------------|-------------------|-----------------|
| In Octets | `/interfaces/interface/state/counters/in-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets` | `network_interface_in_octets` |
| Out Octets | `/interfaces/interface/state/counters/out-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets` | `network_interface_out_octets` |
| In Packets | `/interfaces/interface/state/counters/in-pkts` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-pkts` | `network_interface_in_packets` |
| Out Packets | `/interfaces/interface/state/counters/out-pkts` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-pkts` | `network_interface_out_packets` |
| In Errors | `/interfaces/interface/state/counters/in-errors` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-errors` | `network_interface_in_errors` |
| Out Errors | `/interfaces/interface/state/counters/out-errors` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-errors` | `network_interface_out_errors` |

### BGP Metrics

| Metric Type | SONiC OpenConfig Path | SONiC Native Path | Normalized Name |
|-------------|----------------------|-------------------|-----------------|
| Session State | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state` | `network_bgp_session_state` |
| Established Transitions | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/established-transitions` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/established-transitions` | `network_bgp_established_transitions` |
| Received Routes | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/received` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/received-routes` | `network_bgp_received_routes` |
| Sent Routes | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/sent` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/sent-routes` | `network_bgp_sent_routes` |

### Interface Name Normalization

SONiC uses a simple interface naming convention that needs to be normalized:

| SONiC Interface Name | Normalized Name | Pattern |
|---------------------|-----------------|---------|
| Ethernet0 | eth0_0 | `Ethernet(\d+)` → `eth${1}_0` |
| Ethernet1 | eth1_0 | `Ethernet(\d+)` → `eth${1}_0` |
| Ethernet48 | eth48_0 | `Ethernet(\d+)` → `eth${1}_0` |

**Note**: SONiC typically uses single-number interface names (Ethernet0, Ethernet1, etc.) unlike Arista which may use Ethernet1/1 format.

## Processor Configuration Details

### 1. Interface Metrics Normalization

The `normalize_interface_metrics` processor was extended with SONiC-specific transformations:

```yaml
processors:
  normalize_interface_metrics:
    event-processors:
      # SONiC native interface counters
      - event-convert:
          value-names:
            - "^/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets"
                new: "network_interface_in_octets"
      
      # ... (similar for other counters)
      
      # Interface name normalization
      - event-convert:
          tag-names:
            - "interface_name"
            - "interface"
          transforms:
            # SONiC: Ethernet0 -> eth0_0
            - replace:
                apply-on: "value"
                old: "^Ethernet(\\d+)$"
                new: "eth${1}_0"
```

**Key Points**:
- Handles both OpenConfig and SONiC native paths
- OpenConfig paths are shared with Arista (already configured)
- Native paths provide fallback for SONiC-specific implementations
- Interface name regex matches single-number format (Ethernet0, not Ethernet0/1)

### 2. BGP Metrics Normalization

The `normalize_bgp_metrics` processor was extended with SONiC-specific transformations:

```yaml
processors:
  normalize_bgp_metrics:
    event-processors:
      # SONiC native BGP session state
      - event-convert:
          value-names:
            - "^/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state"
                new: "network_bgp_session_state"
      
      # ... (similar for other BGP metrics)
```

**Key Points**:
- Handles both OpenConfig and SONiC native BGP paths
- OpenConfig paths are shared with Arista and Juniper
- Native paths provide access to SONiC-specific BGP features
- State values are normalized to uppercase (ESTABLISHED, IDLE, etc.)

### 3. Vendor Tag Detection

The `add_vendor_tags` processor was extended to detect SONiC devices:

```yaml
processors:
  add_vendor_tags:
    event-processors:
      # Detect and tag SONiC devices (Dell EMC)
      - event-add-tag:
          tag-name: vendor
          value: "dellemc"
          condition: 'contains(source, "sonic") || contains(source, "dell")'
      
      - event-add-tag:
          tag-name: os
          value: "sonic"
          condition: 'contains(source, "sonic") || contains(source, "dell")'
```

**Key Points**:
- Detects SONiC devices by checking if source name contains "sonic" or "dell"
- Tags with `vendor=dellemc` (Dell EMC is the primary SONiC vendor)
- Tags with `os=sonic` for OS identification
- Enables vendor-specific filtering in Grafana queries

## Validation

### Running the Validation Script

```bash
# Make sure Prometheus and gNMIc are running
./monitoring/gnmic/validate-sonic-normalization.sh
```

The validation script checks:

1. **Prometheus connectivity** - Ensures Prometheus is accessible
2. **gNMIc metrics endpoint** - Verifies gNMIc is exporting metrics
3. **Normalized interface metrics** - Checks for `network_interface_*` metrics from SONiC
4. **Normalized BGP metrics** - Checks for `network_bgp_*` metrics from SONiC
5. **Interface name normalization** - Verifies Ethernet0 → eth0_0 transformation
6. **Vendor tags** - Confirms `vendor=dellemc` and `os=sonic` tags are present
7. **Universal metric tags** - Checks `universal_metric=true` tag
8. **Cross-vendor consistency** - Compares metrics across Nokia, Arista, and SONiC
9. **Path transformation** - Ensures native paths are transformed

### Manual Validation Queries

#### Check SONiC Interface Metrics

```bash
# Query Prometheus for SONiC interface metrics
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="dellemc"}' | jq

# Expected: Metrics with vendor=dellemc, os=sonic, interface=eth0_0, etc.
```

#### Check SONiC BGP Metrics

```bash
# Query Prometheus for SONiC BGP metrics
curl -s 'http://localhost:9090/api/v1/query?query=network_bgp_session_state{vendor="dellemc"}' | jq

# Expected: BGP session state metrics with SONiC vendor tags
```

#### Check Interface Name Normalization

```bash
# Check gNMIc metrics directly
curl -s http://localhost:9273/metrics | grep 'network_interface_in_octets.*dellemc'

# Expected: interface="eth0_0", interface="eth1_0", etc. (not Ethernet0, Ethernet1)
```

#### Universal Query Test

```bash
# Query that works across all vendors
curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets' | jq

# Expected: Metrics from Nokia (vendor=nokia), Arista (vendor=arista), and SONiC (vendor=dellemc)
```

## Universal Grafana Queries

With SONiC normalization in place, these queries work across all vendors:

### Interface Bandwidth (All Vendors)

```promql
# Bits per second, all vendors
rate(network_interface_in_octets[5m]) * 8
```

### Interface Bandwidth (SONiC Only)

```promql
# Bits per second, SONiC devices only
rate(network_interface_in_octets{vendor="dellemc"}[5m]) * 8
```

### BGP Session Status (All Vendors)

```promql
# Count established BGP sessions across all vendors
count(network_bgp_session_state == 6) by (source, vendor)
```

### BGP Session Status (SONiC Only)

```promql
# SONiC BGP sessions
network_bgp_session_state{vendor="dellemc"}
```

### Interface Errors (Multi-Vendor Comparison)

```promql
# Compare error rates across vendors
sum(rate(network_interface_in_errors[5m])) by (vendor)
```

### Top Interfaces by Traffic (SONiC)

```promql
# Top 10 SONiC interfaces by traffic
topk(10, rate(network_interface_in_octets{vendor="dellemc"}[5m]) * 8)
```

## SONiC-Specific Considerations

### OpenConfig Support

SONiC has **good OpenConfig support** for basic metrics:
- ✅ Interface counters - Excellent support
- ✅ BGP basic state - Good support
- ⚠️ OSPF - Limited support (use native paths)
- ⚠️ Advanced features - May require native paths

**Recommendation**: Use OpenConfig paths where available, fall back to native paths for advanced features.

### Native Path Support

SONiC native paths are included for completeness and fallback:
- `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/*` - Interface statistics
- `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/*` - BGP neighbor state
- `/sonic-ospf:sonic-ospf/OSPF/*` - OSPF state (limited OpenConfig support)

### Interface Naming

SONiC uses simple numeric interface names:
- **Format**: Ethernet0, Ethernet1, Ethernet48
- **Normalized**: eth0_0, eth1_0, eth48_0
- **Pattern**: Single number (no slash notation like Arista's Ethernet1/1)

### Vendor Identification

SONiC devices are identified by:
- **Vendor tag**: `dellemc` (Dell EMC is the primary SONiC vendor)
- **OS tag**: `sonic`
- **Detection**: Source name contains "sonic" or "dell"

**Note**: If using SONiC from other vendors (Microsoft, Alibaba, etc.), you may need to adjust the detection logic.

## Testing with SONiC Devices

### Prerequisites

1. SONiC device deployed in containerlab topology
2. gNMI enabled on SONiC device
3. gNMIc configured to collect from SONiC device
4. Prometheus scraping gNMIc metrics

### Deployment Example

```yaml
# topology.yml
name: sonic-test
topology:
  nodes:
    sonic-leaf1:
      kind: sonic
      image: docker-sonic-vs:latest
      mgmt_ipv4: 172.20.20.31
```

### gNMIc Target Configuration

```yaml
# gnmic-config.yml
targets:
  sonic-leaf1:
    address: clab-sonic-test-sonic-leaf1:8080
    username: admin
    password: admin
    skip-verify: true
    subscriptions:
      - oc_interface_stats
      - oc_bgp_neighbors
```

### Verification Steps

1. **Deploy SONiC device**:
   ```bash
   sudo containerlab deploy -t topology.yml
   ```

2. **Verify gNMI connectivity**:
   ```bash
   gnmic -a sonic-leaf1:8080 -u admin -p admin --insecure capabilities
   ```

3. **Check metrics in Prometheus**:
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=network_interface_in_octets{vendor="dellemc"}' | jq
   ```

4. **Run validation script**:
   ```bash
   ./monitoring/gnmic/validate-sonic-normalization.sh
   ```

## Troubleshooting

### No SONiC Metrics Appearing

**Symptoms**: Validation script shows no SONiC metrics

**Possible Causes**:
1. No SONiC devices deployed
2. gNMI not enabled on SONiC device
3. gNMIc not configured to collect from SONiC
4. Network connectivity issues

**Solutions**:
```bash
# Check if SONiC container is running
docker ps | grep sonic

# Test gNMI connectivity
gnmic -a sonic-leaf1:8080 -u admin -p admin --insecure capabilities

# Check gNMIc logs
docker logs clab-monitoring-gnmic

# Verify gNMIc target configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 5 sonic
```

### Interface Names Not Normalized

**Symptoms**: Interface labels still show "Ethernet0" instead of "eth0_0"

**Possible Causes**:
1. Processor not applied to output
2. Label name mismatch (interface vs interface_name)
3. Regex pattern doesn't match

**Solutions**:
```bash
# Check raw gNMIc metrics
curl -s http://localhost:9273/metrics | grep interface_name

# Verify processor configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 20 "normalize_interface_metrics"

# Check if processors are applied to output
cat monitoring/gnmic/gnmic-config.yml | grep -A 10 "outputs:"
```

### Vendor Tags Missing

**Symptoms**: SONiC metrics don't have vendor=dellemc tag

**Possible Causes**:
1. Device name doesn't contain "sonic" or "dell"
2. Processor not applied
3. Condition logic incorrect

**Solutions**:
```bash
# Check device source name in metrics
curl -s http://localhost:9273/metrics | grep network_interface | grep -v "#"

# Verify vendor tag processor
cat monitoring/gnmic/gnmic-config.yml | grep -A 10 "add_vendor_tags"

# Test condition manually
# If source name is "leaf1" instead of "sonic-leaf1", update the condition
```

### BGP Metrics Not Appearing

**Symptoms**: No network_bgp_* metrics for SONiC

**Possible Causes**:
1. BGP not configured on SONiC device
2. gNMIc not subscribed to BGP paths
3. OpenConfig BGP not supported on this SONiC version

**Solutions**:
```bash
# Check if BGP is running on SONiC
docker exec clab-sonic-test-sonic-leaf1 vtysh -c "show bgp summary"

# Test BGP path subscription
gnmic -a sonic-leaf1:8080 -u admin -p admin --insecure \
  get --path "/network-instances/network-instance/protocols/protocol/bgp/neighbors"

# Try native SONiC BGP path
gnmic -a sonic-leaf1:8080 -u admin -p admin --insecure \
  get --path "/sonic-bgp:sonic-bgp/BGP_NEIGHBOR"
```

## Integration with Existing Normalization

SONiC normalization integrates seamlessly with existing SR Linux and Arista normalization:

### Shared OpenConfig Paths

SONiC shares OpenConfig paths with Arista:
- `/interfaces/interface/state/counters/*` - Interface metrics
- `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/*` - BGP metrics

These paths are already configured in the processors, so SONiC automatically benefits from them.

### Shared Interface Name Normalization

The interface name normalization regex `^Ethernet(\d+)$` → `eth${1}_0` works for both:
- **Arista**: Ethernet1 → eth1_0
- **SONiC**: Ethernet0 → eth0_0

### Vendor-Specific Paths

SONiC native paths are added alongside SR Linux and Arista native paths:
- **SR Linux**: `/interface/statistics/*`
- **Arista**: `/Sysdb/interface/counter/*`
- **SONiC**: `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/*`

All transform to the same normalized names: `network_interface_*`

## Requirements Validation

### Requirement 4.1: Transform vendor-specific metric names to OpenConfig paths

✅ **Implemented**: SONiC paths transformed to `network_interface_*` and `network_bgp_*`

**Evidence**:
- Interface metrics: `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets` → `network_interface_in_octets`
- BGP metrics: `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state` → `network_bgp_session_state`

### Requirement 4.2: Transform vendor-specific label names to OpenConfig conventions

✅ **Implemented**: SONiC interface names normalized to universal format

**Evidence**:
- Interface names: Ethernet0 → eth0_0
- Consistent with SR Linux (ethernet-1/1 → eth1_1) and Arista (Ethernet1 → eth1_0)

### Requirement 4.3: Preserve metric values and timestamps during transformation

✅ **Implemented**: Transformations only affect metric names and labels, not values

**Evidence**:
- `apply-on: "name"` - Only transforms metric names
- `apply-on: "value"` - Only transforms label values (interface names)
- Metric values and timestamps pass through unchanged

## Next Steps

After completing SONiC normalization:

1. **Task 15.4**: Configure Juniper metric normalization
   - Add Juniper path transformations
   - Handle Juniper interface naming (ge-0/0/0 → eth0_0_0)
   - Complete multi-vendor normalization

2. **Deploy SONiC devices** to test normalization
   - Add SONiC nodes to topology
   - Configure gNMI on SONiC devices
   - Verify metrics appear in Prometheus

3. **Create universal Grafana dashboards**
   - Build dashboards using normalized metrics
   - Test queries work across Nokia, Arista, and SONiC
   - Add vendor-specific drill-down panels

4. **Performance testing**
   - Measure normalization overhead
   - Test with production-scale metric volumes
   - Optimize processor configuration if needed

## References

- **SONiC gNMI Documentation**: https://github.com/sonic-net/SONiC/blob/master/doc/mgmt/gnmi/SONiC_GNMI_Server_Interface_Design.md
- **SONiC YANG Models**: https://github.com/sonic-net/sonic-buildimage/tree/master/src/sonic-yang-models
- **OpenConfig Models**: https://github.com/openconfig/public
- **gNMIc Event Processors**: https://gnmic.openconfig.net/user_guide/event_processors/intro/
- **Related Files**:
  - `monitoring/gnmic/gnmic-config.yml` - Main configuration
  - `monitoring/gnmic/normalization-mappings.yml` - Path mapping documentation
  - `monitoring/gnmic/transformation-rules.yml` - Transformation rules documentation
  - `monitoring/gnmic/SR-LINUX-NORMALIZATION.md` - SR Linux implementation
  - `monitoring/gnmic/ARISTA-NORMALIZATION.md` - Arista implementation
