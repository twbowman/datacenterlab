# Task 16.3 Implementation: Transformation Rule Validation

## Task Description

**Task**: 16.3 Implement transformation rule validation
- Create startup validation script for gNMIc config
- Validate all transformation rules are syntactically correct
- Test transformation rules with sample data
- **Requirements**: 4.7

**Requirement 4.7**: THE Metric_Normalizer SHALL validate transformation rules at startup

## Implementation Summary

Created a comprehensive validation system for gNMIc transformation rules that ensures metric normalization is configured correctly before the collector starts.

## Files Created

### 1. `validate-transformation-rules.sh`
**Location**: `monitoring/gnmic/validate-transformation-rules.sh`

Main validation script that performs 13 comprehensive checks:

1. Configuration file existence
2. Python 3 dependency check
3. YAML syntax validation
4. Processors section validation
5. Interface metrics processor validation
6. BGP metrics processor validation
7. Vendor tags processor validation
8. Regex pattern validation
9. Metric path transformation validation
10. Output configuration validation
11. Sample data transformation testing
12. Duplicate transformation detection
13. Vendor coverage validation

**Features**:
- Color-coded output (green/yellow/red)
- Detailed error messages
- Sample data testing with real interface names
- Exit code 0 for success, 1 for failure
- Counts passed/warned/failed checks

### 2. `validate-config-helper.py`
**Location**: `monitoring/gnmic/validate-config-helper.py`

Python helper script for YAML parsing and configuration inspection:

**Commands**:
- `check_processors`: Verify processors section exists
- `check_processor <name>`: Check if specific processor exists
- `count_transforms <processor>`: Count transformations in a processor
- `check_vendor_tag <vendor>`: Verify vendor tag configuration
- `check_pattern <processor> <pattern>`: Check if regex pattern exists
- `check_metric_transform <processor> <name>`: Verify metric transformation
- `check_output_processor <name>`: Check if processor is applied to output
- `check_vendor_path <processor> <path>`: Verify vendor-specific path exists
- `list_value_names <processor>`: List all value-names from a processor

**Why Python?**:
- More portable than yq (which requires separate installation)
- Python 3 is typically pre-installed on most systems
- Provides robust YAML parsing with PyYAML

### 3. `TRANSFORMATION-VALIDATION-GUIDE.md`
**Location**: `monitoring/gnmic/TRANSFORMATION-VALIDATION-GUIDE.md`

Comprehensive documentation covering:
- How to use the validation script
- What gets validated (detailed explanation of all 13 checks)
- Output format and interpretation
- Integration with startup procedures
- Troubleshooting common issues
- Best practices
- Example: Adding a new vendor

## Validation Checks Performed

### Syntax Validation
- ✓ YAML syntax is valid
- ✓ Configuration file structure is correct
- ✓ All required sections exist

### Processor Validation
- ✓ `normalize_interface_metrics` processor exists
- ✓ `normalize_bgp_metrics` processor exists
- ✓ `add_vendor_tags` processor exists
- ✓ Sufficient transformations defined (10+ for interfaces, 5+ for BGP)

### Vendor Coverage
- ✓ SR Linux transformations present
- ✓ Arista transformations present
- ✓ SONiC transformations present
- ✓ Juniper transformations present
- ✓ Vendor tags configured for all vendors

### Transformation Rules
- ✓ Interface metrics transformed to `network_interface_*`
- ✓ BGP metrics transformed to `network_bgp_*`
- ✓ Interface names normalized (ethernet-1/1 → eth1_1)
- ✓ No duplicate transformations

### Output Configuration
- ✓ Prometheus output configured
- ✓ All processors applied to output
- ✓ Metrics will be exported correctly

### Sample Data Testing
Tests actual transformation logic with sample interface names:
- SR Linux: `ethernet-1/1` → `eth1_1` ✓
- Arista: `Ethernet1/1` → `eth1_1` ✓
- SONiC: `Ethernet0` → `eth0_0` ✓
- Juniper: `ge-0/0/0` → `eth0_0_0` ✓

## Usage

### Basic Usage

```bash
# Run validation
./monitoring/gnmic/validate-transformation-rules.sh
```

### Integration with Deployment

```bash
# Validate before starting gNMIc
if ./monitoring/gnmic/validate-transformation-rules.sh; then
    echo "Configuration valid, starting gNMIc..."
    orb -m clab docker-compose -f monitoring/docker-compose.yml up -d gnmic
else
    echo "Configuration validation failed!"
    exit 1
fi
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Validate gNMIc Configuration
  run: |
    ./monitoring/gnmic/validate-transformation-rules.sh
```

## Test Results

Ran validation against current `gnmic-config.yml`:

```
==========================================
Validation Summary
==========================================
Passed: 32
Warnings: 0
Failed: 0

✓ All transformation rule validations passed!
```

**Validated**:
- 24 interface metric transformations
- 16 BGP metric transformations
- 4 vendor tag configurations
- All critical metric paths
- All vendor-specific paths
- Sample data transformations

## Benefits

### 1. Early Error Detection
- Catches configuration errors before gNMIc starts
- Prevents runtime failures
- Reduces debugging time

### 2. Comprehensive Coverage
- Validates syntax, structure, and logic
- Tests with sample data
- Checks all vendors

### 3. Clear Feedback
- Color-coded output
- Specific error messages
- Actionable remediation steps

### 4. Production Ready
- Exit codes for automation
- Detailed logging
- Portable (only requires Python 3)

### 5. Maintainable
- Modular design (helper script)
- Well-documented
- Easy to extend for new vendors

## Requirement Validation

**Requirement 4.7**: THE Metric_Normalizer SHALL validate transformation rules at startup

✓ **SATISFIED**

The validation script:
1. Can be run at startup (before gNMIc starts)
2. Validates all transformation rules are syntactically correct
3. Tests transformation rules with sample data
4. Provides clear pass/fail indication
5. Exits with appropriate status code for automation

## Integration Points

### 1. Manual Deployment
Run validation before starting monitoring stack:
```bash
./monitoring/gnmic/validate-transformation-rules.sh && \
orb -m clab docker-compose -f monitoring/docker-compose.yml up -d
```

### 2. Deployment Scripts
Add to `deploy.sh` or similar:
```bash
echo "Validating gNMIc configuration..."
if ! ./monitoring/gnmic/validate-transformation-rules.sh; then
    echo "ERROR: Configuration validation failed"
    exit 1
fi
```

### 3. Docker Entrypoint
For containerized gNMIc:
```bash
#!/bin/bash
# Validate before starting
/usr/local/bin/validate-transformation-rules.sh || exit 1
exec gnmic --config /etc/gnmic/gnmic-config.yml subscribe
```

### 4. CI/CD Pipeline
Add to GitHub Actions, GitLab CI, etc.:
```yaml
test:
  script:
    - ./monitoring/gnmic/validate-transformation-rules.sh
```

## Future Enhancements

Possible improvements for future tasks:

1. **JSON Schema Validation**
   - Define JSON schema for gNMIc config
   - Validate against schema

2. **Live Testing**
   - Connect to test device
   - Verify actual metric transformation

3. **Performance Testing**
   - Measure transformation overhead
   - Validate CPU/memory usage

4. **Regression Testing**
   - Store known-good configurations
   - Compare against baseline

5. **Auto-fix**
   - Suggest fixes for common issues
   - Auto-generate missing transformations

## Related Tasks

- **Task 15.1**: Configure SR Linux metric normalization
- **Task 15.2**: Configure Arista metric normalization
- **Task 15.3**: Configure SONiC metric normalization
- **Task 15.4**: Configure Juniper metric normalization
- **Task 16.1**: Add interface name normalization rules
- **Task 16.2**: Add vendor-specific relabeling rules

## Conclusion

Task 16.3 is complete. The transformation rule validation system:

✓ Validates gNMIc configuration at startup
✓ Checks all transformation rules are syntactically correct
✓ Tests transformation rules with sample data
✓ Provides comprehensive coverage for all vendors
✓ Integrates easily with deployment workflows
✓ Satisfies Requirement 4.7

The validation script is production-ready and can be used immediately to ensure reliable metric normalization across all vendors.
