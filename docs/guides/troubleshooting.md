# Grafana Dashboard Troubleshooting

## Current Status

- **Grafana**: Running at http://localhost:3000
- **Prometheus Datasource**: Configured to use http://172.20.20.3:9090
- **Dashboard**: interface-performance.json is provisioned
- **Credentials**: admin/admin

## If Dashboard Shows "No Data"

### Step 1: Verify Datasource Connection

1. Open Grafana: http://localhost:3000
2. Login with admin/admin
3. Go to **Configuration** (gear icon) → **Data Sources**
4. Click on **Prometheus**
5. Scroll to bottom and click **Save & Test**
6. Should show: "Successfully queried the Prometheus API"

If it fails:
- Check the URL is: `http://172.20.20.3:9090`
- Click **Save & Test** again

### Step 2: Test Query Manually

1. Go to **Explore** (compass icon in left sidebar)
2. Make sure **Prometheus** is selected as datasource
3. Enter this query:
   ```
   gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets
   ```
4. Click **Run Query**
5. You should see metrics with labels like `exported_source`, `interface_name`

If no data:
- Check gNMIc is collecting: `curl -s http://172.20.20.5:9273/metrics | grep interface_statistics | head -5`
- Check Prometheus is scraping: `curl -s http://172.20.20.3:9090/api/v1/targets`

### Step 3: Check Dashboard Queries

1. Open the **Network Interface Performance** dashboard
2. Click on any panel title → **Edit**
3. Look at the query in the **Query** tab
4. The metric name should be: `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets`
5. Click **Apply** to save

### Step 4: Check Time Range

The dashboard defaults to "Last 15 minutes". If your lab just started:
1. Click the time picker (top right)
2. Change to "Last 5 minutes" or "Last 1 hour"
3. Click **Apply**

### Step 5: Force Refresh

1. Click the refresh icon (top right)
2. Or set auto-refresh to 10s

## Common Issues

### Issue: "Data source not found"

**Solution**: The datasource UID might be wrong.

1. Go to **Configuration** → **Data Sources**
2. Click **Prometheus**
3. Note the UID in the URL (e.g., `/datasources/edit/abc123`)
4. Edit dashboard panels to use this UID

Or simpler: Just select "Prometheus" from the dropdown in each panel.

### Issue: Queries return empty

**Cause**: Metric names might have changed.

**Check current metrics**:
```bash
curl -s http://172.20.20.5:9273/metrics | grep "interface_statistics" | head -10
```

Look for the actual metric names and update dashboard queries accordingly.

### Issue: Dashboard not loading

**Solution**: Restart Grafana
```bash
docker restart clab-monitoring-grafana
```

Wait 20 seconds, then refresh browser.

### Issue: Old dashboard errors in logs

The errors about `network-overview.json` are from a cached old dashboard. They don't affect the new dashboard. To clear:
```bash
bash -c "cd /Users/toddbowman/Documents/projects/grpc/containerlab && ./lab mon-stop && ./lab mon-start"
```

## Manual Dashboard Import

If auto-provisioning isn't working, import manually:

1. Open Grafana: http://localhost:3000
2. Click **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select: `monitoring/grafana/provisioning/dashboards/interface-performance.json`
5. Select **Prometheus** as the datasource
6. Click **Import**

## Verify Monitoring Stack

Run the check script:
```bash
bash -c "cd /Users/toddbowman/Documents/projects/grpc/containerlab && ./check-metrics.sh"
```

Should show:
- ✅ Prometheus is running
- ✅ gNMIc is running
- ✅ gNMIc metrics endpoint is accessible
- ✅ Interface metrics found
- ✅ Prometheus is scraping targets
- ✅ Prometheus has interface data

## Test Queries

### Basic connectivity test:
```bash
curl -s 'http://172.20.20.3:9090/api/v1/query?query=up'
```

### Check interface metrics exist:
```bash
curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets' | python3 -m json.tool | head -50
```

### Check rate calculation (what dashboard uses):
```bash
curl -s 'http://172.20.20.3:9090/api/v1/query?query=rate(gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets[1m])' | python3 -m json.tool | head -50
```

## Dashboard Panels

The dashboard includes these panels:

1. **Interface Throughput (All Devices)** - Line graph of all interfaces
2. **Link Utilization (%)** - Bar gauge with color thresholds
3. **Link Utilization Over Time** - Time series with 80% threshold
4. **Spine1/Spine2 Interface Throughput** - Individual gauges
5. **Traffic Distribution by Device** - Pie chart
6. **Link Utilization Heatmap** - Visual pattern identification
7. **Packet Rate (OUT)** - Packets per second
8. **Interface Errors and Discards** - Error monitoring

All panels use the metric: `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets`

## Still Not Working?

If you've tried everything above and still see "No Data":

1. **Check if metrics have different names**:
   ```bash
   curl -s http://172.20.20.5:9273/metrics | grep "interface" | grep "octets" | head -5
   ```

2. **Verify Prometheus can scrape gNMIc**:
   ```bash
   curl -s http://172.20.20.3:9090/api/v1/targets | python3 -m json.tool
   ```
   Look for the gNMIc target and check if `health: "up"`

3. **Check Grafana can reach Prometheus**:
   ```bash
   docker exec clab-monitoring-grafana wget -qO- http://172.20.20.3:9090/api/v1/query?query=up
   ```

4. **Restart everything**:
   ```bash
   bash -c "cd /Users/toddbowman/Documents/projects/grpc/containerlab && ./lab mon-stop && sleep 5 && ./lab mon-start"
   ```

5. **Check browser console** (F12) for JavaScript errors

## Getting Help

If still stuck, provide:
1. Output of `./check-metrics.sh`
2. Grafana logs: `docker logs clab-monitoring-grafana --tail 50`
3. Screenshot of the "No Data" error
4. Output of the test queries above
