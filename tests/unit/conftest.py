"""
Pytest configuration for unit tests

Provides fixtures and configuration for unit testing.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add scripts directory to path
scripts_dir = project_root / 'scripts'
sys.path.insert(0, str(scripts_dir))

# Add ansible plugins to path
ansible_plugins = project_root / 'ansible' / 'plugins' / 'inventory'
sys.path.insert(0, str(ansible_plugins))

ansible_filters = project_root / 'ansible' / 'filter_plugins'
sys.path.insert(0, str(ansible_filters))


@pytest.fixture
def sample_topology():
    """Provide a sample topology for testing"""
    return {
        'name': 'test-lab',
        'topology': {
            'nodes': {
                'spine1': {
                    'kind': 'nokia_srlinux',
                    'image': 'ghcr.io/nokia/srlinux:latest',
                    'type': 'ixrd3'
                },
                'leaf1': {
                    'kind': 'nokia_srlinux',
                    'image': 'ghcr.io/nokia/srlinux:latest',
                    'type': 'ixrd3'
                }
            },
            'links': [
                {
                    'endpoints': ['spine1:e1-1', 'leaf1:e1-49']
                }
            ]
        }
    }


@pytest.fixture
def sample_bgp_config():
    """Provide a sample BGP configuration for testing"""
    return {
        'asn': 65001,
        'router_id': '10.0.0.1',
        'neighbors': [
            {
                'ip': '10.1.1.1',
                'peer_as': 65011,
                'group': 'leafs',
                'description': 'to leaf1'
            }
        ]
    }


@pytest.fixture
def sample_interface_config():
    """Provide a sample interface configuration for testing"""
    return {
        'name': 'ethernet-1/1',
        'description': 'to leaf1',
        'enabled': True,
        'ipv4_address': '10.1.1.0',
        'ipv4_prefix_length': 31,
        'mtu': 9000
    }


@pytest.fixture
def sample_metric():
    """Provide a sample metric for testing"""
    return {
        'name': 'network_interface_in_octets',
        'value': 1234567890,
        'timestamp': 1705315800,
        'labels': {
            'source': 'spine1',
            'vendor': 'nokia',
            'interface': 'eth1_1',
            'role': 'spine'
        }
    }


@pytest.fixture
def sample_validation_report():
    """Provide a sample validation report for testing"""
    return {
        'timestamp': '2024-01-15T10:30:00Z',
        'device': 'spine1',
        'checks': {
            'bgp_sessions': {
                'status': 'pass',
                'expected': 4,
                'actual': 4,
                'details': []
            },
            'interface_states': {
                'status': 'pass',
                'expected': 8,
                'actual': 8,
                'details': []
            }
        },
        'overall_status': 'pass',
        'duration_seconds': 12
    }


@pytest.fixture
def sample_lab_state():
    """Provide a sample lab state for testing"""
    return {
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
        },
        'configurations': {
            'spine1': {
                'vendor': 'nokia',
                'os': 'srlinux',
                'config': '{"interface": []}'
            }
        },
        'metadata': {
            'created_by': 'test@example.com',
            'description': 'Test lab snapshot',
            'tags': ['test']
        }
    }
