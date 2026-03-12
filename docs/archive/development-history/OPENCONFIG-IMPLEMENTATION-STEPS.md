# OpenConfig Telemetry Implementation Steps

## Quick Implementation

Follow these steps to implement OpenConfig telemetry collection:

### Step 1: Update gNMIc Configuration

The gNMIc config has already been updated to use OpenConfig paths where supported.

**File**: `monitoring/gnmic/gnmic-config.yml`

**What changed**:
- ✅ Interface stats now use OpenConfig paths
- ✅ BGP uses OpenConfig for neighbor state
- ✅ Added OpenConfig LLDP subscription
- ⚠️ Kept native paths for OSPF and detailed BGP/EVPN

### Step 2: Restart gNMIc

If your lab is running, restart gNMIc to pick up the new config:

```bash
# Restart gNMIc container
docker restart clab-gnmi-clos-gnmic

# Wait for it to reconnect
sleep 10
```

### Step 3: Verify OpenConfig Metrics

Check that OpenConfig metrics are being collected:

```bash
# Check Prometheus metrics endpoint
curl http://172.20.20.5:9273/metrics | grep gnmic_interfaces_interface_state

# Should see metrics like:
# gnmic_interfaces_interface_state_counters_in_octets
# gnmic_interfaces_interface_state_counters_out_octets
# gnmic_interfaces_interface_state_oper_status
```

### Step 4: Test OpenConfig Paths Manually

Test OpenConfig paths directly on a device:

```bash
# Test interface counters (OpenConfig)
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/counters"

# Test interface status (OpenConfig)
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status"

# Test LLDP (OpenConfig)
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  get --path "/lldp/interfaces"
```

### Step 5: Run Automated Test

Run the comprehensive test script:

```bash
./test-openconfig-implementation.sh
```

This will:
- Check lab status
- Test OpenConfig paths on all devices
- Verify streaming subscriptions
- Check Prometheus metrics
- Compare OpenConfig vs native paths

## What You Get

### OpenConfig Metrics (Vendor Agnostic)

These metrics will work on SR Linux, Arista EOS, and SONiC:

```
gnmic_interfaces_interface_state_counters_in_octets
gnmic_interfaces_interface_state_counters_out_octets
gnmic_interfaces_interface_state_counters_in_unicast_pkts
gnmic_interfaces_interface_state_counters_out_unicast_pkts
gnmic_interfaces_interface_state_oper_status
gnmic_interfaces_interface_state_admin_status
gnmic_lldp_interfaces_interface_neighbors_neighbor_state_*
```

### Native Metrics (SR Linux Specific)

These metrics use SR Linux native models for features not in OpenConfig:

```
gnmic_network_instance_protocols_ospf_*
gnmic_network_instance_protocols_bgp_* (detailed)
```

## Adding New Vendors

When you add Arista or SONiC devices:

### 1. Add Target to gNMIc Config

Edit `monitoring/gnmic/gnmic-config.yml`:

```yaml
targets:
  # Existing SR Linux devices
  spine1:
    address: clab-gnmi-clos-spine1:57400
    username: admin
    password: NokiaSrl1!

  # Add Arista device
  arista-spine1:
    address: arista-spine1:6030
    username: admin
    password: admin
    tags:
      vendor: arista
      os: eos

  # Add SONiC device
  sonic-leaf1:
    address: sonic-leaf1:8080
    username: admin
    password: admin
    tags:
      vendor: dellemc
      os: sonic
```

### 2. OpenConfig Subscriptions Work Automatically

The existing OpenConfig subscriptions will automatically collect from new vendors:
- `oc_interface_stats` - Works on all vendors
- `oc_bgp_neighbors` - Works on all vendors
- `oc_lldp` - Works on all vendors

### 3. Add Vendor-Specific Subscriptions (Optional)

For vendor-specific features, add targeted subscriptions:

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
      - arista-spine1

  # SONiC native for specific features
  sonic_bgp:
    paths:
      - /sonic-bgp-global:sonic-bgp-global
    mode: stream
    stream-mode: sample
    sample-interval: 30s
    targets:
      - sonic-leaf1
```

### 4. Restart gNMIc

```bash
docker restart clab-gnmi-clos-gnmic
```

## Grafana Dashboards

### Using OpenConfig Metrics

Create vendor-agnostic dashboards using OpenConfig metrics:

```promql
# Interface throughput (works on all vendors)
rate(gnmic_interfaces_interface_state_counters_in_octets[5m]) * 8

# Interface status (works on all vendors)
gnmic_interfaces_interface_state_oper_status

# Filter by vendor
rate(gnmic_interfaces_interface_state_counters_in_octets{vendor="nokia"}[5m])
rate(gnmic_interfaces_interface_state_counters_in_octets{vendor="arista"}[5m])
```

### Existing Dashboards

Your existing dashboards using SR Linux native paths will continue to work.

## Verification Checklist

- [ ] gNMIc config updated with OpenConfig paths
- [ ] gNMIc container restarted
- [ ] OpenConfig metrics visible in Prometheus endpoint
- [ ] Test script passes all OpenConfig path tests
- [ ] Grafana can query OpenConfig metrics
- [ ] Existing native metrics still working

## Troubleshooting

### No OpenConfig Metrics

```bash
# Check gNMIc logs
docker logs clab-gnmi-clos-gnmic

# Verify device supports OpenConfig
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure capabilities | grep openconfig
```

### Path Not Found Errors

Some OpenConfig paths may not be supported. Check the vendor support matrix in `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md`.

### Metrics Not in Prometheus

```bash
# Check gNMIc Prometheus endpoint
curl http://172.20.20.5:9273/metrics | grep gnmic

# Check Prometheus is scraping gNMIc
curl http://172.20.20.3:9090/api/v1/targets
```

## Reference Documentation

- **Vendor Support Matrix**: `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md`
- **Multi-Vendor Summary**: `monitoring/TELEMETRY-MULTI-VENDOR-SUMMARY.md`
- **Pure OpenConfig Config**: `monitoring/gnmic/gnmic-config-openconfig.yml`
- **Test Script**: `monitoring/test-openconfig-telemetry.sh`

## Next Steps

1. Run the test script: `./test-openconfig-implementation.sh`
2. Verify metrics in Grafana: http://localhost:3000
3. Create OpenConfig-based dashboards
4. Add new vendors and test cross-vendor metrics
5. Document any vendor-specific quirks you discover
