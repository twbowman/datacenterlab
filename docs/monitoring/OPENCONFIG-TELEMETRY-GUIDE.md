# OpenConfig Telemetry Multi-Vendor Guide

## Overview

This guide covers collecting telemetry using OpenConfig models across multiple vendors. OpenConfig is much better supported for telemetry (read/subscribe) than configuration (write).

## Vendor Support Matrix

### Interface Statistics (Best Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| `/interfaces/interface/state/counters` | ✅ Full | ✅ Full | ✅ Full | Universal support |
| `/interfaces/interface/state/oper-status` | ✅ Full | ✅ Full | ✅ Full | Universal support |
| `/interfaces/interface/state/admin-status` | ✅ Full | ✅ Full | ✅ Full | Universal support |

### BGP State (Good Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| `/network-instances/.../bgp/neighbors/neighbor/state` | ⚠️ Partial | ✅ Full | ⚠️ Partial | Check AFI/SAFI support |
| `/network-instances/.../bgp/global/state` | ⚠️ Partial | ✅ Full | ⚠️ Partial | Basic state works |
| `/network-instances/.../bgp/rib` | ❌ Limited | ✅ Full | ❌ Limited | Arista best support |

### LLDP (Good Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| `/lldp/interfaces/interface/neighbors` | ✅ Full | ✅ Full | ✅ Full | Universal support |

### System Info (Good Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| `/system/state` | ✅ Full | ✅ Full | ✅ Full | Basic info works |
| `/components/component/state` | ⚠️ Partial | ✅ Full | ⚠️ Partial | Hardware details vary |

### OSPF/ISIS (Limited Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| `/network-instances/.../ospf` | ❌ Use native | ⚠️ Partial | ❌ Use native | Poor OC support |
| `/network-instances/.../isis` | ❌ Use native | ⚠️ Partial | ❌ Use native | Poor OC support |

### EVPN/VXLAN (Poor Support)

| Path | SR Linux | Arista EOS | SONiC | Notes |
|------|----------|------------|-------|-------|
| OpenConfig EVPN paths | ❌ Use native | ❌ Use native | ❌ Use native | Use vendor models |

## Recommended Strategy

### Use OpenConfig For:
1. **Interface statistics** - Universal support, works everywhere
2. **Basic BGP state** - Neighbor status, session state
3. **LLDP** - Topology discovery
4. **System info** - Hostname, uptime, basic hardware

### Use Native Models For:
1. **EVPN/VXLAN** - Poor OpenConfig support
2. **Advanced routing** - OSPF/ISIS details
3. **Vendor-specific features** - QoS, ACLs, platform features
4. **Detailed RIB/FIB** - Routing table details

## Configuration Examples

### Pure OpenConfig (Maximum Compatibility)

```yaml
# gnmic-config-openconfig.yml
subscriptions:
  oc_interfaces:
    paths:
      - /interfaces/interface/state/counters
      - /interfaces/interface/state/oper-status
    mode: stream
    stream-mode: sample
    sample-interval: 10s

  oc_bgp_basic:
    paths:
      - /network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state
      - /network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/established-transitions
    mode: stream
    stream-mode: sample
    sample-interval: 30s
```

### Hybrid Approach (OpenConfig + Native)

```yaml
# gnmic-config-hybrid.yml
subscriptions:
  # OpenConfig for common metrics
  oc_interfaces:
    paths:
      - /interfaces/interface/state/counters
    mode: stream
    stream-mode: sample
    sample-interval: 10s

  # SR Linux native for EVPN
  srl_evpn:
    paths:
      - /network-instance[name=*]/protocols/bgp-evpn
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - spine1
      - leaf1

  # Arista native for EVPN
  eos_evpn:
    paths:
      - /Sysdb/l2/evpn
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - spine2
      - leaf2
```

### Per-Vendor Subscriptions

```yaml
# Target-specific subscriptions
subscriptions:
  # OpenConfig - all devices
  oc_interfaces:
    paths:
      - /interfaces/interface/state/counters
    mode: stream
    stream-mode: sample
    sample-interval: 10s

  # SR Linux specific
  srl_native:
    paths:
      - /network-instance[name=default]/protocols/bgp
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - spine1
      - leaf1

  # Arista specific
  eos_native:
    paths:
      - /Sysdb/routing/bgp
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - spine2
      - leaf2
```

## Testing OpenConfig Support

### 1. Check Capabilities

```bash
# SR Linux
gnmic -a spine1:57400 -u admin -p NokiaSrl1! --insecure capabilities

# Arista EOS
gnmic -a spine2:6030 -u admin -p admin --insecure capabilities

# Look for OpenConfig models in supported-models
```

### 2. Test Interface Stats (Should Work Everywhere)

```bash
# Test OpenConfig interfaces
gnmic -a spine1:57400 -u admin -p NokiaSrl1! --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/counters"

# Arista (adjust interface name)
gnmic -a spine2:6030 -u admin -p admin --insecure \
  get --path "/interfaces/interface[name=Ethernet1]/state/counters"
```

### 3. Test BGP State

```bash
# OpenConfig BGP neighbor state
gnmic -a spine1:57400 -u admin -p NokiaSrl1! --insecure \
  get --path "/network-instances/network-instance[name=default]/protocols/protocol[name=bgp]/bgp/neighbors"
```

### 4. Subscribe to Telemetry

```bash
# Test subscription
gnmic -a spine1:57400 -u admin -p NokiaSrl1! --insecure \
  subscribe --path "/interfaces/interface/state/counters" \
  --stream-mode sample --sample-interval 10s
```

## Grafana Dashboard Considerations

When using OpenConfig telemetry with multiple vendors:

### 1. Normalize Metric Names

```yaml
# In gNMIc config
processors:
  normalize_interfaces:
    event-processors:
      - event-strings:
          value-names:
            - "^interface_name$"
          transforms:
            - replace:
                apply-on: "value"
                old: "ethernet-"
                new: "Ethernet"
```

### 2. Add Vendor Tags

```yaml
targets:
  spine1:
    address: spine1:57400
    tags:
      vendor: nokia
      os: srlinux
      
  spine2:
    address: spine2:6030
    tags:
      vendor: arista
      os: eos
```

### 3. Create Vendor-Agnostic Queries

```promql
# Works across vendors
rate(gnmic_interfaces_interface_state_counters_in_octets[5m])

# Filter by vendor
rate(gnmic_interfaces_interface_state_counters_in_octets{vendor="nokia"}[5m])
```

## Migration Path

### Phase 1: Start with OpenConfig
- Deploy OpenConfig for interfaces, basic BGP
- Validate metrics across all vendors
- Build initial dashboards

### Phase 2: Add Native for Gaps
- Identify missing metrics (EVPN, advanced routing)
- Add vendor-specific subscriptions
- Update dashboards with vendor-specific panels

### Phase 3: Optimize
- Remove duplicate metrics
- Consolidate dashboards
- Document vendor differences

## Common Issues

### Issue: Path Not Found

**Symptom**: `path not found` or `unsupported path`

**Solution**: 
1. Check vendor capabilities
2. Try native model path
3. Verify OpenConfig version support

### Issue: Different Data Structures

**Symptom**: Same path returns different JSON structure

**Solution**:
1. Use gNMIc processors to normalize
2. Create vendor-specific Grafana queries
3. Document differences

### Issue: Missing Metrics

**Symptom**: Some vendors return data, others don't

**Solution**:
1. Check OpenConfig model version
2. Use hybrid approach (OC + native)
3. Accept vendor limitations

## Best Practices

1. **Start Simple**: Begin with interface stats (universal support)
2. **Test Per Vendor**: Validate each path on each vendor
3. **Use Hybrid**: OpenConfig where possible, native where needed
4. **Tag Everything**: Add vendor/os tags for filtering
5. **Document Gaps**: Note what works and what doesn't
6. **Version Lock**: Pin OpenConfig model versions
7. **Monitor Coverage**: Track which metrics come from OC vs native

## Reference

- OpenConfig Models: https://github.com/openconfig/public
- gNMIc Documentation: https://gnmic.openconfig.net
- Arista OpenConfig Support: https://aristanetworks.github.io/openmgmt/
- SR Linux YANG Browser: https://yang.srlinux.dev
