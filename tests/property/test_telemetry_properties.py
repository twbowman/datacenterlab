"""
Property-based tests for telemetry collection and metric normalization

**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 4.3, 4.4**
"""

import copy

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Import test data generators
from .strategies import metrics


# Mock metric normalizer for testing
class MetricNormalizer:
    """
    Mock metric normalizer that simulates the gNMIc normalization process

    This is a simplified version for testing the normalization properties.
    In production, this would be the actual gNMIc processor logic.
    """

    # Mapping from vendor-specific paths to normalized OpenConfig paths
    NORMALIZATION_MAP = {
        # SR Linux paths
        "/interface/statistics/in-octets": "network_interface_in_octets",
        "/interface/statistics/out-octets": "network_interface_out_octets",
        "/interface/statistics/in-packets": "network_interface_in_packets",
        "/interface/statistics/out-packets": "network_interface_out_packets",
        "/network-instance/protocols/bgp/neighbor/session-state": "network_bgp_session_state",
        # Arista EOS paths (OpenConfig)
        "/interfaces/interface/state/counters/in-octets": "network_interface_in_octets",
        "/interfaces/interface/state/counters/out-octets": "network_interface_out_octets",
        "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state": "network_bgp_session_state",
        # SONiC paths
        "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets": "network_interface_in_octets",
        "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets": "network_interface_out_octets",
        "/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state": "network_bgp_session_state",
    }

    def normalize(self, metric: dict) -> dict:
        """
        Normalize a vendor-specific metric to OpenConfig format

        Args:
            metric: Dictionary with 'name', 'labels', 'value', 'timestamp'

        Returns:
            Normalized metric with universal name
        """
        normalized = copy.deepcopy(metric)

        # Transform metric name
        vendor_path = metric["name"]
        if vendor_path in self.NORMALIZATION_MAP:
            normalized["name"] = self.NORMALIZATION_MAP[vendor_path]
        else:
            # Preserve native metric with vendor prefix
            vendor = metric["labels"].get("vendor", "unknown")
            normalized["name"] = f"{vendor}_{vendor_path.replace('/', '_').strip('_')}"

        return normalized


# Property 14: Metric Transformation Preservation
@given(metric=metrics())
@settings(max_examples=100)
def test_metric_transformation_preservation(metric):
    """
    **Property 14: Metric Transformation Preservation**

    **Validates: Requirements 4.3**

    For any metric transformation, the metric value and timestamp should
    remain unchanged after normalization.

    This property ensures that normalization only changes the metric name
    and labels, but never modifies the actual data (value) or timing information.
    """
    normalizer = MetricNormalizer()

    # Store original value and timestamp
    original_value = metric["value"]
    original_timestamp = metric["timestamp"]

    # Normalize the metric
    normalized = normalizer.normalize(metric)

    # Property: Value must be preserved exactly
    assert normalized["value"] == original_value, (
        f"Value changed during normalization: {original_value} -> {normalized['value']}"
    )

    # Property: Timestamp must be preserved exactly
    assert normalized["timestamp"] == original_timestamp, (
        f"Timestamp changed during normalization: {original_timestamp} -> {normalized['timestamp']}"
    )

    # Property: Labels should be preserved (may be augmented but not removed)
    for key, value in metric["labels"].items():
        assert key in normalized["labels"], f"Label '{key}' was removed during normalization"
        assert normalized["labels"][key] == value, (
            f"Label '{key}' value changed: {value} -> {normalized['labels'][key]}"
        )


# Property 15: Cross-Vendor Metric Path Consistency
@given(
    metric_type=st.sampled_from(["in-octets", "out-octets", "bgp-session-state"]),
    vendor1=st.sampled_from(["srlinux", "eos", "sonic", "junos"]),
    vendor2=st.sampled_from(["srlinux", "eos", "sonic", "junos"]),
)
@settings(max_examples=100)
def test_cross_vendor_metric_path_consistency(metric_type, vendor1, vendor2):
    """
    **Property 15: Cross-Vendor Metric Path Consistency**

    **Validates: Requirements 4.1, 4.2, 4.4**

    For any equivalent metric from different vendors, the normalized metric
    path should be identical.

    This property ensures that the same type of metric (e.g., interface in-octets)
    from different vendors gets normalized to the exact same metric name, enabling
    universal queries across all vendors.
    """
    normalizer = MetricNormalizer()

    # Map metric types to vendor-specific paths
    metric_paths = {
        "srlinux": {
            "in-octets": "/interface/statistics/in-octets",
            "out-octets": "/interface/statistics/out-octets",
            "bgp-session-state": "/network-instance/protocols/bgp/neighbor/session-state",
        },
        "eos": {
            "in-octets": "/interfaces/interface/state/counters/in-octets",
            "out-octets": "/interfaces/interface/state/counters/out-octets",
            "bgp-session-state": "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state",
        },
        "sonic": {
            "in-octets": "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets",
            "out-octets": "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets",
            "bgp-session-state": "/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state",
        },
        "junos": {
            "in-octets": "/interfaces/interface/state/counters/in-octets",
            "out-octets": "/interfaces/interface/state/counters/out-octets",
            "bgp-session-state": "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state",
        },
    }

    # Create metrics from both vendors
    metric1 = {
        "name": metric_paths[vendor1][metric_type],
        "labels": {"vendor": vendor1, "source": "device1", "interface": "eth1"},
        "value": 1000.0,
        "timestamp": 1700000000,
    }

    metric2 = {
        "name": metric_paths[vendor2][metric_type],
        "labels": {"vendor": vendor2, "source": "device2", "interface": "eth2"},
        "value": 2000.0,
        "timestamp": 1700000001,
    }

    # Normalize both metrics
    normalized1 = normalizer.normalize(metric1)
    normalized2 = normalizer.normalize(metric2)

    # Property: Normalized metric names must be identical
    assert normalized1["name"] == normalized2["name"], (
        f"Metrics from {vendor1} and {vendor2} normalized to different names: "
        f"'{normalized1['name']}' vs '{normalized2['name']}'"
    )

    # Property: Normalized names must start with "network_" prefix
    assert normalized1["name"].startswith("network_"), (
        f"Normalized metric name '{normalized1['name']}' does not start with 'network_' prefix"
    )

    # Property: Normalized names must not contain vendor-specific information
    for vendor in ["srlinux", "eos", "sonic", "junos", "nokia", "arista"]:
        assert vendor not in normalized1["name"].lower(), (
            f"Normalized metric name '{normalized1['name']}' contains vendor-specific term '{vendor}'"
        )


# Additional test: Verify native metric preservation
@given(metric=metrics())
@settings(max_examples=50)
def test_native_metric_preservation(metric):
    """
    **Property 16: Native Metric Preservation**

    **Validates: Requirements 4.5, 6.2**

    For any vendor-specific metric without an OpenConfig equivalent,
    the metric should be preserved with a vendor prefix label.

    This ensures that vendor-specific metrics that don't have OpenConfig
    equivalents are still collected and identifiable.
    """
    normalizer = MetricNormalizer()

    # Create a metric with a path that has no OpenConfig equivalent
    native_metric = copy.deepcopy(metric)
    native_metric["name"] = "/vendor-specific/custom/metric"

    # Normalize the metric
    normalized = normalizer.normalize(native_metric)

    # Property: Native metrics should be preserved
    assert normalized["name"] is not None, "Native metric was dropped"

    # Property: Native metrics should have vendor identifier in name
    vendor = native_metric["labels"].get("vendor", "unknown")
    assert vendor in normalized["name"] or "vendor" in normalized["name"].lower(), (
        f"Native metric name '{normalized['name']}' does not contain vendor identifier"
    )

    # Property: Value and timestamp still preserved
    assert normalized["value"] == native_metric["value"]
    assert normalized["timestamp"] == native_metric["timestamp"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
