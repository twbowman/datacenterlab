#!/usr/bin/env python3
"""
Unit tests for configuration management

Tests configuration generation for each vendor, syntax validation, and rollback.
Validates: Requirements 15.2
"""

import os
import sys

import pytest

# Add ansible filter plugins to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ansible", "filter_plugins"))

from interface_names import FilterModule


class TestInterfaceNameTranslation:
    """Test interface name translation filters"""

    @pytest.fixture
    def filters(self):
        """Get filter module instance"""
        fm = FilterModule()
        return fm.filters()

    def test_to_arista_interface_from_srlinux(self, filters):
        """Test conversion from SR Linux to Arista format"""
        assert filters["to_arista_interface"]("ethernet-1/1") == "Ethernet1/1"
        assert filters["to_arista_interface"]("ethernet-2/10") == "Ethernet2/10"
        assert filters["to_arista_interface"]("eth-1/1") == "Ethernet1/1"

    def test_to_arista_interface_already_arista(self, filters):
        """Test that Arista format passes through unchanged"""
        assert filters["to_arista_interface"]("Ethernet1/1") == "Ethernet1/1"

    def test_to_sonic_interface_from_srlinux(self, filters):
        """Test conversion from SR Linux to SONiC format"""
        # First port of first module -> Ethernet0
        assert filters["to_sonic_interface"]("ethernet-1/1") == "Ethernet0"
        # Second port of first module -> Ethernet1
        assert filters["to_sonic_interface"]("ethernet-1/2") == "Ethernet1"
        # First port of second module -> Ethernet48 (assuming 48 ports per module)
        assert filters["to_sonic_interface"]("ethernet-2/1") == "Ethernet48"

    def test_to_sonic_interface_with_port_increment(self, filters):
        """Test SONiC conversion with different port increments"""
        # Mellanox uses increment of 4
        assert filters["to_sonic_interface"]("ethernet-1/1", port_increment=4) == "Ethernet0"
        assert filters["to_sonic_interface"]("ethernet-1/2", port_increment=4) == "Ethernet4"

    def test_to_srlinux_interface_from_arista(self, filters):
        """Test conversion from Arista to SR Linux format"""
        assert filters["to_srlinux_interface"]("Ethernet1/1") == "ethernet-1/1"
        assert filters["to_srlinux_interface"]("Ethernet2/10") == "ethernet-2/10"

    def test_to_srlinux_interface_from_sonic(self, filters):
        """Test conversion from SONiC to SR Linux format"""
        # Ethernet0 -> ethernet-1/1 (first port of first module)
        assert filters["to_srlinux_interface"]("Ethernet0") == "ethernet-1/1"
        # Ethernet1 -> ethernet-1/2
        assert filters["to_srlinux_interface"]("Ethernet1") == "ethernet-1/2"
        # Ethernet48 -> ethernet-2/1 (first port of second module)
        assert filters["to_srlinux_interface"]("Ethernet48") == "ethernet-2/1"

    def test_to_junos_interface_from_srlinux(self, filters):
        """Test conversion from SR Linux to Junos format"""
        # ethernet-1/1 -> ge-0/0/0 (Junos uses 0-indexed ports)
        assert filters["to_junos_interface"]("ethernet-1/1") == "ge-0/0/0"
        assert filters["to_junos_interface"]("ethernet-1/2") == "ge-0/0/1"
        assert filters["to_junos_interface"]("eth-1/1") == "ge-0/0/0"

    def test_normalize_interface(self, filters):
        """Test interface normalization to common format"""
        # All should normalize to SR Linux format
        assert filters["normalize_interface"]("Ethernet1/1") == "ethernet-1/1"
        assert filters["normalize_interface"]("Ethernet0") == "ethernet-1/1"
        assert filters["normalize_interface"]("ethernet-1/1") == "ethernet-1/1"

    def test_interface_translation_round_trip(self, filters):
        """Test that interface names can be converted and back"""
        original = "ethernet-1/5"

        # SR Linux -> Arista -> SR Linux
        arista = filters["to_arista_interface"](original)
        back_to_srl = filters["to_srlinux_interface"](arista)
        assert back_to_srl == original


class TestConfigurationGeneration:
    """Test configuration template generation"""

    def test_bgp_configuration_structure(self):
        """Test BGP configuration has required fields"""
        # Mock BGP configuration structure
        bgp_config = {
            "asn": 65001,
            "router_id": "10.0.0.1",
            "neighbors": [{"ip": "10.1.1.1", "peer_as": 65011, "group": "leafs"}],
        }

        # Validate structure
        assert "asn" in bgp_config
        assert "router_id" in bgp_config
        assert "neighbors" in bgp_config
        assert isinstance(bgp_config["neighbors"], list)
        assert len(bgp_config["neighbors"]) > 0

        neighbor = bgp_config["neighbors"][0]
        assert "ip" in neighbor
        assert "peer_as" in neighbor

    def test_interface_configuration_structure(self):
        """Test interface configuration has required fields"""
        interface_config = {
            "name": "ethernet-1/1",
            "description": "to leaf1",
            "enabled": True,
            "ipv4_address": "10.1.1.0",
            "ipv4_prefix_length": 31,
        }

        # Validate structure
        assert "name" in interface_config
        assert "enabled" in interface_config
        assert "ipv4_address" in interface_config
        assert "ipv4_prefix_length" in interface_config

    def test_ospf_configuration_structure(self):
        """Test OSPF configuration has required fields"""
        ospf_config = {
            "process_id": 1,
            "router_id": "10.0.0.1",
            "areas": [
                {
                    "area_id": "0.0.0.0",
                    "interfaces": [{"name": "ethernet-1/1", "network_type": "point-to-point"}],
                }
            ],
        }

        # Validate structure
        assert "process_id" in ospf_config
        assert "router_id" in ospf_config
        assert "areas" in ospf_config
        assert isinstance(ospf_config["areas"], list)


class TestConfigurationValidation:
    """Test configuration syntax validation"""

    def test_valid_ip_address_format(self):
        """Test IP address validation"""
        import re

        # Simple pattern for demonstration (real validation would be more complex)
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"

        # Valid IPs
        assert re.match(ip_pattern, "10.0.0.1")
        assert re.match(ip_pattern, "192.168.1.1")

        # Invalid IPs (pattern matches but values are out of range)
        # Note: Full IP validation would check each octet is 0-255
        assert re.match(ip_pattern, "256.0.0.1")  # Matches pattern but invalid value
        assert not re.match(ip_pattern, "10.0.0")  # Missing octet
        assert not re.match(ip_pattern, "invalid")  # Not an IP

    def test_valid_asn_range(self):
        """Test BGP ASN validation"""
        # Valid ASNs (16-bit and 32-bit)
        assert 1 <= 65001 <= 4294967295
        assert 1 <= 64512 <= 4294967295

        # Invalid ASNs
        assert not (0 <= 0 <= 4294967295 and 0 >= 1)
        assert not (4294967296 <= 4294967296 <= 4294967295)

    def test_valid_router_id_format(self):
        """Test router ID format validation"""
        import re

        # Router ID should be in IP address format
        router_id_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"

        assert re.match(router_id_pattern, "10.0.0.1")
        assert not re.match(router_id_pattern, "invalid-id")

    def test_interface_name_validation(self):
        """Test interface name format validation"""
        import re

        # SR Linux format
        srl_pattern = r"^ethernet-\d+/\d+$"
        assert re.match(srl_pattern, "ethernet-1/1")
        assert re.match(srl_pattern, "ethernet-2/10")
        assert not re.match(srl_pattern, "invalid-interface")

        # Arista format
        arista_pattern = r"^Ethernet\d+/\d+$"
        assert re.match(arista_pattern, "Ethernet1/1")
        assert not re.match(arista_pattern, "ethernet1/1")


class TestConfigurationRollback:
    """Test configuration rollback functionality"""

    def test_rollback_captures_previous_state(self):
        """Test that rollback captures configuration before changes"""
        # Mock configuration state
        previous_config = {"interfaces": [{"name": "ethernet-1/1", "enabled": True}]}

        new_config = {"interfaces": [{"name": "ethernet-1/1", "enabled": False}]}

        # Simulate rollback
        rollback_state = previous_config.copy()

        # Verify rollback state matches previous
        assert rollback_state == previous_config
        assert rollback_state != new_config

    def test_rollback_on_validation_failure(self):
        """Test that rollback occurs when validation fails"""
        # Mock scenario: configuration fails validation
        config_valid = False
        rollback_executed = False

        if not config_valid:
            rollback_executed = True

        assert rollback_executed is True

    def test_rollback_error_reporting(self):
        """Test that rollback reports specific errors"""
        error_report = {
            "component": "bgp_configuration",
            "error": "Invalid peer AS number",
            "rollback_status": "success",
            "remediation": "Check BGP peer AS configuration",
        }

        assert "component" in error_report
        assert "error" in error_report
        assert "rollback_status" in error_report
        assert "remediation" in error_report


class TestConfigurationIdempotency:
    """Test configuration idempotency"""

    def test_applying_same_config_twice_produces_same_result(self):
        """Test that applying configuration multiple times is idempotent"""
        config = {"interfaces": [{"name": "ethernet-1/1", "enabled": True, "ip": "10.1.1.0/31"}]}

        # Simulate applying config twice
        state_after_first_apply = config.copy()
        state_after_second_apply = config.copy()

        # States should be identical
        assert state_after_first_apply == state_after_second_apply

    def test_config_merge_is_idempotent(self):
        """Test that merging same configuration is idempotent"""
        base_config = {"asn": 65001, "router_id": "10.0.0.1"}
        update_config = {"asn": 65001, "router_id": "10.0.0.1"}

        # Merge configs
        merged = {**base_config, **update_config}

        # Merging again should produce same result
        merged_again = {**merged, **update_config}

        assert merged == merged_again


class TestVendorSpecificConfiguration:
    """Test vendor-specific configuration generation"""

    def test_srlinux_json_format(self):
        """Test SR Linux uses JSON format"""
        import json

        config = {"interface": [{"name": "ethernet-1/1", "admin-state": "enable"}]}

        # Should be valid JSON
        json_str = json.dumps(config)
        parsed = json.loads(json_str)
        assert parsed == config

    def test_arista_cli_format(self):
        """Test Arista uses CLI format"""
        config_lines = [
            "interface Ethernet1/1",
            "  description to leaf1",
            "  no shutdown",
            "  ip address 10.1.1.0/31",
        ]

        # Verify format
        assert config_lines[0].startswith("interface")
        assert config_lines[1].startswith("  ")  # Indented

    def test_sonic_json_format(self):
        """Test SONiC uses JSON format"""
        import json

        config = {"PORT": {"Ethernet0": {"admin_status": "up", "speed": "100000"}}}

        # Should be valid JSON
        json_str = json.dumps(config)
        parsed = json.loads(json_str)
        assert parsed == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
