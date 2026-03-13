# Task 17.1 Implementation: Metric Normalization Verification

**Task**: 17.1 Implement metric normalization verification  
**Requirements**: 8.3  
**Status**: ✅ Completed

## Overview

Implemented a comprehensive validation script that verifies metric normalization is working correctly across all vendors (SR Linux, Arista, SONiC, Juniper). The script queries Prometheus to ensure normalized metrics exist, all vendors produce expected metric names, and metric values are preserved during transformation.

## What Was Implemented

### 1. Main Validation Script

**File**: `validation/check_normalization.py`

A standalone Python script that performs comprehensive normalization validation:

**Features**:
- Prometheus connectivity check
- Normalized metric existence verification
- Vendor coverage validation (all 4 vendors)
- Metric value preservation checks (timestamps, numeric values)
- Interface name normalization verification
- Cross-vendor consistency validation
- JSON output support for CI/CD integration
- Detailed error reporting with remediation suggestions

**Validation Checks**:

1. **Prometheus Connectivity**: Verifies Prometheus is accessible
2. **Normalized Metrics Exist**: Checks for all 6 expected normalized metrics:
   - `network_interface_in_octets`
   - `network_interface_out_octets`
   - `network_interface_in_packets`
   - `network_interface_out_packets`
   - `network_interface_in_errors`
   - `network_interface_out_errors`

3. **Vendor Coverage**: Verifies all 4 vendors produce all expected metrics:
   - Nokia SR Linux (`vendor=nokia`)
   - Arista EOS (`vendor=arista`)
   - Dell EMC SONiC (`vendor=dellemc`)
   - Juniper Junos (`vendor=juniper`)

4. **Metric Values Preserved**: Validates:
   - Metric values are numeric
   - Timestamps are recent (within 5 minutes)
   - Values are not corrupted during transformation

5. **Interface Name Normalization**: Checks interface names follow normalized pattern:
   - SR Linux: `ethernet-1/1` → `eth1_1`
   - Arista: `Ethernet1` → `eth1_0`, `Ethernet1/1` → `eth1_1`
   - SONiC: `Ethernet0` → `eth0_0`
   - Juniper: `ge-0/0/0` → `eth0_0_0`

6. **Cross-Vendor Consistency**: Ensures same metric names across all vendors

### 2. Unit Tests

**File**: `validation/test_check_normalization.py`

Comprehensive unit tests covering:
- Validator initialization
- Prometheus connectivity (success and failure cases)
- Query execution (success and failure cases)
- Normalized metrics detection (all found, some missing)
- Vendor coverage (all vendors, missing vendors)
- Interface name normalization (normalized, unnormalized)
- Report generation

**Test Results**: ✅ 14 tests passed

### 3. Documentation

**File**: `validation/README.md`

Complete documentation including:
- Script purpose and requirements
- Usage examples
- Expected output format
- Exit codes
- Troubleshooting guide
- CI/CD integration examples
- Related documentation links

## Usage Examples

### Basic Usage

```bash
# Run validation (assumes Prometheus at localhost:9090)
./validation/check_normalization.py

# Specify custom Prometheus URL
./validation/check_normalization.py --prometheus-url http://prometheus:9090

# Output as JSON for CI/CD
./validation/check_normalization.py --json > report.json
```

### Expected Output

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

## Integration Points

### With Existing Normalization

The validation script works with the existing normalization infrastructure:

1. **gNMIc Processors**: Validates output from:
   - `normalize_interface_metrics` processor
   - `normalize_bgp_metrics` processor
   - `add_vendor_tags` processor

2. **Prometheus Relabeling**: Validates Prometheus relabeling rules in:
   - `monitoring/prometheus/prometheus.yml`

3. **Vendor-Specific Normalization**: Validates implementations from:
   - SR Linux normalization (Task 15.1)
   - Arista normalization (Task 15.2)
   - SONiC normalization (Task 15.3)
   - Juniper normalization (Task 15.4)

### With CI/CD Pipelines

The script is designed for CI/CD integration:

```bash
# Run in CI pipeline
./validation/check_normalization.py || exit 1

# Generate artifact
./validation/check_normalization.py --json > normalization-report.json
```

**Exit Codes**:
- `0`: All checks passed
- `1`: One or more checks failed

## Requirements Validation

### Requirement 8.3: Verify metric normalization is producing expected OpenConfig paths

✅ **Fully Implemented**

**Evidence**:

1. **Normalized Metrics Check**: Verifies all expected `network_*` metrics exist
2. **Vendor Coverage Check**: Confirms all vendors produce normalized metrics
3. **Metric Values Check**: Validates values are preserved during transformation
4. **Interface Names Check**: Ensures interface names are normalized
5. **Consistency Check**: Verifies same metric names across all vendors

**Acceptance Criteria Met**:
- ✅ Query Prometheus for normalized metrics
- ✅ Verify all vendors produce expected metric names
- ✅ Check that metric values are preserved
- ✅ Provide clear pass/fail output with details

## Testing

### Unit Tests

```bash
# Run unit tests
python3 -m pytest validation/test_check_normalization.py -v

# Results: 14 passed in 0.13s
```

### Manual Testing

```bash
# Test with non-existent Prometheus (error handling)
./validation/check_normalization.py --prometheus-url http://localhost:9999

# Output: ❌ Cannot connect to Prometheus. Aborting remaining checks.
```

### Integration Testing

To test with a live lab:

1. Deploy monitoring stack:
   ```bash
   orb -m clab ./deploy-monitoring.sh
   ```

2. Deploy lab topology with devices:
   ```bash
   orb -m clab sudo containerlab deploy -t topology.yml
   ```

3. Wait for metrics to be collected (30-60 seconds)

4. Run validation:
   ```bash
   ./validation/check_normalization.py
   ```

## Files Created

1. `validation/check_normalization.py` - Main validation script (executable)
2. `validation/test_check_normalization.py` - Unit tests
3. `validation/README.md` - Documentation
4. `validation/TASK-17.1-IMPLEMENTATION.md` - This implementation summary

## Dependencies

**Python Requirements**:
- Python 3.7+
- `requests` library (for Prometheus API calls)

**Runtime Requirements**:
- Prometheus running and accessible
- gNMIc collecting metrics from devices
- Lab topology deployed with devices streaming telemetry

## Error Handling

The script provides detailed error messages for common issues:

1. **Prometheus Connectivity Failed**
   - Clear message about connection failure
   - Aborts remaining checks to avoid cascading errors

2. **Missing Metrics**
   - Lists which metrics are missing
   - Shows count of found vs expected

3. **Missing Vendors**
   - Identifies which vendors are not producing metrics
   - Shows which metrics each vendor is producing

4. **Stale Data**
   - Reports metrics with old timestamps
   - Shows age of stale data

5. **Unnormalized Interface Names**
   - Lists examples of unnormalized names
   - Shows vendor for each example

## Future Enhancements

Potential improvements for future tasks:

1. **BGP Metrics Validation**: Add checks for BGP normalized metrics
2. **OSPF Metrics Validation**: Add checks for OSPF normalized metrics
3. **Historical Validation**: Check normalization over time ranges
4. **Performance Metrics**: Measure normalization overhead
5. **Alerting Integration**: Generate alerts for normalization failures
6. **Dashboard Integration**: Create Grafana dashboard showing validation status

## Related Documentation

- **Requirements**: `.kiro/specs/production-network-testing-lab/requirements.md` (Requirement 8.3)
- **Design**: `.kiro/specs/production-network-testing-lab/design.md`
- **Tasks**: `.kiro/specs/production-network-testing-lab/tasks.md` (Task 17.1)
- **Metric Normalization Guide**: `docs/developer/metric-normalization.md`
- **Vendor Normalization**:
  - `monitoring/gnmic/SR-LINUX-NORMALIZATION.md`
  - `monitoring/gnmic/ARISTA-NORMALIZATION.md`
  - `monitoring/gnmic/SONIC-NORMALIZATION.md`
  - `monitoring/gnmic/JUNIPER-NORMALIZATION.md`

## Summary

Task 17.1 is complete. The validation script provides comprehensive verification of metric normalization across all four vendors, with clear pass/fail output, detailed error reporting, and CI/CD integration support. All unit tests pass, and the script is ready for integration testing with a live lab environment.

**Key Achievements**:
- ✅ Standalone validation script with 6 comprehensive checks
- ✅ 14 unit tests covering all validation logic
- ✅ Complete documentation with usage examples
- ✅ CI/CD integration support with JSON output
- ✅ Detailed error reporting with remediation suggestions
- ✅ Validates all 4 vendors (SR Linux, Arista, SONiC, Juniper)
- ✅ Checks metric values are preserved during transformation
- ✅ Verifies interface name normalization across vendors
