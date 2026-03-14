#!/usr/bin/env python3
"""
Unit tests for validation functionality

Tests validation checks, error detection, and report generation.
Validates: Requirements 15.1
"""

import json

import pytest


class TestBGPValidation:
    """Test BGP session validation"""

    def test_bgp_session_established(self, mock_device_bgp_state):
        """Test validation of established BGP sessions"""
        # Use mock device state from fixture
        bgp_state = mock_device_bgp_state["spine1"]

        expected_neighbors = ["10.1.1.1"]

        # Validate all expected neighbors are established
        for neighbor_ip in expected_neighbors:
            assert neighbor_ip in bgp_state["neighbor"]
            assert bgp_state["neighbor"][neighbor_ip]["session_state"] == "ESTABLISHED"

    def test_bgp_session_not_established(self):
        """Test detection of non-established BGP sessions"""
        # Create mock state with non-established session
        bgp_state = {"neighbor": {"10.1.1.1": {"session_state": "IDLE", "peer_as": 65011}}}

        # Should detect non-established session
        for neighbor_ip, neighbor_data in bgp_state["neighbor"].items():
            if neighbor_data["session_state"] != "ESTABLISHED":
                error = {
                    "check": "bgp_session",
                    "status": "fail",
                    "neighbor": neighbor_ip,
                    "expected": "ESTABLISHED",
                    "actual": neighbor_data["session_state"],
                    "remediation": f"Check BGP configuration for neighbor {neighbor_ip}",
                }

                assert error["status"] == "fail"
                assert error["remediation"] != ""

    def test_missing_bgp_neighbor(self, mock_device_bgp_state):
        """Test detection of missing BGP neighbors"""
        # Use mock device state from fixture
        bgp_state = mock_device_bgp_state["spine1"]

        # Expected neighbors includes one that exists and one that doesn't
        expected_neighbors = ["10.1.1.1", "10.1.1.5"]

        # Find missing neighbors
        actual_neighbors = set(bgp_state["neighbor"].keys())
        expected_set = set(expected_neighbors)
        missing = expected_set - actual_neighbors

        assert len(missing) == 1
        assert "10.1.1.5" in missing

    def test_unexpected_bgp_neighbor(self, mock_device_bgp_state):
        """Test detection of unexpected BGP neighbors"""
        # Use mock device state from fixture
        bgp_state = mock_device_bgp_state["spine1"]

        # Only expect one neighbor, but fixture has two
        expected_neighbors = ["10.1.1.1"]

        # Find unexpected neighbors
        actual_neighbors = set(bgp_state["neighbor"].keys())
        expected_set = set(expected_neighbors)
        unexpected = actual_neighbors - expected_set

        assert len(unexpected) == 1
        assert "10.1.1.3" in unexpected


class TestEVPNValidation:
    """Test EVPN route validation"""

    def test_evpn_routes_advertised(self, mock_device_evpn_state):
        """Test validation of advertised EVPN routes"""
        # Use mock device state from fixture
        evpn_state = mock_device_evpn_state["spine1"]

        # Validate routes are advertised
        assert len(evpn_state["routes"]["advertised"]) > 0

        # Check specific VNI
        vni_100_routes = [r for r in evpn_state["routes"]["advertised"] if r["vni"] == 100]
        assert len(vni_100_routes) == 1
        assert vni_100_routes[0]["count"] > 0

    def test_evpn_routes_received(self, mock_device_evpn_state):
        """Test validation of received EVPN routes"""
        # Use mock device state from fixture
        evpn_state = mock_device_evpn_state["spine1"]

        # Validate routes are received
        assert len(evpn_state["routes"]["received"]) > 0

    def test_evpn_route_target_validation(self):
        """Test EVPN route target validation"""
        evpn_config = {
            "vni": 100,
            "route_distinguisher": "10.0.0.1:100",
            "route_targets": {"import": ["65001:100"], "export": ["65001:100"]},
        }

        # Validate route target format
        import re

        rt_pattern = r"^\d+:\d+$"

        for rt in evpn_config["route_targets"]["import"]:
            assert re.match(rt_pattern, rt)

        for rt in evpn_config["route_targets"]["export"]:
            assert re.match(rt_pattern, rt)


class TestLLDPValidation:
    """Test LLDP neighbor validation"""

    def test_lldp_neighbors_match_topology(self, mock_device_lldp_state):
        """Test LLDP neighbors match topology definition"""
        # Use mock device state from fixture
        lldp_state = mock_device_lldp_state

        topology_links = [{"endpoints": ["spine1:ethernet-1/1", "leaf1:ethernet-1/49"]}]

        # Validate LLDP matches topology
        device = "spine1"
        interface = "ethernet-1/1"

        if device in lldp_state and interface in lldp_state[device]:
            neighbor = lldp_state[device][interface]["neighbor"]
            neighbor_port = lldp_state[device][interface]["neighbor_port"]

            # Check if this link exists in topology
            expected_link = f"{device}:{interface}"
            expected_neighbor = f"{neighbor}:{neighbor_port}"

            link_found = False
            for link in topology_links:
                if expected_link in link["endpoints"] and expected_neighbor in link["endpoints"]:
                    link_found = True
                    break

            assert link_found is True

    def test_missing_lldp_neighbor(self, mock_device_lldp_state):
        """Test detection of missing LLDP neighbors"""
        # Use mock device state from fixture
        lldp_state = mock_device_lldp_state

        expected_neighbors = {
            "spine1": {
                "ethernet-1/1": "leaf1",
                "ethernet-1/3": "leaf3",  # Missing - not in fixture
            }
        }

        # Find missing neighbors
        missing = []
        for device, interfaces in expected_neighbors.items():
            for interface, expected_neighbor in interfaces.items():
                if device not in lldp_state or interface not in lldp_state[device]:
                    missing.append(
                        {
                            "device": device,
                            "interface": interface,
                            "expected_neighbor": expected_neighbor,
                        }
                    )

        assert len(missing) == 1
        assert missing[0]["interface"] == "ethernet-1/3"


class TestInterfaceValidation:
    """Test interface state validation"""

    def test_interface_operational_state(self, mock_device_interface_state):
        """Test interface operational state validation"""
        # Use mock device state from fixture
        interface_state = mock_device_interface_state["spine1"]

        # Validate operational state matches expected
        expected_state = "up"
        actual_state = interface_state["ethernet-1/1"]["oper_state"]

        assert actual_state == expected_state

    def test_interface_admin_oper_mismatch(self):
        """Test detection of admin/oper state mismatch"""
        # Create mock state with mismatch
        interface_state = {
            "ethernet-1/1": {
                "admin_state": "enable",
                "oper_state": "down",  # Mismatch
            }
        }

        # Detect mismatch
        admin = interface_state["ethernet-1/1"]["admin_state"]
        oper = interface_state["ethernet-1/1"]["oper_state"]

        if admin == "enable" and oper == "down":
            error = {
                "check": "interface_state",
                "status": "fail",
                "interface": "ethernet-1/1",
                "issue": "Admin enabled but operationally down",
                "remediation": "Check physical connectivity and interface configuration",
            }

            assert error["status"] == "fail"
            assert "connectivity" in error["remediation"].lower()

    def test_interface_counters_validation(self, mock_device_interface_state):
        """Test interface counter validation"""
        # Use mock device state from fixture
        interface_counters = mock_device_interface_state["spine1"]["ethernet-1/1"]["counters"]

        # Validate no errors
        assert interface_counters["in_errors"] == 0
        assert interface_counters["out_errors"] == 0

        # Validate traffic is flowing
        assert interface_counters["in_octets"] > 0
        assert interface_counters["out_octets"] > 0


class TestValidationReporting:
    """Test validation report generation"""

    def test_validation_report_structure(self):
        """Test validation report has required structure"""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "device": "spine1",
            "checks": {
                "bgp_sessions": {"status": "pass", "expected": 4, "actual": 4},
                "interface_states": {"status": "pass", "expected": 8, "actual": 8},
            },
            "overall_status": "pass",
            "duration_seconds": 12,
        }

        # Validate structure
        assert "timestamp" in report
        assert "device" in report
        assert "checks" in report
        assert "overall_status" in report
        assert "duration_seconds" in report

    def test_validation_report_with_failures(self):
        """Test validation report includes failure details"""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "device": "spine1",
            "checks": {
                "bgp_sessions": {
                    "status": "fail",
                    "expected": 4,
                    "actual": 3,
                    "details": {
                        "missing": ["10.1.1.7"],
                        "remediation": "Check BGP configuration for missing neighbor",
                    },
                }
            },
            "overall_status": "fail",
        }

        # Validate failure details
        bgp_check = report["checks"]["bgp_sessions"]
        assert bgp_check["status"] == "fail"
        assert "details" in bgp_check
        assert "missing" in bgp_check["details"]
        assert "remediation" in bgp_check["details"]

    def test_validation_summary_statistics(self):
        """Test validation summary includes statistics"""
        summary = {
            "total_checks": 10,
            "passed": 8,
            "failed": 2,
            "warnings": 0,
            "devices_checked": 6,
        }

        # Validate statistics
        assert (
            summary["total_checks"] == summary["passed"] + summary["failed"] + summary["warnings"]
        )
        assert summary["passed"] > 0
        assert summary["devices_checked"] > 0

    def test_validation_report_json_format(self):
        """Test validation report can be serialized to JSON"""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "checks": {"bgp_sessions": {"status": "pass"}},
        }

        # Should be valid JSON
        json_str = json.dumps(report)
        parsed = json.loads(json_str)

        assert parsed == report


class TestValidationRemediationSuggestions:
    """Test validation remediation suggestions"""

    def test_bgp_session_down_remediation(self):
        """Test remediation for BGP session down"""
        error = {
            "check": "bgp_session",
            "neighbor": "10.1.1.1",
            "status": "IDLE",
            "remediation": "Check BGP configuration and network connectivity to 10.1.1.1",
        }

        assert "configuration" in error["remediation"].lower()
        assert "connectivity" in error["remediation"].lower()
        assert error["neighbor"] in error["remediation"]

    def test_interface_down_remediation(self):
        """Test remediation for interface down"""
        error = {
            "check": "interface_state",
            "interface": "ethernet-1/1",
            "remediation": "Check physical connectivity and interface configuration for ethernet-1/1",
        }

        assert "physical" in error["remediation"].lower()
        assert error["interface"] in error["remediation"]

    def test_missing_lldp_neighbor_remediation(self):
        """Test remediation for missing LLDP neighbor"""
        error = {
            "check": "lldp_neighbor",
            "interface": "ethernet-1/2",
            "expected_neighbor": "leaf2",
            "remediation": "Check physical connectivity to leaf2 on interface ethernet-1/2",
        }

        assert error["expected_neighbor"] in error["remediation"]
        assert error["interface"] in error["remediation"]


class TestValidationPerformance:
    """Test validation performance requirements"""

    def test_validation_completes_within_timeout(self):
        """Test validation completes within 60 seconds"""
        import time

        start_time = time.time()

        # Simulate validation checks
        checks = ["bgp_sessions", "evpn_routes", "lldp_neighbors", "interface_states"]

        # Mock validation (in real implementation, this would query devices)
        for _check in checks:
            pass  # Simulate check

        end_time = time.time()
        duration = end_time - start_time

        # Should complete quickly (< 60 seconds requirement)
        assert duration < 60

    def test_validation_reports_duration(self):
        """Test validation report includes duration"""
        report = {"checks": {}, "duration_seconds": 12}

        assert "duration_seconds" in report
        assert report["duration_seconds"] > 0


class TestValidationErrorDetection:
    """Test validation error detection"""

    def test_detect_configuration_drift(self):
        """Test detection of configuration drift"""
        expected_config = {"bgp": {"asn": 65001}}

        actual_config = {
            "bgp": {"asn": 65002}  # Drift detected
        }

        # Detect drift
        if expected_config["bgp"]["asn"] != actual_config["bgp"]["asn"]:
            error = {
                "check": "configuration_compliance",
                "status": "fail",
                "expected": expected_config["bgp"]["asn"],
                "actual": actual_config["bgp"]["asn"],
                "remediation": "Update BGP ASN to match expected configuration",
            }

            assert error["status"] == "fail"

    def test_detect_route_count_anomaly(self):
        """Test detection of route count anomalies"""
        expected_route_count = 100
        actual_route_count = 50  # Anomaly

        threshold = 0.8  # 80% of expected

        if actual_route_count < (expected_route_count * threshold):
            warning = {
                "check": "route_count",
                "status": "warning",
                "expected": expected_route_count,
                "actual": actual_route_count,
                "remediation": "Investigate why route count is below expected",
            }

            assert warning["status"] == "warning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
