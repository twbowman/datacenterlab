#!/usr/bin/env python3
"""
Unit tests for deployment functionality

Tests topology validation, error conditions, and health checks.
Validates: Requirements 15.1
"""

import sys
import os
import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch, mock_open
import yaml

# Add scripts directory to path
scripts_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts')
sys.path.insert(0, scripts_path)

# Import with proper module name
import importlib.util
spec = importlib.util.spec_from_file_location("validate_topology", os.path.join(scripts_path, "validate-topology.py"))
validate_topology = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_topology)

TopologyValidator = validate_topology.TopologyValidator
ValidationError = validate_topology.ValidationError


class TestTopologyValidation:
    """Test topology validation functionality"""
    
    def test_valid_srlinux_topology(self):
        """Test validation of a valid SR Linux topology"""
        topology_content = """
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
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is True
            assert len(validator.errors) == 0
    
    def test_valid_multi_vendor_topology(self):
        """Test validation of multi-vendor topology"""
        topology_content = """
name: multi-vendor-lab
topology:
  nodes:
    srlinux-spine:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
    arista-leaf:
      kind: arista_ceos
      image: ceos:latest
    sonic-leaf:
      kind: sonic-vs
      image: docker-sonic-vs:latest
  links:
    - endpoints: ["srlinux-spine:e1-1", "arista-leaf:eth1"]
    - endpoints: ["srlinux-spine:e1-2", "sonic-leaf:Ethernet0"]
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is True
            assert len(validator.errors) == 0
    
    def test_missing_topology_file(self):
        """Test error when topology file doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            validator = TopologyValidator("/nonexistent/topology.yml")
            assert validator.validate() is False
            assert len(validator.errors) > 0
            assert any("not found" in str(e.message).lower() for e in validator.errors)
    
    def test_invalid_yaml_syntax(self):
        """Test error on invalid YAML syntax"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: [invalid yaml syntax
"""
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert len(validator.errors) > 0
    
    def test_missing_required_field_name(self):
        """Test error when 'name' field is missing"""
        topology_content = """
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("name" in str(e.message).lower() for e in validator.errors)
    
    def test_missing_required_field_topology(self):
        """Test error when 'topology' section is missing"""
        topology_content = """
name: test-lab
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("topology" in str(e.message).lower() for e in validator.errors)
    
    def test_missing_node_kind(self):
        """Test error when node is missing 'kind' field"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      image: ghcr.io/nokia/srlinux:latest
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("kind" in str(e.message).lower() for e in validator.errors)
    
    def test_unsupported_device_kind(self):
        """Test error when device kind is not supported"""
        topology_content = """
name: test-lab
topology:
  nodes:
    router1:
      kind: unsupported_vendor
      image: some-image:latest
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("unsupported" in str(e.message).lower() for e in validator.errors)
    
    def test_missing_image_for_network_device(self):
        """Test error when network device is missing 'image' field"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("image" in str(e.message).lower() for e in validator.errors)
    
    def test_invalid_link_format(self):
        """Test error when link has invalid format"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
  links:
    - endpoints: ["spine1-e1-1", "spine1-e1-2"]
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("endpoint" in str(e.message).lower() for e in validator.errors)
    
    def test_link_to_undefined_node(self):
        """Test error when link references undefined node"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
  links:
    - endpoints: ["spine1:e1-1", "undefined_node:e1-1"]
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("undefined" in str(e.message).lower() for e in validator.errors)
    
    def test_self_loop_detection(self):
        """Test detection of self-referencing links"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
  links:
    - endpoints: ["spine1:e1-1", "spine1:e1-1"]
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("self-loop" in str(e.message).lower() for e in validator.errors)
    
    def test_group_based_configuration(self):
        """Test validation with group-based node configuration"""
        topology_content = """
name: test-lab
topology:
  groups:
    srlinux-router:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
  nodes:
    spine1:
      group: srlinux-router
    spine2:
      group: srlinux-router
  links:
    - endpoints: ["spine1:e1-1", "spine2:e1-1"]
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is True
            assert len(validator.errors) == 0
    
    def test_undefined_group_reference(self):
        """Test error when node references undefined group"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      group: undefined-group
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            assert validator.validate() is False
            assert any("undefined group" in str(e.message).lower() for e in validator.errors)
    
    def test_validation_error_has_remediation(self):
        """Test that validation errors include remediation suggestions"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      image: ghcr.io/nokia/srlinux:latest
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            validator.validate()
            
            # Check that errors have remediation
            assert len(validator.errors) > 0
            for error in validator.errors:
                assert hasattr(error, 'remediation')
                assert hasattr(error, 'component')
                assert hasattr(error, 'message')


class TestHealthChecks:
    """Test health check functionality"""
    
    def test_health_check_identifies_component(self):
        """Test that health checks identify specific failing components"""
        # This would test actual health check logic when implemented
        # For now, test the error structure
        error = ValidationError(
            component="spine1",
            message="Device not reachable",
            remediation="Check device is running: docker ps | grep spine1"
        )
        
        assert error.component == "spine1"
        assert "reachable" in error.message.lower()
        assert "docker ps" in error.remediation


class TestDeploymentErrorMessages:
    """Test deployment error message specificity"""
    
    def test_error_identifies_missing_image(self):
        """Test that error specifically identifies missing image"""
        topology_content = """
name: test-lab
topology:
  nodes:
    spine1:
      kind: nokia_srlinux
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            validator.validate()
            
            # Find the image-related error
            image_errors = [e for e in validator.errors if "image" in str(e.message).lower()]
            assert len(image_errors) > 0
            
            # Check error specificity
            error = image_errors[0]
            assert "spine1" in error.component
            assert error.remediation != ""
    
    def test_error_identifies_invalid_topology_structure(self):
        """Test that error identifies structural issues"""
        topology_content = """
name: test-lab
invalid_section:
  nodes:
    spine1:
      kind: nokia_srlinux
"""
        topology_data = yaml.safe_load(topology_content)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=topology_content)), \
             patch('yaml.safe_load', return_value=topology_data):
            
            validator = TopologyValidator("/mock/topology.yml")
            validator.validate()
            
            # Should have error about missing topology section
            assert any("topology" in str(e.message).lower() for e in validator.errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
