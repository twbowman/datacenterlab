# Monitoring Documentation

Documentation for the telemetry and monitoring stack using gNMIc and Prometheus.

## Overview

- [OpenConfig Telemetry Guide](OPENCONFIG-TELEMETRY-GUIDE.md) - OpenConfig telemetry overview
- [Telemetry Multi-Vendor Summary](TELEMETRY-MULTI-VENDOR-SUMMARY.md) - Multi-vendor telemetry approach
- [gNMI vs SNMP Comparison](GNMI-VS-SNMP-COMPARISON.md) - Protocol comparison

## Metric Normalization

- [Metric Normalization Guide](METRIC-NORMALIZATION-GUIDE.md) - Normalizing metrics across vendors
- [Current Metrics Reference](CURRENT-METRICS-REFERENCE.md) - Available metrics reference
- [Transformation Validation Guide](TRANSFORMATION-VALIDATION-GUIDE.md) - Validating transformations

### Vendor-Specific Normalization

- [SR Linux Normalization](SR-LINUX-NORMALIZATION.md)
- [Arista Normalization](ARISTA-NORMALIZATION.md)
- [SONiC Normalization](SONIC-NORMALIZATION.md)
- [Juniper Normalization](JUNIPER-NORMALIZATION.md)

## Prometheus Configuration

- [Relabeling Rules Summary](RELABELING-RULES-SUMMARY.md) - Prometheus relabeling overview
- [Vendor Relabeling Guide](VENDOR-RELABELING-GUIDE.md) - Vendor-specific relabeling
- [Testing Guide](TESTING-GUIDE.md) - Testing monitoring configuration

## Dashboards

- [Vendor-Specific Dashboards Guide](VENDOR-SPECIFIC-DASHBOARDS-GUIDE.md) - Creating vendor dashboards

## Related Documentation

- Original monitoring directory: `../../monitoring/`
- gNMIc configuration: `../../monitoring/gnmic/`
- Prometheus configuration: `../../monitoring/prometheus/`
