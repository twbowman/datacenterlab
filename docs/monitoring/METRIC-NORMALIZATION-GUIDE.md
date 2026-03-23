# Metric Normalization Guide - Vendor-Agnostic Queries

## Goal

Transform vendor-specific gNMI metrics into universal metrics that work like SNMP MIBs.

## Before Normalization

```promql
# Different query per vendor
rate(gnmic_srl_interface_statistics_in_octets{source="spine1"}[5m]) * 8
rate(gnmic_eos_interface_counters_in_octets{source="arista-spine1"}[5m]) * 8
```

## After Normalization

```promql
# One query for all vendors
rate(network_interface_in_octets{source=~".*spine.*"}[5m]) * 8
```

## Solution 1: gNMIc Event Processors (Recommended)

### Update gNMIc Configuration

Edit `monitoring/gnmic/gnmic-config.yml`:

```yaml
username: admin
password: NokiaSrl1!
skip-verify: true
encoding: json_ietf

targets:
  spine1:
    address: clab-gnmi-clos-spine1:57400
    tags:
      vendor: nokia
      os: srlinux
      device_type: spine
  
  spine2:
    address: clab-gnmi-clos-spine2:57400
    tags:
      vendor: nokia
      os: srlinux
      device_type: spine

subscriptions:
  # SR Linux native paths
  srl_interface_stats:
    paths:
      - /interface[name=*]/statistics
    mode: stream
    stream-mode: sample
    sample-interval: 10s
  
  srl_bgp_state:
    paths:
      - /network-instance[name=default]/protocols/bgp
    mode: stream
    stream-mode: sample
    sample-interval: 30s

# Processors to normalize metrics
processors:
  # Normalize interface metrics
  normalize_interface_metrics:
    event-processors:
      # Convert SR Linux interface metrics to generic names
      - event-convert:
          value-names:
            - "^/srl_nokia/interface/statistics/in-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/srl_nokia/interface/statistics/in-octets"
                new: "interface_in_octets"
      
      - event-convert:
          value-names:
            - "^/srl_nokia/interface/statistics/out-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/srl_nokia/interface/statistics/out-octets"
                new: "interface_out_octets"

outputs:
  # Original vendor-specific metrics
  prom_vendor_specific:
    type: prometheus
    listen: :9273
    path: /metrics
    metric-prefix: gnmic
    append-subscription-name: true
  
  # Normalized vendor-agnostic metrics
  prom_normalized:
    type: prometheus
    listen: :9274
    path: /metrics
    metric-prefix: network
    event-processors:
      - normalize_interface_metrics
```

### Result

Two metric endpoints:
- `:9273/metrics` - Original vendor-specific (for debugging)
- `:9274/metrics` - Normalized vendor-agnostic (for dashboards)

## Solution 2: Prometheus Relabeling

### Update Prometheus Configuration

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'gnmic'
    static_configs:
      - targets: ['clab-monitoring-gnmic:9273']
    
    metric_relabel_configs:
      # Normalize SR Linux interface metrics
      - source_labels: [__name__]
        regex: 'gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_in_octets'
        target_label: __name__
        replacement: 'network_interface_in_octets'
      
      - source_labels: [__name__]
        regex: 'gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_out_octets'
        target_label: __name__
        replacement: 'network_interface_out_octets'
      
      # Normalize Arista interface metrics (when added)
      - source_labels: [__name__]
        regex: 'gnmic_eos_interface_counters_in_octets'
        target_label: __name__
        replacement: 'network_interface_in_octets'
      
      - source_labels: [__name__]
        regex: 'gnmic_eos_interface_counters_out_octets'
        target_label: __name__
        replacement: 'network_interface_out_octets'
      
      # Keep original metric as label for debugging
      - source_labels: [__name__]
        regex: 'gnmic_(srl|eos|sonic)_.*'
        target_label: original_metric
        replacement: '${1}'
```

### Restart Prometheus

```bash
docker restart clab-monitoring-prometheus
```

## Solution 3: Combined Approach (Best)

Use both gNMIc processors AND Prometheus relabeling:

1. **gNMIc**: Basic normalization and tagging
2. **Prometheus**: Final metric name standardization

This gives you flexibility and debugging capability.

## Metric Mapping Table

Create a standard mapping for all vendors:

| Generic Metric | SR Linux | Arista EOS | SONiC |
|----------------|----------|------------|-------|
| `network_interface_in_octets` | `/interface/statistics/in-octets` | `/interfaces/interface/state/counters/in-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets` |
| `network_interface_out_octets` | `/interface/statistics/out-octets` | `/interfaces/interface/state/counters/out-octets` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets` |
| `network_interface_in_packets` | `/interface/statistics/in-packets` | `/interfaces/interface/state/counters/in-pkts` | `/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-pkts` |
| `network_bgp_session_state` | `/network-instance/protocols/bgp/neighbor/session-state` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` | `/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state` |

## Implementation Steps

### Step 1: Test Current Metrics

```bash
# Check what metrics are currently available
curl http://172.20.20.5:9273/metrics | grep "gnmic_srl_interface" | head -5
```

### Step 2: Add Normalization to gNMIc

Update `monitoring/gnmic/gnmic-config.yml` with processors

### Step 3: Restart gNMIc

```bash
docker restart clab-monitoring-gnmic
sleep 10
```

### Step 4: Verify Normalized Metrics

```bash
# Check normalized metrics
curl http://172.20.20.5:9274/metrics | grep "network_interface"
```

### Step 5: Update Grafana Dashboards

Change queries from:
```promql
rate(gnmic_srl_interface_statistics_in_octets[5m]) * 8
```

To:
```promql
rate(network_interface_in_octets[5m]) * 8
```

## Example: Complete Normalized Config

```yaml
# monitoring/gnmic/gnmic-config-normalized.yml
username: admin
password: NokiaSrl1!
skip-verify: true
encoding: json_ietf

targets:
  spine1:
    address: clab-gnmi-clos-spine1:57400
    tags:
      vendor: nokia
      device_type: spine

subscriptions:
  interface_stats:
    paths:
      - /interface[name=*]/statistics
    mode: stream
    stream-mode: sample
    sample-interval: 10s

processors:
  normalize_metrics:
    event-processors:
      # Add metric type tag
      - event-add-tag:
          tag-name: metric_class
          value: interface
      
      # Normalize metric names
      - event-strings:
          value-names:
            - "^.*in-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: ".*"
                new: "interface_in_octets"

outputs:
  prom:
    type: prometheus
    listen: :9273
    path: /metrics
    metric-prefix: network
    event-processors:
      - normalize_metrics
    add-target-labels: true
```

## Grafana Query Examples

### Before Normalization
```promql
# Vendor-specific
rate(gnmic_srl_interface_statistics_in_octets{source="spine1",interface="ethernet-1/1"}[5m]) * 8
```

### After Normalization
```promql
# Vendor-agnostic
rate(network_interface_in_octets{source="spine1",interface="ethernet-1/1"}[5m]) * 8

# Works across all vendors
rate(network_interface_in_octets{vendor=~"nokia|arista"}[5m]) * 8

# Just like SNMP!
rate(network_interface_in_octets[5m]) * 8
```

## Benefits

### 1. Universal Queries
✅ One query works for all vendors
✅ Like SNMP MIBs but better

### 2. Easy Migration
✅ Add new vendors without changing dashboards
✅ Swap vendors without query changes

### 3. Simplified Maintenance
✅ One set of dashboards
✅ One set of alerts
✅ Less complexity

### 4. Keep gNMI Advantages
✅ Streaming efficiency
✅ Rich data
✅ Real-time updates
✅ Modern features

## Testing

```bash
# Test normalized metrics
curl http://172.20.20.5:9274/metrics | grep "network_interface_in_octets"

# Should see
network_interface_in_octets{interface="ethernet-1/1",source="spine1",vendor="nokia"} 123456

# Query in Prometheus
curl 'http://172.20.20.3:9090/api/v1/query?query=network_interface_in_octets'
```

## Troubleshooting

### Metrics Not Appearing

1. Check gNMIc logs:
```bash
docker logs clab-monitoring-gnmic | tail -50
```

2. Verify processor syntax:
```bash
docker exec clab-monitoring-gnmic cat /gnmic-config.yml
```

3. Test without processors first

### Wrong Metric Names

Check the exact path in gNMI response:
```bash
docker exec clab-monitoring-gnmic /app/gnmic -a 172.20.20.10:57400 \
  -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interface[name=ethernet-1/1]/statistics"
```

## Next Steps

1. Implement normalization in your lab
2. Test with current SR Linux devices
3. When adding Arista, add Arista mappings
4. Update dashboards to use normalized metrics
5. Document your metric mapping table

## Result

You get SNMP-like universal queries PLUS all the benefits of gNMI:
- Streaming efficiency
- Rich data
- Real-time updates
- Modern features
- Vendor-agnostic queries

Best of both worlds!
