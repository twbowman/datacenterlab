# Monitoring Guide

This guide explains how to collect telemetry, normalize metrics across vendors, and use Grafana dashboards to monitor your network lab.

## Overview

The monitoring stack consists of three components:

1. **gNMIc** - Collects telemetry from network devices via gNMI streaming
2. **Prometheus** - Stores time-series metrics with 30-day retention
3. **Grafana** - Visualizes metrics with universal and vendor-specific dashboards

## Architecture

```
Network Devices (SR Linux, Arista, SONiC, Juniper)
    ↓ gNMI streaming (10-60s intervals)
gNMIc Collector
    ↓ Metric normalization (vendor-agnostic paths)
Prometheus
    ↓ PromQL queries
Grafana Dashboards
```

## Deploying the Monitoring Stack

### Deploy Monitoring

```bash
# macOS ARM
sudo containerlab deploy -t topology-monitoring.yml

# Linux
sudo containerlab deploy -t topology-monitoring.yml
```

### Access Monitoring Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **gNMIc Metrics**: http://localhost:9273/metrics

### Verify Monitoring

```bash
# Check containers are running
docker ps --filter "name=clab-monitoring"

# Check gNMIc is collecting
curl -s http://localhost:9273/metrics | grep network_interface

# Check Prometheus has data
curl -s 'http://localhost:9090/api/v1/query?query=up'
```

## Metric Normalization

### Why Normalization?

Different vendors use different metric names and paths:

**SR Linux**: `/interface/statistics/in-octets`
**Arista**: `/interfaces/interface/state/counters/in-octets`
**SONiC**: `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets`
**Juniper**: `/junos/system/linecard/interface/logical/usage/in-octets`

Normalization transforms these to a universal format: `network_interface_in_octets`

### Normalized Metric Names

#### Interface Metrics

| Universal Metric | Description | SR Linux Path | Arista/SONiC Path | Juniper Path |
|------------------|-------------|---------------|-------------------|--------------|
| `network_interface_in_octets` | Bytes received | `/interface/statistics/in-octets` | `/interfaces/interface/state/counters/in-octets` | `/junos/system/linecard/interface/logical/usage/in-octets` |
| `network_interface_out_octets` | Bytes transmitted | `/interface/statistics/out-octets` | `/interfaces/interface/state/counters/out-octets` | `/junos/system/linecard/interface/logical/usage/out-octets` |
| `network_interface_in_packets` | Packets received | `/interface/statistics/in-packets` | `/interfaces/interface/state/counters/in-pkts` | `/junos/system/linecard/interface/logical/usage/in-pkts` |
| `network_interface_out_packets` | Packets transmitted | `/interface/statistics/out-packets` | `/interfaces/interface/state/counters/out-pkts` | `/junos/system/linecard/interface/logical/usage/out-pkts` |
| `network_interface_in_errors` | Input errors | `/interface/statistics/in-errors` | `/interfaces/interface/state/counters/in-errors` | `/junos/system/linecard/interface/logical/usage/in-errors` |
| `network_interface_out_errors` | Output errors | `/interface/statistics/out-errors` | `/interfaces/interface/state/counters/out-errors` | `/junos/system/linecard/interface/logical/usage/out-errors` |

#### BGP Metrics

| Universal Metric | Description | SR Linux Path | Arista/SONiC Path | Juniper Path |
|------------------|-------------|---------------|-------------------|--------------|
| `network_bgp_session_state` | BGP session state | `/network-instance/protocols/bgp/neighbor/session-state` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` | `/junos/routing/bgp/neighbor/state` |
| `network_bgp_peer_as` | Peer AS number | `/network-instance/protocols/bgp/neighbor/peer-as` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/peer-as` | N/A |
| `network_bgp_received_routes` | Routes received | `/network-instance/protocols/bgp/neighbor/received-routes` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/received` | `/junos/routing/bgp/neighbor/received-routes` |
| `network_bgp_sent_routes` | Routes sent | `/network-instance/protocols/bgp/neighbor/sent-routes` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/sent` | `/junos/routing/bgp/neighbor/advertised-routes` |

### Interface Name Normalization

Interface names are also normalized to a consistent format:

| Vendor | Original | Normalized |
|--------|----------|------------|
| SR Linux | `ethernet-1/1` | `eth1_1` |
| Arista | `Ethernet1/1` | `eth1_1` |
| Arista | `Ethernet1` | `eth1_0` |
| SONiC | `Ethernet0` | `eth0_0` |
| Juniper | `ge-0/0/0` | `eth0_0_0` |
| Juniper | `xe-0/0/0` | `eth0_0_0` |

This normalization happens in two places:
1. **gNMIc processors** - Transform metric names and labels
2. **Prometheus relabeling** - Add `interface_normalized` label

### Vendor Labels

All metrics include vendor identification labels:

- `vendor`: nokia, arista, dellemc, juniper
- `os`: srlinux, eos, sonic, junos
- `role`: spine, leaf, border
- `source`: device name (spine1, leaf1, etc.)

## Telemetry Collection

### Collection Intervals

gNMIc collects metrics at different intervals based on data type:

| Subscription | Paths | Interval | Mode |
|--------------|-------|----------|------|
| `oc_interface_stats` | Interface counters, oper-status, admin-status | 10s | stream/sample |
| `oc_bgp_neighbors` | BGP neighbor state | 30s | stream/sample |
| `srl_ospf_state` | OSPF state (SR Linux native) | 30s | stream/sample |
| `srl_bgp_detailed` | BGP detailed (SR Linux native, includes EVPN) | 30s | stream/sample |
| `oc_lldp` | LLDP neighbors | 60s | stream/sample |

### OpenConfig vs Native Paths

The lab uses a hybrid approach:

**OpenConfig Paths** (vendor-agnostic):
- Interface statistics
- BGP basic state
- LLDP neighbors

**Native Vendor Paths** (vendor-specific):
- OSPF state (poor OpenConfig support)
- BGP detailed state (includes EVPN)
- Vendor-specific features

### Adding New Devices to Monitoring

Edit `monitoring/gnmic/gnmic-config.yml`:

```yaml
targets:
  new-device:
    address: clab-lab-name-new-device:57400
    # gNMIc will automatically apply all subscriptions
```

Restart gNMIc:
```bash
docker restart clab-monitoring-gnmic
```

## Grafana Dashboards

### Universal Dashboards

Universal dashboards work across all vendors without modification.

#### Interface Performance Dashboard

**Panels**:
- Interface throughput (all devices)
- Link utilization percentage
- Link utilization over time
- Per-device interface throughput
- Traffic distribution by device
- Link utilization heatmap
- Packet rate
- Interface errors and discards

**Key Query**:
```promql
# Interface bandwidth (works for all vendors)
rate(gnmic_oc_interface_stats_network_interface_out_octets[1m]) * 8
```

**Filtering**:
- By vendor: `{vendor="nokia"}`
- By role: `{role="spine"}`
- By device: `{source="spine1"}`
- By interface: `{interface_normalized="eth1_1"}`

#### BGP Monitoring Dashboard

**Panels**:
- BGP session status (all neighbors)
- BGP session state by device
- BGP routes received/sent
- BGP session flaps

**Key Query**:
```promql
# BGP session state (works for all vendors)
gnmic_oc_bgp_neighbors_network_bgp_session_state{session_state="ESTABLISHED"}
```

#### LLDP Topology Dashboard

**Panels**:
- LLDP neighbor count by device
- LLDP topology map
- Missing LLDP neighbors

**Key Query**:
```promql
# LLDP neighbor count (works for all vendors)
count by (source) (gnmic_oc_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name)
```

### Vendor-Specific Dashboards

Vendor-specific dashboards show native metrics not available in OpenConfig.

#### SR Linux Native Dashboard

**Additional Metrics**:
- OSPF neighbor state
- EVPN routes
- System resources
- gNMI subscription status

**Example Query**:
```promql
# SR Linux OSPF neighbors
gnmic_srl_ospf_state_network_instance_protocols_ospf_neighbor_state
```

#### Arista Native Dashboard

**Additional Metrics**:
- Hardware sensor data
- ASIC statistics
- Queue depths

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3000
2. Click **Dashboards** → **New Dashboard**
3. Add a panel
4. Select **Prometheus** as data source
5. Enter a query (see examples below)
6. Configure visualization
7. Save dashboard

## Query Examples

### Interface Queries

**Interface bandwidth (bits per second)**:
```promql
rate(gnmic_oc_interface_stats_network_interface_out_octets[1m]) * 8
```

**Interface utilization percentage** (assuming 10Gbps links):
```promql
(rate(gnmic_oc_interface_stats_network_interface_out_octets[1m]) * 8) / 10000000000 * 100
```

**Top 10 busiest interfaces**:
```promql
topk(10, rate(gnmic_oc_interface_stats_network_interface_out_octets[5m]) * 8)
```

**Interface errors per second**:
```promql
rate(gnmic_oc_interface_stats_network_interface_in_errors[1m])
```

**Interfaces with errors**:
```promql
gnmic_oc_interface_stats_network_interface_in_errors > 0
```

### BGP Queries

**BGP sessions by state**:
```promql
count by (session_state) (gnmic_oc_bgp_neighbors_network_bgp_session_state)
```

**Established BGP sessions**:
```promql
count(gnmic_oc_bgp_neighbors_network_bgp_session_state{session_state="ESTABLISHED"})
```

**BGP sessions not established**:
```promql
gnmic_oc_bgp_neighbors_network_bgp_session_state{session_state!="ESTABLISHED"}
```

**BGP routes received per neighbor**:
```promql
gnmic_oc_bgp_neighbors_network_bgp_received_routes
```

**Total BGP routes in network**:
```promql
sum(gnmic_oc_bgp_neighbors_network_bgp_received_routes)
```

### Multi-Vendor Queries

**Interface bandwidth by vendor**:
```promql
sum by (vendor) (rate(gnmic_oc_interface_stats_network_interface_out_octets[1m]) * 8)
```

**BGP sessions by vendor**:
```promql
count by (vendor) (gnmic_oc_bgp_neighbors_network_bgp_session_state{session_state="ESTABLISHED"})
```

**Compare SR Linux vs Arista interface utilization**:
```promql
# SR Linux
avg(rate(gnmic_oc_interface_stats_network_interface_out_octets{vendor="nokia"}[5m]) * 8)

# Arista
avg(rate(gnmic_oc_interface_stats_network_interface_out_octets{vendor="arista"}[5m]) * 8)
```

### Device Role Queries

**Spine interface bandwidth**:
```promql
rate(gnmic_oc_interface_stats_network_interface_out_octets{role="spine"}[1m]) * 8
```

**Leaf BGP sessions**:
```promql
count(gnmic_oc_bgp_neighbors_network_bgp_session_state{role="leaf",session_state="ESTABLISHED"})
```

### Topology Queries

**LLDP neighbors per device**:
```promql
count by (source) (gnmic_oc_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name)
```

**Devices with missing LLDP neighbors** (expected 4, actual < 4):
```promql
count by (source) (gnmic_oc_lldp_lldp_interfaces_interface_neighbors_neighbor_state_system_name) < 4
```

## Alerting

### Prometheus Alerts

Alerts are defined in `monitoring/prometheus/alerts.yml`.

**Example Alert** (BGP session down):
```yaml
groups:
  - name: bgp_alerts
    rules:
      - alert: BGPSessionDown
        expr: gnmic_oc_bgp_neighbors_network_bgp_session_state{session_state!="ESTABLISHED"} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "BGP session down on {{ $labels.source }}"
          description: "BGP session to {{ $labels.neighbor_address }} is {{ $labels.session_state }}"
```

**Example Alert** (High interface utilization):
```yaml
- alert: HighInterfaceUtilization
  expr: (rate(gnmic_oc_interface_stats_network_interface_out_octets[5m]) * 8) / 10000000000 * 100 > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High interface utilization on {{ $labels.source }}"
    description: "Interface {{ $labels.interface_normalized }} is {{ $value }}% utilized"
```

### Viewing Alerts

1. Open Prometheus: http://localhost:9090
2. Click **Alerts** in the top menu
3. View active alerts and their states

## Troubleshooting

### No Data in Grafana

**Check gNMIc is collecting**:
```bash
curl -s http://localhost:9273/metrics | grep network_interface | head -5
```

**Check Prometheus is scraping**:
```bash
curl -s http://localhost:9090/api/v1/targets | jq
```

**Check gNMIc logs**:
```bash
docker logs clab-monitoring-gnmic --tail 50
```

### Metrics Missing for Specific Vendor

**Check device is reachable**:
```bash
docker exec clab-monitoring-gnmic ping -c 3 clab-lab-name-device1
```

**Check gNMI is enabled on device**:
```bash
# SR Linux
docker exec clab-lab-name-device1 sr_cli "show system gnmi-server"

# Arista
docker exec clab-lab-name-device1 Cli -c "show management api gnmi"
```

**Check gNMIc target configuration**:
```bash
# View gNMIc config
cat monitoring/gnmic/gnmic-config.yml | grep -A 2 "device1:"
```

### Dashboard Shows "No Data"

**Check time range**: Ensure time range includes recent data (last 5-15 minutes)

**Check query syntax**: Test query in Prometheus Explore view first

**Check data source**: Verify dashboard is using correct Prometheus data source

**Refresh dashboard**: Click refresh icon or set auto-refresh

### Metric Names Don't Match

**Check normalization is working**:
```bash
# Should see network_interface_* metrics
curl -s http://localhost:9273/metrics | grep "network_interface_in_octets"
```

**Check gNMIc processors**:
```bash
# View processor configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 20 "normalize_interface_metrics"
```

**Restart gNMIc** to reload configuration:
```bash
docker restart clab-monitoring-gnmic
```

## Best Practices

### Dashboard Design

1. **Use Universal Metrics**: Prefer `network_*` metrics for cross-vendor dashboards
2. **Add Vendor Filter**: Include vendor variable for filtering
3. **Normalize Interface Names**: Use `interface_normalized` label
4. **Document Queries**: Add panel descriptions explaining queries
5. **Set Appropriate Intervals**: Match query intervals to collection intervals

### Query Optimization

1. **Use Recording Rules**: Pre-calculate expensive queries
2. **Limit Time Ranges**: Avoid queries over 24+ hours
3. **Use Aggregation**: Aggregate before rate calculations
4. **Avoid Regex**: Use label matching instead of regex when possible

### Metric Collection

1. **Balance Intervals**: Don't collect everything at 1s intervals
2. **Monitor Collector**: Watch gNMIc CPU and memory usage
3. **Limit Subscriptions**: Only collect metrics you need
4. **Use Sampling**: Use sample mode for counters, on-change for state

### Data Retention

1. **Default**: 30 days in Prometheus
2. **Adjust**: Edit `monitoring/prometheus/prometheus.yml` retention settings
3. **Backup**: Export important metrics before retention expires
4. **Archive**: Use Prometheus snapshots for long-term storage

## Advanced Topics

### Custom Metric Normalization

Add new normalization rules in `monitoring/gnmic/gnmic-config.yml`:

```yaml
processors:
  normalize_custom_metrics:
    event-processors:
      - event-convert:
          value-names:
            - "^/vendor-specific/path$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/vendor-specific/path"
                new: "network_custom_metric"
```

### Recording Rules

Pre-calculate expensive queries in `monitoring/prometheus/prometheus.yml`:

```yaml
groups:
  - name: interface_rules
    interval: 30s
    rules:
      - record: interface_bandwidth_bps
        expr: rate(gnmic_oc_interface_stats_network_interface_out_octets[1m]) * 8
      
      - record: interface_utilization_percent
        expr: (interface_bandwidth_bps / 10000000000) * 100
```

### Prometheus Federation

For multi-lab setups, federate metrics to a central Prometheus:

```yaml
# Central Prometheus config
scrape_configs:
  - job_name: 'federate-lab1'
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="gnmic"}'
    static_configs:
      - targets:
          - 'lab1-prometheus:9090'
```

## Next Steps

- **Troubleshooting Guide**: Detailed troubleshooting procedures
- **Example Dashboards**: Pre-built dashboard examples
- **Alerting Guide**: Configure alerting and notifications
- **Performance Tuning**: Optimize collection and storage
