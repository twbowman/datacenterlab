# Current Metrics Reference - SR Linux

## Available Metrics

Based on the current lab deployment, here are the actual metrics being collected from SR Linux devices.

## Checking Available Metrics

```bash
# View all metrics
curl http://172.20.20.5:9273/metrics | less

# Search for specific metrics
curl http://172.20.20.5:9273/metrics | grep "gnmic_srl"

# Count metrics
curl http://172.20.20.5:9273/metrics | grep "^gnmic_srl" | wc -l
```

## BGP Metrics

### BGP Admin State
```promql
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state

# Example value
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state{
  admin_state="enable",
  network_instance_name="default",
  oper_state="up",
  router_id="10.0.0.1",
  source="spine1",
  subscription_name="srl_bgp_detailed"
} 1
```

### BGP Active Routes by AFI/SAFI
```promql
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes

# Example values
# EVPN routes on leaf
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{
  admin_state="enable",
  afi_safi_afi_safi_name="evpn",
  network_instance_name="default",
  source="leaf1",
  subscription_name="srl_bgp_detailed"
} 3

# IPv4 unicast routes
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{
  admin_state="enable",
  afi_safi_afi_safi_name="ipv4-unicast",
  network_instance_name="default",
  source="spine1",
  subscription_name="srl_bgp_detailed"
} 6
```

### BGP Neighbor State
```promql
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state

# Example
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{
  neighbor_address="10.0.1.1",
  peer_as="65000",
  session_state="established",
  source="spine1",
  subscription_name="srl_bgp_detailed"
} 1
```

## OSPF Metrics

### OSPF Instance State
```promql
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state

# Example
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state{
  admin_state="enable",
  instance_name="main",
  network_instance_name="default",
  oper_state="up",
  router_id="10.0.0.1",
  source="spine1",
  subscription_name="srl_ospf_state"
} 1
```

### OSPF Neighbor Count
```promql
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_total_neighbors

# Example
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_total_neighbors{
  instance_name="main",
  network_instance_name="default",
  source="spine1",
  subscription_name="srl_ospf_state"
} 4
```

## Interface Metrics

### Interface Statistics (if collected)
```promql
# These would be available if interface subscription is added
gnmic_srl_interface_statistics_in_octets
gnmic_srl_interface_statistics_out_octets
gnmic_srl_interface_statistics_in_packets
gnmic_srl_interface_statistics_out_packets
gnmic_srl_interface_statistics_in_error_packets
gnmic_srl_interface_statistics_out_error_packets
```

## LLDP Metrics (if collected)
```promql
# These would be available if LLDP subscription is added
gnmic_srl_lldp_interface_neighbor_count
gnmic_srl_lldp_neighbor_system_name
```

## Grafana Query Examples

### Dashboard: BGP Overview

**Panel 1: BGP Sessions by State**
```promql
# Count of established sessions
count(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{session_state="established"})

# Count by device
count by (source) (gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{session_state="established"})
```

**Panel 2: BGP Routes by AFI/SAFI**
```promql
# EVPN routes per device
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{afi_safi_afi_safi_name="evpn"}

# Total routes by type
sum by (afi_safi_afi_safi_name) (gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes)
```

**Panel 3: BGP Session Flaps**
```promql
# Established transitions (flap counter)
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_established_transitions

# Rate of flaps
rate(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_established_transitions[5m])
```

### Dashboard: OSPF Overview

**Panel 1: OSPF Neighbor Count**
```promql
# Total neighbors per device
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_total_neighbors

# Sum across all devices
sum(gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_total_neighbors)
```

**Panel 2: OSPF State**
```promql
# Devices with OSPF up
gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state{oper_state="up"}

# Count of devices with OSPF up
count(gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_admin_state{oper_state="up"})
```

### Dashboard: Network Overview

**Panel 1: Device Status**
```promql
# All devices reporting metrics
count by (source) (gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state)

# Or use up metric if available
up{job="gnmic"}
```

**Panel 2: Total EVPN Routes**
```promql
# Sum of all EVPN routes
sum(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{afi_safi_afi_safi_name="evpn"})

# EVPN routes per device
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{afi_safi_afi_safi_name="evpn"}
```

## Alert Examples

### BGP Session Down
```yaml
- alert: BGPSessionDown
  expr: |
    gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state{session_state!="established"} > 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "BGP session down on {{ $labels.source }}"
    description: "BGP neighbor {{ $labels.neighbor_address }} on {{ $labels.source }} is {{ $labels.session_state }}"
```

### OSPF Neighbor Loss
```yaml
- alert: OSPFNeighborLoss
  expr: |
    gnmic_srl_ospf_state_srl_nokia_network_instance_network_instance_protocols_ospf_instance_total_neighbors < 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "OSPF neighbor count low on {{ $labels.source }}"
    description: "{{ $labels.source }} has only {{ $value }} OSPF neighbors"
```

### BGP Route Count Change
```yaml
- alert: EVPNRouteCountChange
  expr: |
    abs(delta(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_afi_safi_active_routes{afi_safi_afi_safi_name="evpn"}[5m])) > 1
  for: 2m
  labels:
    severity: info
  annotations:
    summary: "EVPN route count changed on {{ $labels.source }}"
    description: "EVPN routes changed by {{ $value }} on {{ $labels.source }}"
```

## Adding Interface Metrics

To add interface statistics to your collection, update `monitoring/gnmic/gnmic-config.yml`:

```yaml
subscriptions:
  # Add this subscription
  srl_interface_stats:
    paths:
      - /interface[name=*]/statistics
    mode: stream
    stream-mode: sample
    sample-interval: 10s
```

Then restart gNMIc:
```bash
docker restart clab-monitoring-gnmic
```

New metrics will appear:
```promql
gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_in_octets
gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_out_octets
gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_in_packets
gnmic_srl_interface_stats_srl_nokia_interface_interface_statistics_out_packets
```

## Metric Name Pattern

SR Linux metrics follow this pattern:
```
gnmic_{subscription_name}_srl_nokia_{path_components}

Examples:
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state
       ^                ^                                                                        ^
       |                |                                                                        |
  subscription      vendor prefix                                                          metric name
```

## Labels Available

Common labels on SR Linux metrics:
- `source` - Device name (spine1, leaf1, etc.)
- `subscription_name` - gNMIc subscription name
- `network_instance_name` - Network instance (usually "default")
- `admin_state` - Administrative state
- `oper_state` - Operational state
- `router_id` - BGP/OSPF router ID
- `neighbor_address` - BGP neighbor IP
- `afi_safi_afi_safi_name` - BGP address family
- `interface` - Interface name (when applicable)

## Querying Tips

### 1. Find Available Metrics
```promql
# List all SR Linux BGP metrics
{__name__=~"gnmic_srl_bgp.*"}

# List all metrics for a device
{source="spine1"}

# List all metrics from a subscription
{subscription_name="srl_bgp_detailed"}
```

### 2. Aggregate Across Devices
```promql
# Total BGP sessions
count(gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state)

# Sessions per device
count by (source) (gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state)

# Sessions by state
count by (session_state) (gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state)
```

### 3. Filter by Device Type
```promql
# Spines only (if you add device_type tag)
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state{source=~"spine.*"}

# Leafs only
gnmic_srl_bgp_detailed_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_admin_state{source=~"leaf.*"}
```

## Next Steps

1. **Explore Current Metrics**
   ```bash
   curl http://172.20.20.5:9273/metrics | grep "gnmic_srl" | less
   ```

2. **Create Basic Dashboard**
   - Import existing dashboards from `monitoring/grafana/provisioning/dashboards/`
   - Modify queries to use actual metric names

3. **Add More Subscriptions**
   - Interface statistics
   - LLDP neighbors
   - System information

4. **Set Up Alerts**
   - BGP session down
   - OSPF neighbor loss
   - Interface errors

## Reference

- **gNMIc Config**: `monitoring/gnmic/gnmic-config.yml`
- **Existing Dashboards**: `monitoring/grafana/provisioning/dashboards/`
- **Prometheus**: http://172.20.20.3:9090
- **Grafana**: http://localhost:3000
- **Metrics Endpoint**: http://172.20.20.5:9273/metrics
