# Testing Guide - Multi-Vendor OpenConfig Implementation

## Quick Test

Run the comprehensive test script:

```bash
./test-openconfig-implementation.sh
```

This will:
1. Check if lab is running (start if needed)
2. Restart gNMIc with OpenConfig config
3. Test OpenConfig paths on devices
4. Verify streaming subscriptions
5. Check Prometheus metrics
6. Show sample telemetry data

## Manual Testing Steps

### 1. Verify Lab is Running

```bash
docker ps --filter "name=clab-gnmi-clos" --format "table {{.Names}}\t{{.Status}}"
```

Should show 13 containers running (6 switches + 4 clients + 3 monitoring).

### 2. Test OpenConfig Paths

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

### 3. Test Streaming Subscriptions

```bash
# Subscribe to interface counters (should stream data every 10s)
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  subscribe --path "/interfaces/interface/state/counters" \
  --stream-mode sample --sample-interval 10s
```

Press Ctrl+C to stop.

### 4. Check Prometheus Metrics

```bash
# Check gNMIc metrics endpoint
curl http://172.20.20.5:9273/metrics | grep gnmic_interfaces_interface_state

# Should see metrics like:
# gnmic_interfaces_interface_state_counters_in_octets
# gnmic_interfaces_interface_state_counters_out_octets
# gnmic_interfaces_interface_state_oper_status
```

### 5. Query Prometheus

```bash
# Query Prometheus for OpenConfig metrics
curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interfaces_interface_state_counters_in_octets' | jq .

# Check all targets are up
curl -s 'http://172.20.20.3:9090/api/v1/targets' | jq .
```

### 6. Check Grafana

Open http://localhost:3000 (admin/admin)

Create a test query:
```promql
rate(gnmic_interfaces_interface_state_counters_in_octets[5m]) * 8
```

## Comparison: OpenConfig vs Native

### OpenConfig Interface Counters

```bash
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/counters/in-octets"
```

### SR Linux Native Interface Statistics

```bash
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure \
  get --path "/interface[name=ethernet-1/1]/statistics/in-octets"
```

Both should return the same data, but OpenConfig path will work on Arista and SONiC too!

## Troubleshooting

### Lab Not Running

```bash
# Start the lab
./deploy.sh

# Wait for devices to boot
sleep 120
```

### gNMIc Not Collecting

```bash
# Check gNMIc logs
docker logs clab-gnmi-clos-gnmic

# Restart gNMIc
docker restart clab-gnmi-clos-gnmic

# Wait for reconnection
sleep 10
```

### Path Not Found

Some OpenConfig paths may not be supported. Check:

```bash
# Check device capabilities
docker exec clab-gnmi-clos-gnmic gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p NokiaSrl1! --insecure capabilities | grep openconfig
```

Refer to `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md` for vendor support matrix.

### No Metrics in Prometheus

```bash
# Check gNMIc is exposing metrics
curl http://172.20.20.5:9273/metrics | head -20

# Check Prometheus is scraping
curl http://172.20.20.3:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="gnmic")'
```

## Expected Results

### ✅ OpenConfig Paths Working
- Interface counters: in-octets, out-octets, in-pkts, out-pkts
- Interface status: oper-status, admin-status
- LLDP: neighbor discovery

### ✅ Metrics in Prometheus
- `gnmic_interfaces_interface_state_counters_*`
- `gnmic_interfaces_interface_state_oper_status`
- `gnmic_lldp_interfaces_*`

### ✅ Native Paths Still Working
- SR Linux OSPF: `/network-instance[name=default]/protocols/ospf`
- SR Linux BGP: `/network-instance[name=default]/protocols/bgp`

## Test Checklist

- [ ] Lab is running (13 containers)
- [ ] OpenConfig interface paths work
- [ ] OpenConfig LLDP paths work
- [ ] Streaming subscriptions work
- [ ] Metrics visible at gNMIc endpoint
- [ ] Metrics queryable in Prometheus
- [ ] Grafana can display metrics
- [ ] Native paths still work for OSPF/BGP

## Next Steps After Testing

1. **Create OpenConfig Dashboards**: Build Grafana dashboards using OpenConfig metrics
2. **Add Vendors**: Add Arista or SONiC devices to test cross-vendor
3. **Document Quirks**: Note any vendor-specific behaviors
4. **Optimize Collection**: Tune sample intervals based on needs

## Reference

- **Implementation Steps**: `OPENCONFIG-IMPLEMENTATION-STEPS.md`
- **Vendor Support**: `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md`
- **Architecture**: `MULTI-VENDOR-IMPLEMENTATION-COMPLETE.md`
