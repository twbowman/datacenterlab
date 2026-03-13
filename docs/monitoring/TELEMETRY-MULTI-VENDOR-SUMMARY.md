# Multi-Vendor Telemetry with OpenConfig

## Summary

Your telemetry stack now uses OpenConfig models where they're well-supported, with fallback to native models for vendor-specific features.

## What Changed

### 1. Updated gNMIc Configuration

**File**: `monitoring/gnmic/gnmic-config.yml`

**Changes**:
- ✅ Interface stats now use OpenConfig paths (universal support)
- ✅ BGP basic state uses OpenConfig (works across vendors)
- ✅ Added OpenConfig LLDP subscription
- ⚠️ Kept SR Linux native for OSPF (poor OpenConfig support)
- ⚠️ Kept SR Linux native for detailed BGP/EVPN

### 2. New Files Created

- `gnmic-config-openconfig.yml` - Pure OpenConfig example for multi-vendor
- `OPENCONFIG-TELEMETRY-GUIDE.md` - Comprehensive vendor support matrix
- `test-openconfig-telemetry.sh` - Script to validate OpenConfig support

## OpenConfig vs Native Decision Matrix

| Metric Type | Use OpenConfig? | Reason |
|-------------|----------------|---------|
| Interface counters | ✅ Yes | Universal support, works everywhere |
| Interface status | ✅ Yes | Universal support |
| LLDP neighbors | ✅ Yes | Good cross-vendor support |
| Basic BGP state | ✅ Yes | Session state, neighbor status work well |
| OSPF details | ❌ No | Poor OpenConfig support, use native |
| EVPN/VXLAN | ❌ No | Not in OpenConfig, use native |
| Advanced BGP (RIB) | ⚠️ Mixed | Basic works, details need native |

## Current Configuration Strategy

```yaml
# OpenConfig for common metrics (works on SR Linux, Arista, SONiC)
oc_interface_stats:
  paths:
    - /interfaces/interface/state/counters  # ✅ Universal
    - /interfaces/interface/state/oper-status  # ✅ Universal

oc_bgp_neighbors:
  paths:
    - /network-instances/.../bgp/neighbors/neighbor/state  # ✅ Good support

# Native models for vendor-specific features
srl_ospf_state:
  paths:
    - /network-instance[name=default]/protocols/ospf  # SR Linux native

srl_bgp_detailed:
  paths:
    - /network-instance[name=default]/protocols/bgp  # SR Linux native (includes EVPN)
```

## Testing OpenConfig Support

### Quick Test

```bash
# Run the test script
cd monitoring
./test-openconfig-telemetry.sh
```

### Manual Testing

```bash
# Test OpenConfig interface stats
gnmic -a clab-gnmi-clos-spine1:57400 -u admin -p NokiaSrl1! --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/counters"

# Test OpenConfig BGP
gnmic -a clab-gnmi-clos-spine1:57400 -u admin -p NokiaSrl1! --insecure \
  get --path "/network-instances/network-instance/protocols/protocol/bgp/neighbors"

# Subscribe to OpenConfig telemetry
gnmic -a clab-gnmi-clos-spine1:57400 -u admin -p NokiaSrl1! --insecure \
  subscribe --path "/interfaces/interface/state/counters" \
  --stream-mode sample --sample-interval 10s
```

## Adding New Vendors

When you add Arista or SONiC devices:

### 1. Update gNMIc Targets

```yaml
targets:
  # Existing SR Linux
  spine1:
    address: clab-gnmi-clos-spine1:57400
    username: admin
    password: NokiaSrl1!
    tags:
      vendor: nokia
      os: srlinux

  # New Arista device
  spine2:
    address: 172.20.20.11:6030
    username: admin
    password: admin
    tags:
      vendor: arista
      os: eos
```

### 2. OpenConfig Subscriptions Work Automatically

The OpenConfig subscriptions will automatically work on new vendors:
- `oc_interface_stats` - Works on Arista, SONiC
- `oc_bgp_neighbors` - Works on Arista, SONiC
- `oc_lldp` - Works on Arista, SONiC

### 3. Add Vendor-Specific Subscriptions

```yaml
subscriptions:
  # ... existing OpenConfig subscriptions ...

  # Arista native for EVPN
  eos_evpn:
    paths:
      - /Sysdb/l2/evpn
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - spine2  # Only Arista devices
```

## Grafana Dashboard Impact

### Existing Dashboards

Your current dashboards use SR Linux native paths. They will continue to work.

### New Multi-Vendor Dashboards

Create dashboards using OpenConfig metrics:

```promql
# Interface throughput - works across all vendors
rate(gnmic_interfaces_interface_state_counters_in_octets{interface="ethernet-1/1"}[5m])

# Filter by vendor
rate(gnmic_interfaces_interface_state_counters_in_octets{vendor="nokia"}[5m])
rate(gnmic_interfaces_interface_state_counters_in_octets{vendor="arista"}[5m])

# BGP session state - works across vendors
gnmic_network_instances_network_instance_protocols_protocol_bgp_neighbors_neighbor_state_session_state
```

### Migration Strategy

1. **Phase 1**: Keep existing dashboards (SR Linux native)
2. **Phase 2**: Create new OpenConfig dashboards alongside
3. **Phase 3**: When you add new vendors, they automatically appear in OpenConfig dashboards
4. **Phase 4**: Gradually migrate to OpenConfig dashboards as primary

## Benefits

### ✅ Vendor Agnostic
- Same telemetry paths work on SR Linux, Arista, SONiC
- Add new vendors without changing telemetry config

### ✅ Future Proof
- OpenConfig is industry standard
- Easier to switch vendors

### ✅ Unified Dashboards
- Single dashboard shows all vendors
- Compare metrics across vendors

### ⚠️ Trade-offs
- Some advanced features need native models
- EVPN/VXLAN not in OpenConfig
- May need hybrid approach (OpenConfig + native)

## Next Steps

1. **Test Current Setup**:
   ```bash
   cd monitoring
   ./test-openconfig-telemetry.sh
   ```

2. **Verify Metrics in Prometheus**:
   ```bash
   curl http://localhost:9273/metrics | grep gnmic_interfaces
   ```

3. **Check Grafana**:
   - Existing dashboards should still work (native paths)
   - OpenConfig metrics available for new dashboards

4. **When Adding New Vendors**:
   - Add target to `gnmic-config.yml`
   - OpenConfig subscriptions work automatically
   - Add vendor-specific subscriptions for EVPN/advanced features

## Reference

- OpenConfig Models: https://github.com/openconfig/public
- Vendor Support Guide: `OPENCONFIG-TELEMETRY-GUIDE.md`
- Pure OpenConfig Config: `gnmic-config-openconfig.yml`
- Test Script: `test-openconfig-telemetry.sh`
