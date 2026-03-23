# Testing Guide for Vendor-Specific Relabeling Rules

## Prerequisites

1. **Lab must be running**:
```bash
sudo containerlab deploy -t topologies/topology-srlinux.yml
```

2. **Monitoring stack must be running**:
```bash
docker-compose -f monitoring/docker-compose.yml up -d
```

3. **Wait for metrics collection** (30-60 seconds):
```bash
# Check gNMIc is collecting metrics
curl -s http://localhost:9273/metrics | grep gnmic_oc_interface_stats | head -5

# Check Prometheus is scraping
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="gnmic")'
```

## Manual Testing

### Test 1: Verify Vendor Labels

**Purpose**: Confirm vendor and os labels are preserved from gNMIc

```bash
# Query for vendor label
curl -s 'http://localhost:9090/api/v1/label/vendor/values' | jq '.data'

# Expected output:
# [
#   "nokia"
# ]

# Query for os label
curl -s 'http://localhost:9090/api/v1/label/os/values' | jq '.data'

# Expected output:
# [
#   "srlinux"
# ]
```

### Test 2: Verify Role Labels

**Purpose**: Confirm role labels are correctly assigned based on device names

```bash
# Query for role label values
curl -s 'http://localhost:9090/api/v1/label/role/values' | jq '.data'

# Expected output:
# [
#   "leaf",
#   "spine"
# ]

# Query spine1 metrics to verify role=spine
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="spine1"}' | jq '.data.result[0].metric.role'

# Expected output:
# "spine"

# Query leaf1 metrics to verify role=leaf
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="leaf1"}' | jq '.data.result[0].metric.role'

# Expected output:
# "leaf"
```

### Test 3: Verify Topology Labels

**Purpose**: Confirm topology labels are correctly applied

```bash
# Query for topology label
curl -s 'http://localhost:9090/api/v1/label/topology/values' | jq '.data'

# Expected output:
# [
#   "gnmi-clos"
# ]

# Query for fabric_type label
curl -s 'http://localhost:9090/api/v1/label/fabric_type/values' | jq '.data'

# Expected output:
# [
#   "clos"
# ]
```

### Test 4: Verify Layer Labels

**Purpose**: Confirm layer labels match device roles

```bash
# Query for layer label values
curl -s 'http://localhost:9090/api/v1/label/layer/values' | jq '.data'

# Expected output:
# [
#   "layer2_layer3",
#   "layer3"
# ]

# Verify spine has layer3
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="spine1"}' | jq '.data.result[0].metric.layer'

# Expected output:
# "layer3"

# Verify leaf has layer2_layer3
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="leaf1"}' | jq '.data.result[0].metric.layer'

# Expected output:
# "layer2_layer3"
```

### Test 5: Verify Complete Label Set

**Purpose**: Confirm all labels are present on metrics

```bash
# Query a spine metric and display all labels
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{source="spine1"}' | jq '.data.result[0].metric'

# Expected output (example):
# {
#   "__name__": "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets",
#   "cluster": "gnmi-clos",
#   "collector": "gnmic",
#   "environment": "lab",
#   "fabric_type": "clos",
#   "instance": "clab-monitoring-gnmic:9273",
#   "interface_name": "ethernet-1/1",
#   "interface_normalized": "eth1_1",
#   "job": "gnmic",
#   "layer": "layer3",
#   "name": "spine1",
#   "os": "srlinux",
#   "role": "spine",
#   "source": "spine1",
#   "subscription_name": "oc_interface_stats",
#   "topology": "gnmi-clos",
#   "vendor": "nokia"
# }
```

## Automated Testing

### Run Validation Script

```bash
./monitoring/prometheus/validate-relabeling.sh
```

**Expected Output**:
```
==========================================
Prometheus Vendor-Specific Relabeling Validation
==========================================

Checking Prometheus availability...
✓ Prometheus is running

==========================================
Validating Vendor Labels
==========================================

Checking label 'vendor' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'vendor' found with values:
  - nokia

Checking label 'os' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'os' found with values:
  - srlinux

==========================================
Validating Device Role Labels
==========================================

Checking label 'role' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'role' found with values:
  - spine
  - leaf
✓ Expected value 'spine' found
✓ Expected value 'leaf' found

Verifying spine devices have 'spine' role...
✓ Spine devices correctly labeled with role=spine

Verifying leaf devices have 'leaf' role...
✓ Leaf devices correctly labeled with role=leaf

==========================================
Validating Topology Labels
==========================================

Checking label 'topology' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'topology' found with values:
  - gnmi-clos
✓ Expected value 'gnmi-clos' found

Checking label 'fabric_type' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'fabric_type' found with values:
  - clos
✓ Expected value 'clos' found

Checking label 'layer' on metric 'gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets'...
✓ Label 'layer' found with values:
  - layer3
  - layer2_layer3
✓ Expected value 'layer3' found
✓ Expected value 'layer2_layer3' found

==========================================
Validating Label Combinations
==========================================

Checking spine devices have layer=layer3...
✓ Spine devices correctly labeled with layer=layer3

Checking leaf devices have layer=layer2_layer3...
✓ Leaf devices correctly labeled with layer=layer2_layer3

Checking all devices with role have fabric_type=clos...
✓ All devices correctly labeled with fabric_type=clos

==========================================
Sample Metrics with All Labels
==========================================

Sample spine metric:
{
  "__name__": "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets",
  "cluster": "gnmi-clos",
  "collector": "gnmic",
  "environment": "lab",
  "fabric_type": "clos",
  "instance": "clab-monitoring-gnmic:9273",
  "interface_name": "ethernet-1/1",
  "interface_normalized": "eth1_1",
  "job": "gnmic",
  "layer": "layer3",
  "name": "spine1",
  "os": "srlinux",
  "role": "spine",
  "source": "spine1",
  "subscription_name": "oc_interface_stats",
  "topology": "gnmi-clos",
  "vendor": "nokia"
}

Sample leaf metric:
{
  "__name__": "gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets",
  "cluster": "gnmi-clos",
  "collector": "gnmic",
  "environment": "lab",
  "fabric_type": "clos",
  "instance": "clab-monitoring-gnmic:9273",
  "interface_name": "ethernet-1/3",
  "interface_normalized": "eth1_3",
  "job": "gnmic",
  "layer": "layer2_layer3",
  "name": "leaf1",
  "os": "srlinux",
  "role": "leaf",
  "source": "leaf1",
  "subscription_name": "oc_interface_stats",
  "topology": "gnmi-clos",
  "vendor": "nokia"
}

==========================================
✓ All vendor-specific relabeling validations passed
==========================================
```

## Query Testing

### Test Role-Based Queries

```bash
# Query all spine metrics
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role="spine"}' | jq '.data.result | length'

# Expected: Number of spine interfaces (should be > 0)

# Query all leaf metrics
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role="leaf"}' | jq '.data.result | length'

# Expected: Number of leaf interfaces (should be > 0)
```

### Test Topology-Based Queries

```bash
# Query all metrics from gnmi-clos topology
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{topology="gnmi-clos"}' | jq '.data.result | length'

# Expected: Total number of interfaces (should be > 0)

# Query all clos fabric metrics
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{fabric_type="clos"}' | jq '.data.result | length'

# Expected: Total number of interfaces (should be > 0)
```

### Test Layer-Based Queries

```bash
# Query layer3 metrics
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{layer="layer3"}' | jq '.data.result | length'

# Expected: Number of spine interfaces (should be > 0)

# Query layer2_layer3 metrics
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{layer="layer2_layer3"}' | jq '.data.result | length'

# Expected: Number of leaf interfaces (should be > 0)
```

### Test Combined Queries

```bash
# Query Nokia spine devices
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{vendor="nokia",role="spine"}' | jq '.data.result | length'

# Expected: Number of Nokia spine interfaces (should be > 0)

# Query layer3 devices in gnmi-clos topology
curl -s 'http://localhost:9090/api/v1/query?query=gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{topology="gnmi-clos",layer="layer3"}' | jq '.data.result | length'

# Expected: Number of spine interfaces (should be > 0)
```

## Grafana Testing

### Test in Grafana UI

1. **Open Grafana**: http://localhost:3000
2. **Navigate to Explore**
3. **Test queries**:

```promql
# Test role filtering
rate(gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{role="spine"}[5m]) * 8

# Test topology filtering
rate(gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{topology="gnmi-clos"}[5m]) * 8

# Test layer filtering
rate(gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{layer="layer3"}[5m]) * 8

# Test combined filtering
rate(gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets{vendor="nokia",role="spine"}[5m]) * 8
```

4. **Verify labels appear in legend**:
   - Legend format: `{{source}} - {{role}} - {{interface_normalized}}`
   - Should show: `spine1 - spine - eth1_1`

## Troubleshooting

### No Metrics Found

**Problem**: Queries return empty results

**Solutions**:
1. Check lab is running:
```bash
sudo containerlab inspect -t topologies/topology-srlinux.yml
```

2. Check monitoring stack is running:
```bash
docker ps | grep -E "gnmic|prometheus|grafana"
```

3. Check gNMIc is collecting metrics:
```bash
curl -s http://localhost:9273/metrics | grep gnmic_oc_interface_stats | head -5
```

4. Check Prometheus is scraping:
```bash
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="gnmic")'
```

### Labels Not Present

**Problem**: Expected labels are missing from metrics

**Solutions**:
1. Check Prometheus configuration is valid:
```bash
curl -s http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep -A 50 metric_relabel_configs
```

2. Check external labels:
```bash
curl -s http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep external_labels -A 5
```

3. Reload Prometheus configuration:
```bash
curl -X POST http://localhost:9090/-/reload
```

4. Check gNMIc is adding vendor labels:
```bash
curl -s http://localhost:9273/metrics | grep vendor
```

### Incorrect Label Values

**Problem**: Labels have wrong values

**Solutions**:
1. Verify device names match regex patterns:
```bash
# Test regex patterns
echo "spine1" | grep -E '(spine\d+)'
echo "leaf1" | grep -E '(leaf\d+)'
```

2. Check source label in metrics:
```bash
curl -s 'http://localhost:9090/api/v1/query?query=up{job="gnmic"}' | jq '.data.result[].metric.source'
```

3. Verify external labels:
```bash
curl -s 'http://localhost:9090/api/v1/query?query=up{job="gnmic"}' | jq '.data.result[].metric.cluster'
```

## Success Criteria

✅ All tests pass:
- Vendor labels preserved (vendor, os)
- Role labels correctly assigned (spine, leaf)
- Topology labels present (topology, fabric_type)
- Layer labels match roles (layer3, layer2_layer3)
- Label combinations are consistent
- Queries work with new labels

✅ Validation script passes:
```bash
./monitoring/prometheus/validate-relabeling.sh
# Exit code: 0
```

✅ Grafana dashboards work with new labels:
- Role-based filtering works
- Topology-based filtering works
- Layer-based filtering works
- Combined filters work

## Next Steps

After successful testing:

1. **Update Grafana dashboards** to use new labels
2. **Create alerting rules** using role/topology labels
3. **Add recording rules** for common aggregations
4. **Document query patterns** for operations team
5. **Test with multi-vendor topology** (when Arista/SONiC/Juniper added)
