# Property-Based Tests

This directory contains property-based tests for the production network testing lab using the [Hypothesis](https://hypothesis.readthedocs.io/) framework.

## Overview

Property-based tests verify universal correctness properties that should hold true across all valid inputs, rather than testing specific examples. This provides much broader test coverage than traditional unit tests.

## Test Modules

### test_telemetry_properties.py
Tests for telemetry collection and metric normalization:
- **Property 14**: Metric Transformation Preservation (Requirements 4.3)
- **Property 15**: Cross-Vendor Metric Path Consistency (Requirements 4.1, 4.2, 4.4)
- **Property 16**: Native Metric Preservation (Requirements 4.5, 6.2)

### test_state_management_properties.py
Tests for lab state management:
- **Property 42**: Lab State Round-Trip (Requirements 12.2)
- **Property 47**: Version Control Friendly Format (Requirements 12.7)
- **Property 43**: State Snapshot Metadata (Requirements 12.3)

## Test Data Generators (strategies.py)

The `strategies` module provides Hypothesis strategies for generating random valid test data:
- `topologies()`: Random multi-vendor network topologies
- `bgp_configurations()`: Random BGP configurations
- `metrics()`: Random vendor-specific metrics
- `configurations()`: Random device configurations

## Running Tests

Install dependencies:
```bash
pip install -r requirements.txt
```

Run all property tests:
```bash
pytest tests/property/ -v
```

Run specific test module:
```bash
pytest tests/property/test_telemetry_properties.py -v
```

Run with more examples (slower but more thorough):
```bash
pytest tests/property/ -v --hypothesis-show-statistics
```

## Configuration

Hypothesis settings are configured in `conftest.py`:
- Default: 100 examples per test
- CI profile: 200 examples per test
- Dev profile: 50 examples with verbose output

To use a different profile:
```bash
pytest tests/property/ --hypothesis-profile=ci
```
