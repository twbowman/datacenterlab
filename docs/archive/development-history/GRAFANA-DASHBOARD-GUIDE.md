# Grafana Dashboard Guide

## Network Interface Performance Dashboard

A comprehensive dashboard for monitoring network interface performance, utilization, and identifying load balancing issues.

## Features

The dashboard includes the following panels:

### 1. Interface Throughput (All Devices)
- Real-time line graph showing IN/OUT traffic for all interfaces
- Displays traffic in bits per second (bps)
- Shows mean and max values in legend

### 2. Link Utilization (%)
- Horizontal bar gauge showing current utilization percentage
- Color-coded thresholds:
  - Green: 0-50%
  - Yellow: 50-70%
  - Orange: 70-80%
  - Red: >80%

### 3. Link Utilization Over Time
- Time series graph showing utilization trends
- Helps identify traffic patterns and peak usage times
- 80% threshold line for quick identification of overutilized links

### 4. Spine1 & Spine2 Interface Throughput
- Individual gauge panels for each spine switch
- Quick visual indication of per-interface load
- Color-coded based on throughput thresholds

### 5. Traffic Distribution by Device
- Pie chart showing traffic distribution across all devices
- Helps identify which devices are handling the most traffic

### 6. Link Utilization Heatmap
- Visual heatmap showing utilization patterns over time
- Quickly identify which links are consistently busy or idle
- Color intensity indicates utilization level

### 7. Packet Rate (OUT)
- Packets per second for all interfaces
- Useful for identifying small packet attacks or unusual traffic patterns

### 8. Interface Errors and Discards
- Monitors interface errors and packet discards
- Critical for identifying link quality issues
- Should normally be zero or very low

## Accessing the Dashboard

### Option 1: Auto-loaded (Recommended)
The dashboard is automatically provisioned when you start the monitoring stack:

```bash
# Start monitoring
./lab mon-start

# Wait 10 seconds for Grafana to start
sleep 10

# Open Grafana
./lab grafana
# Or manually: http://localhost:3000
```

Login credentials:
- Username: `admin`
- Password: `admin`

Navigate to: **Dashboards → Network → Network Interface Performance**

### Option 2: Manual Import
If the dashboard isn't auto-loaded, you can import it manually:

1. Open Grafana: http://localhost:3000
2. Login (admin/admin)
3. Click **Dashboards** → **Import**
4. Click **Upload JSON file**
5. Select: `monitoring/grafana/provisioning/dashboards/interface-performance.json`
6. Click **Import**

## Using the Dashboard

### Identifying Overutilized Links

Look for:
- Red bars in the "Link Utilization (%)" panel (>80%)
- Lines crossing the 80% threshold in "Link Utilization Over Time"
- Red gauges in the spine interface panels

**Action**: Consider adding capacity or redistributing traffic

### Identifying Underutilized Links

Look for:
- Green bars consistently below 10% in utilization panels
- Flat lines near zero in throughput graphs

**Possible causes**:
- ECMP not working properly
- Backup path (expected)
- Misconfigured routing

### Detecting Load Balancing Issues

Compare parallel paths:
- Check if spine1 and spine2 have similar utilization
- Look at the heatmap for consistent patterns
- Compare interface-1/1 across all leafs

**Signs of imbalance**:
- One spine significantly busier than the other
- Uneven distribution in the pie chart
- Different colors in heatmap for parallel paths

### Monitoring Interface Health

Check the "Interface Errors and Discards" panel:
- Should be zero or very low
- Spikes indicate:
  - Physical layer issues
  - Buffer overruns
  - Congestion

## Dashboard Customization

### Adjusting Time Range
- Use the time picker in the top right
- Default: Last 15 minutes
- Recommended for troubleshooting: Last 1 hour

### Changing Refresh Rate
- Default: 10 seconds
- Click the refresh dropdown to change
- Options: 5s, 10s, 30s, 1m, 5m

### Modifying Thresholds
Edit any panel to adjust thresholds:
1. Click panel title → Edit
2. Go to "Thresholds" section
3. Adjust values (default: 50%, 70%, 80%)
4. Save dashboard

### Adding Filters
You can add template variables to filter by device:
1. Dashboard settings → Variables
2. Add new variable
3. Query: `label_values(gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets, exported_source)`
4. Use in queries: `{exported_source="$device"}`

## Troubleshooting

### No Data Showing

**Check monitoring stack**:
```bash
./lab status
```

**Verify gNMIc is collecting**:
```bash
curl -s http://172.20.20.5:9273/metrics | grep interface_statistics | head -5
```

**Check Prometheus is scraping**:
```bash
curl -s http://172.20.20.3:9090/api/v1/targets
```

### Dashboard Not Loading

**Restart Grafana**:
```bash
orb -m clab docker restart clab-monitoring-grafana
```

**Check Grafana logs**:
```bash
orb -m clab docker logs clab-monitoring-grafana --tail 50
```

### Metrics Have Wrong Names

The dashboard expects metrics with this format:
- `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets`
- `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_in_octets`

If your metrics have different names, edit the queries in each panel.

## Integration with Python Analysis Tool

The dashboard complements the Python link analysis tool:

**Dashboard**: Real-time visual monitoring
- Continuous monitoring
- Historical trends
- Quick visual identification

**Python Tool**: Detailed analysis and reporting
- Point-in-time analysis
- Detailed recommendations
- Automation-friendly (exit codes)
- Text-based reports

**Workflow**:
1. Use dashboard for continuous monitoring
2. Run Python tool when issues are detected
3. Use Python tool's recommendations for remediation
4. Monitor dashboard to verify fixes

## Exporting Dashboard

To share or backup the dashboard:

1. Open the dashboard
2. Click the share icon (top right)
3. Click "Export"
4. Choose "Save to file"
5. Save as JSON

## Advanced: Creating Alerts

You can create alerts based on dashboard panels:

1. Edit a panel (e.g., "Link Utilization Over Time")
2. Go to "Alert" tab
3. Create alert rule:
   - Condition: `WHEN avg() OF query(A, 5m, now) IS ABOVE 80`
   - Evaluate every: 1m
   - For: 5m
4. Add notification channel (email, Slack, PagerDuty, etc.)
5. Save

## Related Documentation

- `LINK-UTILIZATION-TESTING.md` - Testing guide for Python analysis tool
- `QUICK-START-LINK-ANALYSIS.md` - Quick start for link analysis
- `analyze-link-utilization.py` - Python analysis script
- `monitoring/prometheus/prometheus.yml` - Prometheus configuration
- `monitoring/gnmic/gnmic-config.yml` - gNMIc telemetry configuration

## Dashboard Panels Summary

| Panel | Type | Purpose | Key Metrics |
|-------|------|---------|-------------|
| Interface Throughput | Time Series | Overall traffic trends | bps IN/OUT |
| Link Utilization (%) | Bar Gauge | Current utilization | % of 10G capacity |
| Link Utilization Over Time | Time Series | Historical utilization | % over time |
| Spine Interface Throughput | Gauge | Per-spine monitoring | bps per interface |
| Traffic Distribution | Pie Chart | Load distribution | Traffic by device |
| Link Utilization Heatmap | Status History | Pattern identification | Utilization patterns |
| Packet Rate | Time Series | Packet-level analysis | pps |
| Errors and Discards | Time Series | Link health | Errors/discards rate |

## Tips for Production Use

1. **Set up alerts** for utilization >80% for 5+ minutes
2. **Create snapshots** before/after changes for comparison
3. **Use annotations** to mark network changes or incidents
4. **Export reports** regularly for capacity planning
5. **Create custom views** for different teams (NOC, Engineering, Management)
6. **Link to runbooks** in panel descriptions for common issues
7. **Set up Grafana authentication** (LDAP, OAuth) for production
8. **Enable dashboard versioning** to track changes
9. **Create playlists** for NOC displays cycling through dashboards
10. **Use Grafana's API** to automate dashboard management
