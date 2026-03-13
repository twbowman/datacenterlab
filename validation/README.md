# Validation Scripts

This directory contains validation scripts for verifying the production network testing lab functionality.

## Metric Normalization Verification

### check_normalization.py

Validates that metric normalization is working correctly across all vendors.

**Requirements**: 8.3

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
# Basic usage (assumes Prometheus at localhost:9090)
./validation/check_normalization.py

# Specify custom Prometheus URL
./validation/check_normalization.py --prometheus-url http://prometheus:9090

# Output results as JSON
./validation/check_normalization.py --json

# Run from ORB VM context (if needed)
orb -m clab python3 validation/check_normalization.py
```

**Example Output**:

```
======================================================================
Metric Normalization Verification
======================================================================

Check Results:
----------------------------------------------------------------------
✅ PASS | Prometheus Connectivity
       Prometheus is accessible

✅ PASS | Normalized Metrics Exist
       All 6 normalized metrics found

✅ PASS | Vendor Coverage
       All 4 vendors producing all normalized metrics

✅ PASS | Metric Values Preserved
       All 48 metric values are valid and current

✅ PASS | Interface Name Normalization
       All 24 interface names are normalized

✅ PASS | Cross-Vendor Consistency
       All metrics consistent across 4 vendors

======================================================================
Summary: 6 passed, 0 failed
======================================================================
✅ All normalization checks passed!
```

**Exit Codes**:
- 0: All checks passed
- 1: One or more checks failed

**Troubleshooting**:

If checks fail, the script provides detailed information about what went wrong:

1. **Prometheus Connectivity Failed**
   - Ensure Prometheus is running: `orb -m clab docker ps | grep prometheus`
   - Check Prometheus URL is correct
   - Verify network connectivity

2. **Normalized Metrics Missing**
   - Check gNMIc is running: `orb -m clab docker ps | grep gnmic`
   - Verify gNMIc processors are configured in `monitoring/gnmic/gnmic-config.yml`
   - Check gNMIc logs: `orb -m clab docker logs clab-monitoring-gnmic`

3. **Vendor Coverage Incomplete**
   - Verify all vendor devices are deployed and running
   - Check gNMIc targets configuration includes all vendors
   - Verify gNMI connectivity to devices

4. **Metric Values Issues**
   - Stale data: Check if devices are still streaming telemetry
   - Zero values: May be normal for some counters (e.g., errors)
   - Non-numeric values: Check gNMIc transformation rules

5. **Interface Names Not Normalized**
   - Verify gNMIc processors include interface name transformations
   - Check Prometheus relabeling rules in `monitoring/prometheus/prometheus.yml`
   - Ensure processor order is correct (Juniper patterns must come first)

6. **Cross-Vendor Inconsistency**
   - Some vendors may not support all metrics
   - Check vendor-specific normalization documentation
   - Verify OpenConfig support for each vendor

**Integration with CI/CD**:

This script can be integrated into CI/CD pipelines:

```bash
# Run validation and fail pipeline if checks don't pass
./validation/check_normalization.py || exit 1

# Generate JSON report for artifact storage
./validation/check_normalization.py --json > normalization-report.json
```

**Related Documentation**:
- `docs/developer/metric-normalization.md` - Comprehensive normalization guide
- `monitoring/gnmic/SR-LINUX-NORMALIZATION.md` - SR Linux implementation
- `monitoring/gnmic/ARISTA-NORMALIZATION.md` - Arista implementation
- `monitoring/gnmic/SONIC-NORMALIZATION.md` - SONiC implementation
- `monitoring/gnmic/JUNIPER-NORMALIZATION.md` - Juniper implementation
