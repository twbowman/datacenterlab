# Grafana Dashboard Device Name Fix

## Problem

BGP and OSPF dashboards were showing IP addresses instead of device names (spine1, leaf1, etc.), while the interface dashboard was showing names correctly.

## Root Cause

Grafana had **duplicate dashboard provisioning configurations**:
1. `dashboards.yml` - Network Dashboards provider
2. `default.yml` - Default provider

Both were pointing to the same directory (`/etc/grafana/provisioning/dashboards`), causing Grafana to load each dashboard twice. This created conflicts and prevented proper dashboard updates.

## Solution

### 1. Removed Duplicate Provisioning Config
Deleted `monitoring/grafana/provisioning/dashboards/default.yml` to eliminate the duplicate provider.

### 2. Verified Metrics
Confirmed that Prometheus has correct `exported_source` labels with device names:
```bash
curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_bgp_state_..._session_state' \
  | jq '.data.result[].metric.exported_source'
```

Output:
- "leaf1"
- "leaf2"
- "leaf3"
- "leaf4"
- "spine1"
- "spine2"

### 3. Restarted Grafana
```bash
docker restart clab-monitoring-grafana
```

## Verification

### Check Dashboard Provisioning
```bash
# Should only show dashboards.yml (not default.yml)
docker exec clab-monitoring-grafana ls /etc/grafana/provisioning/dashboards/*.yml

# Check for duplicate warnings (should be none)
docker logs clab-monitoring-grafana 2>&1 | grep -i "duplicate\|same UID"
```

### Access Dashboards
1. Open Grafana: http://172.20.20.2:3000
2. Navigate to dashboards:
   - BGP Stability Monitoring
   - OSPF Stability Monitoring
   - Network Interface Performance
3. Verify device names show as: spine1, spine2, leaf1, leaf2, leaf3, leaf4

## Current Dashboard Configuration

All three dashboards now correctly use `{{exported_source}}` in their legend templates:

### BGP Dashboard
- Query: `gnmic_bgp_state_..._session_state{session_state="established"}`
- Legend: `{{exported_source}} - {{neighbor_peer_address}}`

### OSPF Dashboard
- Query: `gnmic_ospf_state_..._neighbor_adjacency_state`
- Legend: `{{exported_source}} - {{interface_name}}`

### Interface Dashboard
- Query: `rate(gnmic_interface_stats_..._out_octets[5m]) * 8 / 1000000000`
- Legend: `{{exported_source}} - {{interface_name}}`

## Label Flow

1. **gNMIc exports**: `source="spine1"`
2. **Prometheus scrapes**: Adds `exported_source="spine1"` (preserves original)
3. **Prometheus relabels**: `source` becomes "gnmic" (scrape job name)
4. **Dashboards use**: `{{exported_source}}` to display device names

## Files Modified

- ❌ Deleted: `monitoring/grafana/provisioning/dashboards/default.yml`
- ✅ Kept: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- ✅ Updated: All dashboard JSON files use `{{exported_source}}`

## Related Documentation

- `DNS-NAMING-FIX-SUMMARY.md` - Initial DNS naming implementation
- `GRAFANA-DASHBOARD-GUIDE.md` - Dashboard usage guide
- `GRAFANA-TROUBLESHOOTING.md` - Common issues and solutions
