# Quick Start: Metric Normalization Validation

## Prerequisites

1. **Monitoring stack deployed**:
   ```bash
   orb -m clab ./deploy-monitoring.sh
   ```

2. **Lab topology deployed**:
   ```bash
   orb -m clab sudo containerlab deploy -t topology.yml
   ```

3. **Wait for metrics** (30-60 seconds for initial collection)

## Run Validation

### Basic Usage

```bash
./validation/check_normalization.py
```

### With Custom Prometheus URL

```bash
./validation/check_normalization.py --prometheus-url http://prometheus:9090
```

### JSON Output (for CI/CD)

```bash
./validation/check_normalization.py --json > report.json
```

## Expected Results

### ✅ Success

```
======================================================================
Metric Normalization Verification
======================================================================

Check Results:
----------------------------------------------------------------------
✅ PASS | Prometheus Connectivity
✅ PASS | Normalized Metrics Exist
✅ PASS | Vendor Coverage
✅ PASS | Metric Values Preserved
✅ PASS | Interface Name Normalization
✅ PASS | Cross-Vendor Consistency

======================================================================
Summary: 6 passed, 0 failed
======================================================================
✅ All normalization checks passed!
```

**Exit Code**: 0

### ❌ Failure

```
======================================================================
Metric Normalization Verification
======================================================================

Check Results:
----------------------------------------------------------------------
✅ PASS | Prometheus Connectivity
❌ FAIL | Normalized Metrics Exist
       Missing 2 metrics: network_interface_in_errors, network_interface_out_errors

======================================================================
Summary: 1 passed, 1 failed
======================================================================
❌ Some normalization checks failed. See details above.
```

**Exit Code**: 1

## Troubleshooting

### Cannot Connect to Prometheus

```bash
# Check if Prometheus is running
orb -m clab docker ps | grep prometheus

# Check Prometheus logs
orb -m clab docker logs clab-monitoring-prometheus
```

### Missing Metrics

```bash
# Check if gNMIc is running
orb -m clab docker ps | grep gnmic

# Check gNMIc logs
orb -m clab docker logs clab-monitoring-gnmic

# Check gNMIc metrics endpoint
curl http://localhost:9273/metrics | grep network_interface
```

### Missing Vendors

```bash
# Check which devices are running
orb -m clab docker ps | grep clab-gnmi-clos

# Check gNMIc targets configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 5 targets
```

## Run Unit Tests

```bash
python3 -m pytest validation/test_check_normalization.py -v
```

Expected: 14 tests passed

## More Information

See `validation/README.md` for complete documentation.
