# Validation Scripts

This directory contains validation scripts for verifying the production network testing lab functionality.

## Metric Normalization Verification

### check_normalization.py

Validates that metric normalization is working correctly across all vendors.

**What it checks**:
1. Prometheus connectivity
2. Normalized metrics exist (network_interface_*)
3. All vendors produce expected metric names
4. Metric values are preserved (not zero, have recent timestamps)
5. Interface names are normalized (ethX_Y format)
6. Cross-vendor consistency (same metrics from all vendors)

**Prerequisites**:
- Monitoring stack deployed (Prometheus, gNMIc, Grafana)
- Lab topology deployed with devices streaming telemetry
- Python 3.7+ with requests library

**Usage**:

```bash
# Basic usage (assumes Prometheus at localhost:9090, use ./lab tunnel first)
python3 validation/check_normalization.py

# Specify custom Prometheus URL
python3 validation/check_normalization.py --prometheus-url http://prometheus:9090

# Output results as JSON
python3 validation/check_normalization.py --json

# Or run on the remote server directly
./lab exec "python3 validation/check_normalization.py"
```

**Exit Codes**:
- 0: All checks passed
- 1: One or more checks failed

**Troubleshooting**:

1. **Prometheus Connectivity Failed**
   - Ensure monitoring is running: `./lab status`
   - Open tunnels first: `./lab tunnel`

2. **Normalized Metrics Missing**
   - Check gNMIc config: `monitoring/gnmic/gnmic-config.yml`
   - Check logs: `./lab exec "docker logs clab-monitoring-gnmic"`

3. **Vendor Coverage Incomplete**
   - Verify all vendor devices are deployed and running
   - Check gNMIc targets configuration

**Related Documentation**:
- `docs/developer/metric-normalization.md`
- `docs/monitoring/` — vendor-specific normalization guides
