# Quick Start: Metric Normalization Validation

## Prerequisites

1. **Lab deployed**: `./lab deploy`
2. **Open tunnels**: `./lab tunnel` (for Prometheus access at localhost:9090)
3. **Wait for metrics** (30-60 seconds for initial collection)

## Run Validation

```bash
# Basic usage
python3 validation/check_normalization.py

# JSON output (for CI/CD)
python3 validation/check_normalization.py --json > report.json

# Or run on the remote server
./lab exec "python3 validation/check_normalization.py"
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
```

**Exit Code**: 0

## Troubleshooting

```bash
# Check lab status
./lab status

# Check gNMIc logs
./lab exec "docker logs clab-monitoring-gnmic"

# Check Prometheus targets
# Open http://localhost:9090/targets after ./lab tunnel
```

## Run Unit Tests

```bash
python3 -m pytest validation/test_check_normalization.py -v
```

See `validation/README.md` for complete documentation.
