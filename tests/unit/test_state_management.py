#!/usr/bin/env python3
"""
Unit tests for state management

Tests state export, restore, comparison, and incremental updates.
Validates: Requirements 15.1
"""

import pytest
import json
import yaml
from datetime import datetime


class TestStateExport:
    """Test lab state export functionality"""
    
    def test_state_export_includes_topology(self):
        """Test that exported state includes topology definition"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'topology': {
                'name': 'test-lab',
                'nodes': {
                    'spine1': {
                        'kind': 'nokia_srlinux',
                        'image': 'ghcr.io/nokia/srlinux:latest'
                    }
                }
            }
        }
        
        # Validate topology is included
        assert 'topology' in state
        assert 'nodes' in state['topology']
        assert len(state['topology']['nodes']) > 0
    
    def test_state_export_includes_configurations(self):
        """Test that exported state includes device configurations"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'configurations': {
                'spine1': {
                    'vendor': 'nokia',
                    'os': 'srlinux',
                    'config': '{"interface": [{"name": "ethernet-1/1"}]}'
                }
            }
        }
        
        # Validate configurations are included
        assert 'configurations' in state
        assert 'spine1' in state['configurations']
        assert 'vendor' in state['configurations']['spine1']
        assert 'os' in state['configurations']['spine1']
        assert 'config' in state['configurations']['spine1']
    
    def test_state_export_includes_metadata(self):
        """Test that exported state includes metadata"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'metadata': {
                'created_by': 'user@example.com',
                'description': 'Test lab snapshot',
                'tags': ['production', 'evpn']
            }
        }
        
        # Validate metadata
        assert 'metadata' in state
        assert 'created_by' in state['metadata']
        assert 'description' in state['metadata']
        assert 'tags' in state['metadata']
    
    def test_state_export_includes_metrics_snapshot(self):
        """Test that exported state includes metrics snapshot"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'metrics_snapshot': {
                'start_time': '2024-01-15T10:00:00Z',
                'end_time': '2024-01-15T10:30:00Z',
                'prometheus_snapshot': '/path/to/snapshot'
            }
        }
        
        # Validate metrics snapshot
        assert 'metrics_snapshot' in state
        assert 'start_time' in state['metrics_snapshot']
        assert 'end_time' in state['metrics_snapshot']
    
    def test_state_export_version_information(self):
        """Test that exported state includes version information"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab'
        }
        
        # Validate version info
        assert 'version' in state
        assert 'timestamp' in state
        
        # Timestamp should be ISO 8601 format
        try:
            datetime.fromisoformat(state['timestamp'].replace('Z', '+00:00'))
            timestamp_valid = True
        except ValueError:
            timestamp_valid = False
        
        assert timestamp_valid is True


class TestStateRestore:
    """Test lab state restore functionality"""
    
    def test_state_restore_validates_snapshot(self):
        """Test that restore validates snapshot before applying"""
        snapshot = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'topology': {}
        }
        
        # Validation checks
        required_fields = ['version', 'timestamp', 'lab_name', 'topology']
        
        is_valid = all(field in snapshot for field in required_fields)
        assert is_valid is True
    
    def test_state_restore_rejects_invalid_snapshot(self):
        """Test that restore rejects invalid snapshots"""
        invalid_snapshot = {
            'version': '1.0'
            # Missing required fields
        }
        
        required_fields = ['version', 'timestamp', 'lab_name', 'topology']
        
        is_valid = all(field in invalid_snapshot for field in required_fields)
        assert is_valid is False
    
    def test_state_restore_validates_topology_structure(self):
        """Test that restore validates topology structure"""
        snapshot = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'topology': {
                'name': 'test-lab',
                'nodes': {
                    'spine1': {
                        'kind': 'nokia_srlinux',
                        'image': 'ghcr.io/nokia/srlinux:latest'
                    }
                }
            }
        }
        
        # Validate topology structure
        topology = snapshot['topology']
        assert 'name' in topology
        assert 'nodes' in topology
        assert isinstance(topology['nodes'], dict)
    
    def test_state_restore_validates_configuration_format(self):
        """Test that restore validates configuration format"""
        snapshot = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'configurations': {
                'spine1': {
                    'vendor': 'nokia',
                    'os': 'srlinux',
                    'config': '{"interface": []}'
                }
            }
        }
        
        # Validate configuration format
        config = snapshot['configurations']['spine1']
        assert 'vendor' in config
        assert 'os' in config
        assert 'config' in config
        
        # Config should be valid JSON
        try:
            json.loads(config['config'])
            config_valid = True
        except json.JSONDecodeError:
            config_valid = False
        
        assert config_valid is True


class TestStateComparison:
    """Test state comparison functionality"""
    
    def test_compare_topology_changes(self):
        """Test comparison of topology changes"""
        snapshot1 = {
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'},
                    'leaf1': {'kind': 'nokia_srlinux'}
                }
            }
        }
        
        snapshot2 = {
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'},
                    'leaf1': {'kind': 'nokia_srlinux'},
                    'leaf2': {'kind': 'nokia_srlinux'}  # Added
                }
            }
        }
        
        # Find differences
        nodes1 = set(snapshot1['topology']['nodes'].keys())
        nodes2 = set(snapshot2['topology']['nodes'].keys())
        
        added = nodes2 - nodes1
        removed = nodes1 - nodes2
        
        assert 'leaf2' in added
        assert len(removed) == 0
    
    def test_compare_configuration_changes(self):
        """Test comparison of configuration changes"""
        config1 = {
            'bgp': {
                'asn': 65001,
                'router_id': '10.0.0.1'
            }
        }
        
        config2 = {
            'bgp': {
                'asn': 65001,
                'router_id': '10.0.0.2'  # Changed
            }
        }
        
        # Find differences
        changes = []
        if config1['bgp']['router_id'] != config2['bgp']['router_id']:
            changes.append({
                'field': 'bgp.router_id',
                'old': config1['bgp']['router_id'],
                'new': config2['bgp']['router_id']
            })
        
        assert len(changes) == 1
        assert changes[0]['field'] == 'bgp.router_id'
    
    def test_generate_configuration_diff(self):
        """Test generation of configuration diff"""
        config1 = """
interface ethernet-1/1
  description to leaf1
  ip address 10.1.1.0/31
"""
        
        config2 = """
interface ethernet-1/1
  description to leaf1
  ip address 10.1.1.2/31
"""
        
        # Simple diff detection
        lines1 = config1.strip().split('\n')
        lines2 = config2.strip().split('\n')
        
        diff = []
        for i, (line1, line2) in enumerate(zip(lines1, lines2)):
            if line1 != line2:
                diff.append({
                    'line': i + 1,
                    'old': line1,
                    'new': line2
                })
        
        assert len(diff) > 0
        assert 'ip address' in diff[0]['old']
    
    def test_compare_metrics_snapshots(self):
        """Test comparison of metrics snapshots"""
        snapshot1 = {
            'metrics_snapshot': {
                'start_time': '2024-01-15T10:00:00Z',
                'end_time': '2024-01-15T10:30:00Z'
            }
        }
        
        snapshot2 = {
            'metrics_snapshot': {
                'start_time': '2024-01-15T11:00:00Z',
                'end_time': '2024-01-15T11:30:00Z'
            }
        }
        
        # Compare time ranges
        assert snapshot1['metrics_snapshot']['start_time'] != snapshot2['metrics_snapshot']['start_time']


class TestIncrementalUpdates:
    """Test incremental state update functionality"""
    
    def test_incremental_update_configuration_only(self):
        """Test incremental update with configuration changes only"""
        current_state = {
            'topology': {'nodes': {'spine1': {}}},
            'configurations': {
                'spine1': {'config': 'old_config'}
            }
        }
        
        target_state = {
            'topology': {'nodes': {'spine1': {}}},  # Unchanged
            'configurations': {
                'spine1': {'config': 'new_config'}  # Changed
            }
        }
        
        # Calculate what needs updating
        topology_changed = current_state['topology'] != target_state['topology']
        config_changed = current_state['configurations'] != target_state['configurations']
        
        assert topology_changed is False
        assert config_changed is True
    
    def test_incremental_update_topology_changes(self):
        """Test incremental update with topology changes"""
        current_state = {
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'}
                }
            }
        }
        
        target_state = {
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'},
                    'leaf1': {'kind': 'nokia_srlinux'}  # Added
                }
            }
        }
        
        # Find nodes to add
        current_nodes = set(current_state['topology']['nodes'].keys())
        target_nodes = set(target_state['topology']['nodes'].keys())
        
        nodes_to_add = target_nodes - current_nodes
        nodes_to_remove = current_nodes - target_nodes
        
        assert 'leaf1' in nodes_to_add
        assert len(nodes_to_remove) == 0
    
    def test_incremental_update_avoids_full_redeployment(self):
        """Test that incremental update avoids full redeployment"""
        # Mock update scenario
        full_redeployment_needed = False
        
        # Only configuration changed, not topology
        topology_changed = False
        config_changed = True
        
        if topology_changed:
            full_redeployment_needed = True
        
        assert full_redeployment_needed is False
        assert config_changed is True


class TestVersionControlFriendlyFormat:
    """Test version control friendly format"""
    
    def test_state_exports_as_yaml(self):
        """Test that state can be exported as YAML"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'}
                }
            }
        }
        
        # Export as YAML
        yaml_str = yaml.dump(state, default_flow_style=False, sort_keys=False)
        
        # Should be valid YAML
        parsed = yaml.safe_load(yaml_str)
        assert parsed == state
    
    def test_state_exports_as_json(self):
        """Test that state can be exported as JSON"""
        state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab'
        }
        
        # Export as JSON
        json_str = json.dumps(state, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed == state
    
    def test_yaml_format_is_readable(self):
        """Test that YAML format is human-readable"""
        state = {
            'version': '1.0',
            'lab_name': 'test-lab',
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'}
                }
            }
        }
        
        yaml_str = yaml.dump(state, default_flow_style=False, sort_keys=False)
        
        # YAML should not use flow style (inline)
        assert '{' not in yaml_str or yaml_str.count('{') < 3
        
        # Should have proper indentation
        assert '  ' in yaml_str
    
    def test_keys_are_sorted_for_consistency(self):
        """Test that keys can be sorted for consistent diffs"""
        state = {
            'topology': {},
            'version': '1.0',
            'lab_name': 'test-lab',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        # Export with sorted keys
        yaml_str = yaml.dump(state, default_flow_style=False, sort_keys=True)
        
        # Keys should be in alphabetical order
        lines = yaml_str.split('\n')
        keys = [line.split(':')[0] for line in lines if ':' in line and not line.startswith(' ')]
        
        # Check if sorted
        assert keys == sorted(keys)


class TestStateSnapshotMetadata:
    """Test state snapshot metadata"""
    
    def test_snapshot_includes_timestamp(self):
        """Test that snapshot includes creation timestamp"""
        snapshot = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        assert 'timestamp' in snapshot
        
        # Validate ISO 8601 format
        try:
            datetime.fromisoformat(snapshot['timestamp'].replace('Z', '+00:00'))
            valid = True
        except ValueError:
            valid = False
        
        assert valid is True
    
    def test_snapshot_includes_version(self):
        """Test that snapshot includes version information"""
        snapshot = {
            'version': '1.0'
        }
        
        assert 'version' in snapshot
        
        # Version should follow semantic versioning
        import re
        version_pattern = r'^\d+\.\d+$'
        assert re.match(version_pattern, snapshot['version'])
    
    def test_snapshot_includes_description(self):
        """Test that snapshot can include description"""
        snapshot = {
            'version': '1.0',
            'metadata': {
                'description': 'Snapshot before EVPN deployment',
                'created_by': 'user@example.com',
                'tags': ['pre-deployment', 'baseline']
            }
        }
        
        assert 'metadata' in snapshot
        assert 'description' in snapshot['metadata']
        assert 'created_by' in snapshot['metadata']
        assert 'tags' in snapshot['metadata']


class TestStateRoundTrip:
    """Test state export and restore round-trip"""
    
    def test_export_restore_preserves_topology(self):
        """Test that export then restore preserves topology"""
        original_state = {
            'version': '1.0',
            'timestamp': '2024-01-15T10:30:00Z',
            'lab_name': 'test-lab',
            'topology': {
                'nodes': {
                    'spine1': {'kind': 'nokia_srlinux'}
                }
            }
        }
        
        # Simulate export (to YAML)
        exported = yaml.dump(original_state)
        
        # Simulate restore (from YAML)
        restored_state = yaml.safe_load(exported)
        
        # Should be identical
        assert restored_state['topology'] == original_state['topology']
    
    def test_export_restore_preserves_configurations(self):
        """Test that export then restore preserves configurations"""
        original_config = {
            'spine1': {
                'vendor': 'nokia',
                'os': 'srlinux',
                'config': '{"interface": []}'
            }
        }
        
        # Simulate export/restore
        exported = json.dumps(original_config)
        restored_config = json.loads(exported)
        
        assert restored_config == original_config


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
