# DNS-Based Device Naming - Fix Summary

## Problem
After implementing DNS-based device naming in gNMIc configuration, interface metrics stopped being collected. BGP and OSPF metrics were working correctly with device names (spine1, leaf1, etc.), but interface statistics were missing.

## Root Cause
The interface_stats subscription was using specific leaf paths that weren't working:
```yaml
paths:
  - /interface[name=*]/statistics/out-octets
  - /interface[name=*]/statistics/in-octets
  # ... etc
```

## Solution

### 1. Fixed gNMIc Configuration
Changed the interface_stats subscription to use a broader path:
```yaml
subscriptions:
  interface_stats:
    paths:
      - /interface/statistics
    mode: stream
    stream-mode: sample
    sample-interval: 10s
```

This collects all interface statistics in one subscription instead of individual leaf paths.

### 2. Updated Label Usage
- gNMIc exports metrics with `source="spine1"`, `source="leaf1"`, etc.
- Prometheus scrape config was overriding `source` label
- Metrics are available with `exported_source` label containing device names
- Updated Python script to use `exported_source` instead of `name`
- Updated all Grafana dashboards to use `{{exported_source}}` instead of `{{name}}`

### 3. Files Modified
- `monitoring/gnmic/gnmic-config.yml` - Simplified interface_stats paths
- `monitoring/prometheus/prometheus.yml` - Simplified metric relabeling
- `analyze-link-utilization.py` - Changed from `name` to `exported_source` label
- `monitoring/grafana/provisioning/dashboards/interface-performance.json` - Updated to use `exported_source`
- `monitoring/grafana/provisioning/dashboards/ospf-stability.json` - Updated to use `exported_source`
- `monitoring/grafana/provisioning/dashboards/bgp-stability.json` - Updated to use `exported_source`

## Verification

### Test Python Script
```bash
./lab analyze-links
```

Expected output shows device names correctly:
```
Device          Interface            Gbps       Utilization     Status
--------------------------------------------------------------------------------
leaf1           ethernet-1/1         0.00       0.0           % ℹ️  UNDERUTILIZED
spine1          ethernet-1/1         0.00       0.0           % ℹ️  UNDERUTILIZED
```

### Check Prometheus Metrics
```bash
curl -s http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets | jq '.data.result[0].metric'
```

Should show:
```json
{
  "exported_source": "leaf1",
  "interface_name": "ethernet-1/1",
  ...
}
```

### Check Grafana Dashboards
1. Open Grafana at http://172.20.20.2:3000
2. Navigate to Interface Performance dashboard
3. Verify device names show as spine1, leaf1, etc. (not IP addresses or "gnmic")
4. Check OSPF Stability dashboard
5. Check BGP Stability dashboard

## Current Status
✅ Interface metrics collecting successfully
✅ Device names displaying correctly (spine1, spine2, leaf1-4)
✅ Python analysis script working
✅ All three Grafana dashboards updated
✅ DNS-based naming fully implemented

## Label Reference
- `source` - Overridden by Prometheus scrape config (shows "gnmic")
- `exported_source` - Original source from gNMIc (shows device names: spine1, leaf1, etc.)
- `interface_name` - Interface identifier (ethernet-1/1, etc.)
- `subscription_name` - Subscription type (interface_stats, bgp_state, ospf_state)
