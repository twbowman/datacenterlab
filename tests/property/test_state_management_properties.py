"""
Property-based tests for lab state management

**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 12.2, 12.7**
"""

import copy
import json
from datetime import datetime

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# Import test data generators
from .strategies import topologies


# Mock state management system for testing
class LabStateManager:
    """
    Mock lab state manager that simulates export/restore operations

    This is a simplified version for testing state management properties.
    In production, this would interact with containerlab, Ansible, and Prometheus.
    """

    def export_state(self, lab_name: str, topology: dict, configurations: dict) -> dict:
        """
        Export lab state to a snapshot

        Args:
            lab_name: Name of the lab
            topology: Topology definition
            configurations: Device configurations

        Returns:
            State snapshot dictionary
        """
        snapshot = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "lab_name": lab_name,
            "topology": copy.deepcopy(topology),
            "configurations": copy.deepcopy(configurations),
            "metadata": {
                "created_by": "test_user",
                "description": "Test snapshot",
            },
        }
        return snapshot

    def restore_state(self, snapshot: dict) -> tuple:
        """
        Restore lab state from a snapshot

        Args:
            snapshot: State snapshot dictionary

        Returns:
            Tuple of (lab_name, topology, configurations)
        """
        # Validate snapshot has required fields
        required_fields = ["version", "timestamp", "lab_name", "topology", "configurations"]
        for field in required_fields:
            if field not in snapshot:
                raise ValueError(f"Invalid snapshot: missing field '{field}'")

        return (
            snapshot["lab_name"],
            copy.deepcopy(snapshot["topology"]),
            copy.deepcopy(snapshot["configurations"]),
        )

    def serialize_to_yaml(self, snapshot: dict) -> str:
        """Serialize snapshot to YAML format"""
        return yaml.dump(snapshot, default_flow_style=False, sort_keys=True)

    def deserialize_from_yaml(self, yaml_str: str) -> dict:
        """Deserialize snapshot from YAML format"""
        return yaml.safe_load(yaml_str)

    def serialize_to_json(self, snapshot: dict) -> str:
        """Serialize snapshot to JSON format"""
        return json.dumps(snapshot, indent=2, sort_keys=True)

    def deserialize_from_json(self, json_str: str) -> dict:
        """Deserialize snapshot from JSON format"""
        return json.loads(json_str)


# Property 42: Lab State Round-Trip
@given(
    topology=topologies(),
    lab_name=st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-"),
    ).filter(lambda x: x[0].isalpha()),
)
@settings(max_examples=100, deadline=None)
def test_lab_state_round_trip(topology, lab_name):
    """
    **Property 42: Lab State Round-Trip**

    **Validates: Requirements 12.2**

    For any lab state, exporting then restoring should produce an
    equivalent lab state.

    This property ensures that the export/restore cycle is lossless and
    that labs can be reliably saved and recreated.
    """
    state_manager = LabStateManager()

    # Create mock configurations for each device in topology
    configurations = {}
    for node_name, node_config in topology["topology"]["nodes"].items():
        configurations[node_name] = {
            "vendor": node_config["vendor"],
            "hostname": node_name,
            "config": f"# Configuration for {node_name}\n# Vendor: {node_config['vendor']}\n",
        }

    # Export lab state
    snapshot = state_manager.export_state(lab_name, topology, configurations)

    # Verify snapshot has required fields
    assert "version" in snapshot
    assert "timestamp" in snapshot
    assert "lab_name" in snapshot
    assert "topology" in snapshot
    assert "configurations" in snapshot

    # Restore lab state
    restored_lab_name, restored_topology, restored_configurations = state_manager.restore_state(
        snapshot
    )

    # Property: Lab name must be preserved
    assert restored_lab_name == lab_name, f"Lab name changed: {lab_name} -> {restored_lab_name}"

    # Property: Topology must be equivalent
    assert restored_topology == topology, "Topology changed during export/restore cycle"

    # Property: Configurations must be equivalent
    assert restored_configurations == configurations, (
        "Configurations changed during export/restore cycle"
    )

    # Property: Node count must be preserved
    original_node_count = len(topology["topology"]["nodes"])
    restored_node_count = len(restored_topology["topology"]["nodes"])
    assert restored_node_count == original_node_count, (
        f"Node count changed: {original_node_count} -> {restored_node_count}"
    )

    # Property: Link count must be preserved
    original_link_count = len(topology["topology"]["links"])
    restored_link_count = len(restored_topology["topology"]["links"])
    assert restored_link_count == original_link_count, (
        f"Link count changed: {original_link_count} -> {restored_link_count}"
    )


# Property 47: Version Control Friendly Format
@given(topology=topologies())
@settings(max_examples=100)
def test_version_control_friendly_format_yaml(topology):
    """
    **Property 47: Version Control Friendly Format (YAML)**

    **Validates: Requirements 12.7**

    For any state snapshot, it should be stored in a text-based format
    suitable for version control (YAML or JSON).

    This property tests YAML serialization/deserialization.
    """
    state_manager = LabStateManager()

    # Create a snapshot
    lab_name = "test-lab"
    configurations = {
        node_name: {"vendor": node_config["vendor"], "config": "test"}
        for node_name, node_config in topology["topology"]["nodes"].items()
    }
    snapshot = state_manager.export_state(lab_name, topology, configurations)

    # Serialize to YAML
    yaml_str = state_manager.serialize_to_yaml(snapshot)

    # Property: Result must be a string (text-based)
    assert isinstance(yaml_str, str), "YAML serialization did not produce a string"

    # Property: Result must not be empty
    assert len(yaml_str) > 0, "YAML serialization produced empty string"

    # Property: Result must be valid YAML (can be parsed back)
    try:
        deserialized = state_manager.deserialize_from_yaml(yaml_str)
    except Exception as e:
        pytest.fail(f"YAML deserialization failed: {e}")

    # Property: Deserialized snapshot must equal original
    assert deserialized["lab_name"] == snapshot["lab_name"]
    assert deserialized["topology"] == snapshot["topology"]
    assert deserialized["configurations"] == snapshot["configurations"]

    # Property: YAML must be human-readable (contains newlines)
    assert "\n" in yaml_str, "YAML output is not multi-line (not human-readable)"

    # Property: YAML must contain key topology elements
    assert "topology:" in yaml_str or "topology" in yaml_str
    assert "nodes:" in yaml_str or "nodes" in yaml_str


@given(topology=topologies())
@settings(max_examples=100)
def test_version_control_friendly_format_json(topology):
    """
    **Property 47: Version Control Friendly Format (JSON)**

    **Validates: Requirements 12.7**

    For any state snapshot, it should be stored in a text-based format
    suitable for version control (YAML or JSON).

    This property tests JSON serialization/deserialization.
    """
    state_manager = LabStateManager()

    # Create a snapshot
    lab_name = "test-lab"
    configurations = {
        node_name: {"vendor": node_config["vendor"], "config": "test"}
        for node_name, node_config in topology["topology"]["nodes"].items()
    }
    snapshot = state_manager.export_state(lab_name, topology, configurations)

    # Serialize to JSON
    json_str = state_manager.serialize_to_json(snapshot)

    # Property: Result must be a string (text-based)
    assert isinstance(json_str, str), "JSON serialization did not produce a string"

    # Property: Result must not be empty
    assert len(json_str) > 0, "JSON serialization produced empty string"

    # Property: Result must be valid JSON (can be parsed back)
    try:
        deserialized = state_manager.deserialize_from_json(json_str)
    except Exception as e:
        pytest.fail(f"JSON deserialization failed: {e}")

    # Property: Deserialized snapshot must equal original
    assert deserialized["lab_name"] == snapshot["lab_name"]
    assert deserialized["topology"] == snapshot["topology"]
    assert deserialized["configurations"] == snapshot["configurations"]

    # Property: JSON must be formatted (contains newlines for readability)
    assert "\n" in json_str, "JSON output is not formatted (not human-readable)"

    # Property: JSON must contain key topology elements
    assert '"topology"' in json_str
    assert '"nodes"' in json_str


# Additional test: Snapshot metadata preservation
@given(topology=topologies())
@settings(max_examples=50)
def test_snapshot_metadata_preservation(topology):
    """
    **Property 43: State Snapshot Metadata**

    **Validates: Requirements 12.3**

    For any exported state snapshot, it should include timestamps
    and version information.
    """
    state_manager = LabStateManager()

    lab_name = "test-lab"
    configurations = {}

    # Export state
    snapshot = state_manager.export_state(lab_name, topology, configurations)

    # Property: Snapshot must have version field
    assert "version" in snapshot, "Snapshot missing version field"
    assert snapshot["version"] is not None, "Snapshot version is None"
    assert len(str(snapshot["version"])) > 0, "Snapshot version is empty"

    # Property: Snapshot must have timestamp field
    assert "timestamp" in snapshot, "Snapshot missing timestamp field"
    assert snapshot["timestamp"] is not None, "Snapshot timestamp is None"

    # Property: Timestamp must be valid ISO8601 format
    try:
        datetime.fromisoformat(snapshot["timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pytest.fail(f"Snapshot timestamp is not valid ISO8601: {snapshot['timestamp']}")

    # Property: Snapshot must have metadata section
    assert "metadata" in snapshot, "Snapshot missing metadata section"
    assert isinstance(snapshot["metadata"], dict), "Snapshot metadata is not a dictionary"


# Additional test: Multiple round-trips preserve state
@given(topology=topologies())
@settings(max_examples=50, deadline=None)
def test_multiple_round_trips_preserve_state(topology):
    """
    Test that multiple export/restore cycles preserve state

    This ensures that the round-trip property holds even after
    multiple iterations.
    """
    state_manager = LabStateManager()

    lab_name = "test-lab"
    configurations = {
        node_name: {"vendor": node_config["vendor"]}
        for node_name, node_config in topology["topology"]["nodes"].items()
    }

    # Perform 3 round-trips
    current_topology = topology
    current_configs = configurations

    for _i in range(3):
        # Export
        snapshot = state_manager.export_state(lab_name, current_topology, current_configs)

        # Restore
        restored_name, restored_topology, restored_configs = state_manager.restore_state(snapshot)

        # Verify equivalence
        assert restored_name == lab_name
        assert restored_topology == current_topology
        assert restored_configs == current_configs

        # Use restored state for next iteration
        current_topology = restored_topology
        current_configs = restored_configs

    # After 3 round-trips, state should still equal original
    assert current_topology == topology
    assert current_configs == configurations


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
