# gNMIc Transformation Rule Validation Guide

## Overview

This guide explains how to validate gNMIc transformation rules at startup to ensure metric normalization is configured correctly.

**Requirement**: 4.7 - THE Metric_Normalizer SHALL validate transformation rules at startup

## Validation Script

The validation script `validate-transformation-rules.sh` performs comprehensive checks on the gNMIc configuration file to ensure all transformation rules are syntactically correct and properly configured.

### Location

```
monitoring/gnmic/validate-transformation-rules.sh
```

### Usage

```bash
# Run validation
./monitoring/gnmic/validate-transformation-rules.sh

# Or with explicit path
bash monitoring/gnmic/validate-transformation-rules.sh
```

### Prerequisites

- **Python 3**: Required for YAML parsing
- **PyYAML**: Python YAML library (usually pre-installed)

Check prerequisites:
```bash
python3 --version
python3 -c "import yaml; print('PyYAML installed')"
```

## What Gets Validated

The script performs 13 comprehensive validation checks:

### 1. Configuration File Existence
- Verifies `monitoring/gnmic/gnmic-config.yml` exists

### 2. Dependencies
- Checks that Python 3 is installed

### 3. YAML Syntax
- Validates the configuration file is valid YAML
- Detects syntax errors before gNMIc starts

### 4. Processors Section
- Verifies the `processors` section exists in the configuration

### 5. Interface Metrics Processor
- Checks `normalize_interface_metrics` processor is defined
- Counts transformation rules (expects at least 10)
- Validates coverage for all vendors

### 6. BGP Metrics Processor
- Checks `normalize_bgp_metrics` processor is defined
- Counts transformation rules (expects at least 5)
- Validates BGP metric transformations

### 7. Vendor Tags Processor
- Checks `add_vendor_tags` processor is defined
- Verifies vendor tags for:
  - Nokia (SR Linux)
  - Arista (EOS)
  - Dell EMC (SONiC)
  - Juniper (Junos)

### 8. Regex Patterns
- Validates interface name normalization patterns are configured
- Checks pattern structure

### 9. Metric Path Transformations
- Verifies critical transformations exist:
  - `network_interface_in_octets`
  - `network_interface_out_octets`
  - `network_bgp_session_state`

### 10. Output Configuration
- Checks Prometheus output is configured
- Verifies all processors are applied to the output:
  - `normalize_interface_metrics`
  - `normalize_bgp_metrics`
  - `add_vendor_tags`

### 11. Sample Data Testing
- Tests transformation rules with sample interface names:
  - SR Linux: `ethernet-1/1` → `eth1_1`
  - Arista: `Ethernet1/1` → `eth1_1`
  - SONiC: `Ethernet0` → `eth0_0`
  - Juniper: `ge-0/0/0` → `eth0_0_0`

### 12. Duplicate Detection
- Scans for duplicate transformation rules
- Warns if the same metric path is transformed multiple times

### 13. Vendor Coverage
- Verifies all 4 vendors have transformation rules:
  - SR Linux (`/srl_nokia/`)
  - Arista (`/interfaces/interface/state/counters/`)
  - SONiC (`/sonic-port:`)
  - Juniper (`/junos/`)

## Output Format

The script provides color-coded output:

- **✓ PASS** (Green): Check passed successfully
- **⚠ WARN** (Yellow): Non-critical issue detected
- **✗ FAIL** (Red): Critical issue that must be fixed
- **ℹ INFO** (Blue): Informational message

### Example Output

```
==========================================
gNMIc Transformation Rule Validation
==========================================

1. Checking configuration file...
✓ PASS: Configuration file found: monitoring/gnmic/gnmic-config.yml

2. Checking dependencies...
✓ PASS: python3 is installed

3. Validating YAML syntax...
✓ PASS: YAML syntax is valid

...

==========================================
Validation Summary
==========================================
Passed: 32
Warnings: 0
Failed: 0

✓ All transformation rule validations passed!
```

## Exit Codes

- **0**: All validations passed
- **1**: One or more validations failed

## Integration with Startup

### Manual Validation

Run before starting gNMIc:

```bash
# Validate configuration
./monitoring/gnmic/validate-transformation-rules.sh

# If validation passes, start gNMIc
docker-compose -f monitoring/docker-compose.yml up -d gnmic
```

### Automated Validation

Add to deployment scripts:

```bash
#!/bin/bash
# deploy-monitoring.sh

echo "Validating gNMIc configuration..."
if ! ./monitoring/gnmic/validate-transformation-rules.sh; then
    echo "ERROR: gNMIc configuration validation failed"
    exit 1
fi

echo "Starting monitoring stack..."
docker-compose -f monitoring/docker-compose.yml up -d
```

### Docker Entrypoint

For containerized gNMIc, add validation to entrypoint:

```dockerfile
# Dockerfile
COPY validate-transformation-rules.sh /usr/local/bin/
COPY validate-config-helper.py /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/validate-and-start.sh"]
```

```bash
#!/bin/bash
# validate-and-start.sh

echo "Validating gNMIc configuration..."
if ! /usr/local/bin/validate-transformation-rules.sh; then
    echo "ERROR: Configuration validation failed"
    exit 1
fi

echo "Starting gNMIc..."
exec gnmic --config /etc/gnmic/gnmic-config.yml subscribe
```

## Troubleshooting

### YAML Syntax Errors

If validation fails with YAML syntax errors:

```bash
# Check YAML syntax manually
python3 -c "import yaml; yaml.safe_load(open('monitoring/gnmic/gnmic-config.yml'))"
```

Common issues:
- Incorrect indentation
- Missing colons
- Unquoted special characters
- Unclosed brackets or quotes

### Missing Processors

If processors are not found:

1. Check the `processors` section exists in `gnmic-config.yml`
2. Verify processor names match exactly:
   - `normalize_interface_metrics`
   - `normalize_bgp_metrics`
   - `add_vendor_tags`

### Processors Not Applied to Output

If processors exist but aren't applied to output:

1. Check the `outputs.prom.event-processors` section
2. Ensure all three processors are listed:

```yaml
outputs:
  prom:
    type: prometheus
    event-processors:
      - normalize_interface_metrics
      - normalize_bgp_metrics
      - add_vendor_tags
```

### Missing Vendor Transformations

If vendor-specific transformations are missing:

1. Check the processor contains transformations for the vendor's paths
2. Verify the path patterns match the vendor's gNMI paths
3. See `monitoring/gnmic/METRIC-NORMALIZATION-GUIDE.md` for vendor path mappings

### Sample Test Failures

If sample data tests fail:

1. Check the regex patterns in the configuration
2. Verify the patterns use correct escaping: `\\d+` not `\d+`
3. Test patterns manually:

```bash
echo "ethernet-1/1" | sed -E 's/^ethernet-([0-9]+)\/([0-9]+)$/eth\1_\2/'
# Should output: eth1_1
```

## Helper Script

The validation script uses a Python helper for YAML parsing:

```
monitoring/gnmic/validate-config-helper.py
```

This helper provides commands for:
- Checking processor existence
- Counting transformations
- Validating vendor tags
- Checking patterns and paths

You generally don't need to use this directly, but it's available for custom validation scripts.

## Related Documentation

- **Metric Normalization**: `monitoring/gnmic/METRIC-NORMALIZATION-GUIDE.md`
- **Vendor-Specific Guides**:
  - `monitoring/gnmic/SONIC-NORMALIZATION.md`
  - `monitoring/gnmic/JUNIPER-NORMALIZATION.md`
- **Prometheus Relabeling**: `monitoring/prometheus/VENDOR-RELABELING-GUIDE.md`

## Best Practices

1. **Run validation before every deployment**
   - Catches configuration errors early
   - Prevents runtime failures

2. **Validate after configuration changes**
   - Always validate when adding new vendors
   - Validate when modifying transformation rules

3. **Include in CI/CD pipeline**
   - Add validation to automated tests
   - Fail builds if validation fails

4. **Monitor validation results**
   - Track warnings over time
   - Address warnings before they become failures

5. **Keep validation script updated**
   - Update when adding new vendors
   - Add checks for new transformation types

## Example: Adding a New Vendor

When adding a new vendor, update the validation script:

1. Add vendor to the vendor tags check (section 7)
2. Add vendor path to vendor coverage check (section 13)
3. Add sample interface name to sample tests (section 11)

Example:
```bash
# In validate-transformation-rules.sh

# Section 7: Add to vendors array
vendors=("nokia" "arista" "dellemc" "juniper" "cisco")

# Section 13: Add to vendor paths
vendors=("SR Linux" "Arista" "SONiC" "Juniper" "Cisco")
vendor_paths=("/srl_nokia/" "/interfaces/interface/state/counters/" "/sonic-port:" "/junos/" "/cisco/")

# Section 11: Add sample test
# Cisco: GigabitEthernet0/0/0 -> eth0_0_0
```

## Summary

The transformation rule validation script ensures:

- ✓ Configuration is syntactically valid
- ✓ All required processors are defined
- ✓ Transformations cover all vendors
- ✓ Processors are applied to outputs
- ✓ Regex patterns work correctly
- ✓ No duplicate transformations exist

Run this script before starting gNMIc to catch configuration errors early and ensure reliable metric normalization across all vendors.
