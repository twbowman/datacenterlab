# Routing Protocol Monitoring Dashboards

Two dashboards for monitoring OSPF and BGP stability in your datacenter network.

## Dashboards Created

1. **OSPF Stability Monitoring** (`ospf-stability`)
2. **BGP Stability Monitoring** (`bgp-stability`)

## Accessing the Dashboards

1. Open Grafana: http://localhost:3000
2. Login: admin/admin
3. Navigate to: **Dashboards → Network**
4. Select either:
   - **OSPF Stability Monitoring**
   - **BGP Stability Monitoring**

## OSPF Stability Dashboard

### Panels

1. **OSPF Neighbor Status**
   - Shows current state of all OSPF neighbors
   - Green = FULL (healthy)
   - Red = DOWN (problem)
   - Displays: Device - Interface - Neighbor Router ID

2. **OSPF Neighbors Count Over Time**
   - Line graph showing neighbor count per device
   - Helps identify flapping neighbors
   - Sudden drops indicate stability issues

3. **OSPF Retransmission Queue Length**
   - Shows packets waiting to be retransmitted
   - High values indicate:
     - Network congestion
     - Packet loss
     - Slow neighbor responses
   - Should normally be 0 or very low

4. **OSPF Neighbor Details Table**
   - Complete list of all OSPF neighbors
   - Columns: Device, Interface, Neighbor Router ID, State
   - Color-coded by state

### What to Look For

**Healthy OSPF**:
- All neighbors in FULL state
- Stable neighbor count over time
- Retransmission queue at 0

**Problems**:
- Neighbors not in FULL state
- Neighbor count fluctuating (flapping)
- High retransmission queue (>10)
- Missing expected neighbors

### Common Issues

| Symptom | Possible Cause | Action |
|---------|---------------|--------|
| Neighbor stuck in INIT | Hello packets not received | Check interface, MTU, network-type |
| Neighbor flapping | Unstable link, timers mismatch | Check interface errors, verify timers |
| High retransmit queue | Packet loss, congestion | Check interface utilization, errors |
| Missing neighbors | Interface down, config error | Verify OSPF is enabled on interface |

## BGP Stability Dashboard

### Panels

1. **BGP Session Status**
   - Shows current state of all BGP sessions
   - Green = ESTABLISHED (healthy)
   - Red = IDLE (down)
   - Yellow/Orange = Transitioning
   - Displays: Device - Peer Address

2. **BGP Established Sessions Over Time**
   - Line graph showing established session count
   - Helps identify session flapping
   - Should be stable and flat

3. **BGP Received Routes**
   - Number of routes received from each peer
   - Sudden changes indicate:
     - Route flapping
     - Peer issues
     - Network changes

4. **BGP Active Routes**
   - Number of routes actively used
   - Should match or be less than received routes
   - Tracks routing table health

5. **BGP Message Rate**
   - Rate of BGP messages (RX/TX)
   - Spikes indicate:
     - Route updates
     - Session resets
     - Network instability

6. **BGP Neighbor Details Table**
   - Complete list of all BGP neighbors
   - Columns: Device, Peer Address, Session State, Peer AS
   - Color-coded by session state

### What to Look For

**Healthy BGP**:
- All sessions ESTABLISHED
- Stable session count over time
- Consistent route counts
- Low, steady message rate

**Problems**:
- Sessions not ESTABLISHED
- Session count fluctuating (flapping)
- Route count changes without network changes
- High message rate (route churn)

### Common Issues

| Symptom | Possible Cause | Action |
|---------|---------------|--------|
| Session IDLE | Peer unreachable, config error | Check connectivity, verify config |
| Session flapping | Unstable link, hold timer issues | Check interface, adjust timers |
| Route count drops | Peer filtering, session reset | Check peer logs, verify filters |
| High message rate | Route flapping, instability | Investigate route changes, dampening |
| No routes received | Peer not advertising, filter | Check peer config, route policies |

## Metrics Being Collected

### OSPF Metrics
- `gnmic_ospf_state_srl_nokia_ospf_instance_area_interface_neighbor_adjacency_state`
- `gnmic_ospf_state_srl_nokia_ospf_instance_area_interface_neighbor_retransmission_queue_length`
- `gnmic_ospf_state_srl_nokia_ospf_instance_area_interface_neighbor_last_transition_time`

### BGP Metrics
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_session_state`
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_peer_as`
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_received_routes`
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_active_routes`
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_received_messages`
- `gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_sent_messages`

## Verifying Metrics Collection

Check if OSPF and BGP metrics are being collected:

```bash
# Check OSPF metrics
curl -s http://172.20.20.5:9273/metrics | grep ospf | head -10

# Check BGP metrics
curl -s http://172.20.20.5:9273/metrics | grep bgp | head -10
```

If no metrics appear, check gNMIc logs:
```bash
docker logs clab-monitoring-gnmic --tail 50
```

## Troubleshooting

### No Data in Dashboards

1. **Verify gNMIc is collecting routing metrics**:
   ```bash
   curl -s http://172.20.20.5:9273/metrics | grep -E "ospf|bgp"
   ```

2. **Check gNMIc configuration**:
   ```bash
   cat monitoring/gnmic/gnmic-config.yml
   ```
   Should include `ospf_state` and `bgp_state` subscriptions

3. **Restart gNMIc**:
   ```bash
   docker restart clab-monitoring-gnmic
   sleep 30
   ```

4. **Test manual query**:
   ```bash
   gnmic -a 172.20.20.10:57400 -u admin -p 'NokiaSrl1!' --skip-verify get --path '/network-instance[name=default]/protocols/ospf' --encoding json_ietf
   ```

### Metrics Have Different Names

If the dashboard shows "No data" but metrics exist with different names:

1. Check actual metric names:
   ```bash
   curl -s http://172.20.20.5:9273/metrics | grep "ospf\|bgp" | grep -v "#" | cut -d'{' -f1 | sort -u
   ```

2. Edit dashboard panels to use the correct metric names
3. Click panel title → Edit → Update query → Apply

### Dashboard Not Loading

Restart Grafana:
```bash
docker restart clab-monitoring-grafana
```

Wait 20 seconds, then refresh browser.

## Setting Up Alerts

### OSPF Alerts

**Alert: OSPF Neighbor Down**
- Condition: `gnmic_ospf_state_srl_nokia_ospf_instance_area_interface_neighbor_adjacency_state != 1`
- Threshold: Any neighbor not in FULL state
- Duration: 1 minute
- Severity: Critical

**Alert: High OSPF Retransmissions**
- Condition: `gnmic_ospf_state_srl_nokia_ospf_instance_area_interface_neighbor_retransmission_queue_length > 10`
- Threshold: Queue length > 10
- Duration: 5 minutes
- Severity: Warning

### BGP Alerts

**Alert: BGP Session Down**
- Condition: `gnmic_bgp_state_srl_nokia_bgp_neighbor_session_state{session_state!="established"}`
- Threshold: Any session not ESTABLISHED
- Duration: 2 minutes
- Severity: Critical

**Alert: BGP Route Count Change**
- Condition: `abs(delta(gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_received_routes[5m])) > 100`
- Threshold: >100 route change in 5 minutes
- Duration: Immediate
- Severity: Warning

**Alert: High BGP Message Rate**
- Condition: `rate(gnmic_bgp_state_srl_nokia_bgp_neighbor_statistics_received_messages[5m]) > 10`
- Threshold: >10 messages/second
- Duration: 5 minutes
- Severity: Warning

## Integration with Other Dashboards

These routing protocol dashboards complement:

1. **Interface Performance Dashboard** - Shows link-level issues affecting routing
2. **Python Link Analysis Tool** - Identifies ECMP load balancing problems

**Workflow**:
1. Monitor routing dashboards for protocol stability
2. Check interface dashboard for link issues
3. Use Python tool for detailed ECMP analysis
4. Correlate routing flaps with interface errors

## Production Best Practices

1. **Set up alerts** for all critical conditions
2. **Create runbooks** for common issues
3. **Document baseline** values (normal neighbor counts, route counts)
4. **Regular reviews** of routing stability trends
5. **Correlate events** with change management
6. **Export snapshots** before/after network changes
7. **Use annotations** to mark maintenance windows
8. **Create custom views** for different teams (NOC, Engineering)

## Files

- `monitoring/grafana/provisioning/dashboards/ospf-stability.json` - OSPF dashboard
- `monitoring/grafana/provisioning/dashboards/bgp-stability.json` - BGP dashboard
- `monitoring/gnmic/gnmic-config.yml` - gNMIc telemetry configuration
- `GRAFANA-TROUBLESHOOTING.md` - General Grafana troubleshooting

## Related Documentation

- `GRAFANA-DASHBOARD-GUIDE.md` - Interface performance dashboard guide
- `ansible/methods/srlinux_gnmi/UNDERLAY-ROUTING.md` - OSPF+BGP architecture
- `ansible/methods/srlinux_gnmi/playbooks/verify-detailed.yml` - CLI verification playbook
