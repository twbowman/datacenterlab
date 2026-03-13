"""
Pytest configuration for unit tests

Provides fixtures and configuration for unit testing.
Includes comprehensive mocking infrastructure to eliminate external dependencies.
"""

import pytest
import sys
import os
from pathlib import Path
from io import StringIO
from unittest.mock import Mock, MagicMock, patch, mock_open
import yaml
import json

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


# ============================================================================
# Mock File Operations Fixtures
# ============================================================================

@pytest.fixture
def mock_topology_file():
    """Provide mock topology file content for testing"""
    return """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd3
    leaf1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd3
  links:
    - endpoints: ["spine1:e1-1", "leaf1:e1-49"]
"""


@pytest.fixture
def mock_yaml_load(monkeypatch):
    """Mock yaml.safe_load to return test data without file I/O"""
    def mock_load(stream):
        # If stream is a string or StringIO, parse it normally
        if isinstance(stream, (str, StringIO)):
            return yaml.safe_load(stream)
        # If it's a file handle, return mock topology data
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
                    {'endpoints': ['spine1:e1-1', 'leaf1:e1-49']}
                ]
            }
        }
    
    monkeypatch.setattr(yaml, 'safe_load', mock_load)
    return mock_load


@pytest.fixture
def mock_file_operations(monkeypatch, mock_topology_file):
    """Mock file operations globally for tests"""
    # Mock Path.exists() to return True for topology files
    original_exists = Path.exists
    
    def mock_exists(self):
        path_str = str(self)
        if 'topology' in path_str or 'config' in path_str:
            return True
        return original_exists(self)
    
    monkeypatch.setattr(Path, 'exists', mock_exists)
    
    # Mock Path.read_text() to return test data
    def mock_read_text(self, encoding='utf-8'):
        path_str = str(self)
        if 'topology' in path_str:
            return mock_topology_file
        return ""
    
    monkeypatch.setattr(Path, 'read_text', mock_read_text)
    
    # Mock open() to return StringIO with test data
    original_open = open
    
    def mock_open_func(file, mode='r', *args, **kwargs):
        file_str = str(file)
        if 'topology' in file_str and 'r' in mode:
            return StringIO(mock_topology_file)
        elif 'w' in mode or 'a' in mode:
            # Return a StringIO for write operations
            return StringIO()
        return original_open(file, mode, *args, **kwargs)
    
    monkeypatch.setattr('builtins.open', mock_open_func)
    
    return {
        'exists': mock_exists,
        'read_text': mock_read_text,
        'open': mock_open_func
    }


# ============================================================================
# Mock Subprocess Operations Fixtures
# ============================================================================

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess operations"""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Success"
    mock_result.stderr = ""
    
    def mock_run(*args, **kwargs):
        return mock_result
    
    def mock_popen(*args, **kwargs):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ("Success", "")
        mock_proc.wait.return_value = 0
        return mock_proc
    
    import subprocess
    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr(subprocess, 'Popen', mock_popen)
    
    return {
        'run': mock_run,
        'popen': mock_popen,
        'result': mock_result
    }


@pytest.fixture
def mock_containerlab_cli(mock_subprocess):
    """Mock containerlab CLI commands"""
    def mock_clab_command(command, *args, **kwargs):
        if 'deploy' in command:
            mock_subprocess['result'].stdout = "Lab deployed successfully"
        elif 'destroy' in command:
            mock_subprocess['result'].stdout = "Lab destroyed successfully"
        elif 'inspect' in command:
            mock_subprocess['result'].stdout = json.dumps({
                'name': 'test-lab',
                'containers': [
                    {'name': 'spine1', 'state': 'running'},
                    {'name': 'leaf1', 'state': 'running'}
                ]
            })
        return mock_subprocess['result']
    
    return mock_clab_command


@pytest.fixture
def mock_docker_commands(mock_subprocess):
    """Mock docker CLI commands"""
    def mock_docker_command(command, *args, **kwargs):
        if 'ps' in command:
            mock_subprocess['result'].stdout = "spine1\nleaf1"
        elif 'inspect' in command:
            mock_subprocess['result'].stdout = json.dumps([{
                'State': {'Running': True},
                'NetworkSettings': {'IPAddress': '172.20.20.10'}
            }])
        return mock_subprocess['result']
    
    return mock_docker_command


# ============================================================================
# Mock Network Operations Fixtures
# ============================================================================

@pytest.fixture
def mock_gnmi_connection():
    """Mock gNMI/gRPC connection"""
    mock_conn = MagicMock()
    
    # Mock channel
    mock_channel = MagicMock()
    mock_conn.channel = mock_channel
    
    # Mock subscription
    mock_subscription = MagicMock()
    mock_subscription.subscribe.return_value = iter([
        {
            'update': {
                'path': '/interfaces/interface/state/counters',
                'val': {'in-octets': 1234567890, 'out-octets': 9876543210}
            }
        }
    ])
    mock_conn.subscribe = mock_subscription.subscribe
    
    # Mock get
    def mock_get(path):
        return {
            'notification': [{
                'update': [{
                    'path': path,
                    'val': {'state': 'up'}
                }]
            }]
        }
    
    mock_conn.get = mock_get
    
    return mock_conn


@pytest.fixture
def mock_ssh_connection():
    """Mock SSH connection to devices"""
    mock_ssh = MagicMock()
    
    # Mock connect
    mock_ssh.connect.return_value = True
    
    # Mock command execution
    def mock_exec_command(command):
        stdout = MagicMock()
        stderr = MagicMock()
        
        if 'show bgp' in command:
            stdout.read.return_value = b'BGP neighbor is 10.1.1.1, remote AS 65011, state Established'
        elif 'show interface' in command:
            stdout.read.return_value = b'ethernet-1/1 is up, line protocol is up'
        else:
            stdout.read.return_value = b'Command output'
        
        stderr.read.return_value = b''
        
        return (MagicMock(), stdout, stderr)
    
    mock_ssh.exec_command = mock_exec_command
    
    # Mock close
    mock_ssh.close.return_value = None
    
    return mock_ssh


@pytest.fixture
def mock_netconf_connection():
    """Mock NETCONF connection"""
    mock_nc = MagicMock()
    
    # Mock connect
    mock_nc.connect.return_value = True
    
    # Mock get_config
    def mock_get_config(source='running'):
        return """
        <data>
            <interfaces>
                <interface>
                    <name>ethernet-1/1</name>
                    <admin-state>enable</admin-state>
                    <oper-state>up</oper-state>
                </interface>
            </interfaces>
        </data>
        """
    
    mock_nc.get_config = mock_get_config
    
    # Mock edit_config
    mock_nc.edit_config.return_value = True
    
    # Mock close
    mock_nc.close_session.return_value = None
    
    return mock_nc


# ============================================================================
# Mock Device State Fixtures
# ============================================================================

@pytest.fixture
def mock_device_bgp_state():
    """Mock BGP neighbor state from devices"""
    return {
        'spine1': {
            'neighbor': {
                '10.1.1.1': {
                    'session_state': 'ESTABLISHED',
                    'peer_as': 65011,
                    'received_routes': 100,
                    'advertised_routes': 50
                },
                '10.1.1.3': {
                    'session_state': 'ESTABLISHED',
                    'peer_as': 65012,
                    'received_routes': 100,
                    'advertised_routes': 50
                }
            }
        },
        'leaf1': {
            'neighbor': {
                '10.1.1.0': {
                    'session_state': 'ESTABLISHED',
                    'peer_as': 65001,
                    'received_routes': 50,
                    'advertised_routes': 100
                }
            }
        }
    }


@pytest.fixture
def mock_device_interface_state():
    """Mock interface state from devices"""
    return {
        'spine1': {
            'ethernet-1/1': {
                'admin_state': 'enable',
                'oper_state': 'up',
                'counters': {
                    'in_octets': 1234567890,
                    'out_octets': 9876543210,
                    'in_errors': 0,
                    'out_errors': 0
                }
            },
            'ethernet-1/2': {
                'admin_state': 'enable',
                'oper_state': 'up',
                'counters': {
                    'in_octets': 5555555555,
                    'out_octets': 6666666666,
                    'in_errors': 0,
                    'out_errors': 0
                }
            }
        },
        'leaf1': {
            'ethernet-1/49': {
                'admin_state': 'enable',
                'oper_state': 'up',
                'counters': {
                    'in_octets': 9876543210,
                    'out_octets': 1234567890,
                    'in_errors': 0,
                    'out_errors': 0
                }
            }
        }
    }


@pytest.fixture
def mock_device_lldp_state():
    """Mock LLDP neighbor state from devices"""
    return {
        'spine1': {
            'ethernet-1/1': {
                'neighbor': 'leaf1',
                'neighbor_port': 'ethernet-1/49',
                'chassis_id': '00:11:22:33:44:55',
                'system_name': 'leaf1'
            },
            'ethernet-1/2': {
                'neighbor': 'leaf2',
                'neighbor_port': 'ethernet-1/49',
                'chassis_id': '00:11:22:33:44:66',
                'system_name': 'leaf2'
            }
        },
        'leaf1': {
            'ethernet-1/49': {
                'neighbor': 'spine1',
                'neighbor_port': 'ethernet-1/1',
                'chassis_id': '00:11:22:33:44:77',
                'system_name': 'spine1'
            }
        }
    }


@pytest.fixture
def mock_device_evpn_state():
    """Mock EVPN route state from devices"""
    return {
        'spine1': {
            'routes': {
                'advertised': [
                    {'vni': 100, 'route_type': 'type-2', 'count': 10},
                    {'vni': 200, 'route_type': 'type-2', 'count': 5}
                ],
                'received': [
                    {'vni': 100, 'route_type': 'type-2', 'count': 20},
                    {'vni': 200, 'route_type': 'type-2', 'count': 10}
                ]
            }
        }
    }


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires lab)"
    )
    config.addinivalue_line(
        "markers", "property: mark test as a property-based test"
    )
