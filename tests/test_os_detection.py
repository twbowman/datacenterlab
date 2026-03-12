#!/usr/bin/env python3
"""
Unit tests for OS detection system

Validates: Requirements 1.4, 1.5
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ansible', 'plugins', 'inventory'))

from dynamic_inventory import DeviceOSDetector


def test_detect_os_from_capabilities():
    """Test OS detection from gNMI capabilities output"""
    detector = DeviceOSDetector()
    
    # Test Nokia/SR Linux detection
    nokia_caps = "supported_models: Nokia SR Linux"
    assert detector.detect_os_from_capabilities(nokia_caps) == 'srlinux'
    
    # Test Arista detection
    arista_caps = "supported_models: Arista Networks EOS"
    assert detector.detect_os_from_capabilities(arista_caps) == 'eos'
    
    # Test SONiC detection
    sonic_caps = "supported_models: SONiC"
    assert detector.detect_os_from_capabilities(sonic_caps) == 'sonic'
    
    # Test Juniper detection
    juniper_caps = "supported_models: Juniper Networks"
    assert detector.detect_os_from_capabilities(juniper_caps) == 'junos'
    
    # Test unknown vendor
    unknown_caps = "supported_models: Unknown Vendor"
    assert detector.detect_os_from_capabilities(unknown_caps) == 'unknown'
    
    print("✓ test_detect_os_from_capabilities passed")


def test_detect_os_from_labels():
    """Test OS detection from containerlab labels"""
    detector = DeviceOSDetector()
    
    # Test with labels
    node_config = {'labels': {'os': 'srlinux'}}
    assert detector.detect_os_from_labels(node_config) == 'srlinux'
    
    # Test without labels
    node_config = {}
    assert detector.detect_os_from_labels(node_config) is None
    
    print("✓ test_detect_os_from_labels passed")


def test_detect_os_from_kind():
    """Test OS detection from containerlab kind"""
    detector = DeviceOSDetector()
    
    # Test with direct kind
    node_config = {'kind': 'nokia_srlinux'}
    assert detector.detect_os_from_kind(node_config, None) == 'srlinux'
    
    node_config = {'kind': 'arista_ceos'}
    assert detector.detect_os_from_kind(node_config, None) == 'eos'
    
    # Test with group
    groups = {'srlinux-router': {'kind': 'nokia_srlinux'}}
    node_config = {'group': 'srlinux-router'}
    assert detector.detect_os_from_kind(node_config, groups) == 'srlinux'
    
    print("✓ test_detect_os_from_kind passed")


if __name__ == '__main__':
    test_detect_os_from_capabilities()
    test_detect_os_from_labels()
    test_detect_os_from_kind()
    print("\nAll tests passed!")
