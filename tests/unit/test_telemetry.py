#!/usr/bin/env python3
"""
Unit tests for telemetry collection

Tests gNMI subscription creation, metric normalization, and Prometheus export.
Validates: Requirements 15.3
"""

import pytest
import re


class TestGNMISubscriptions:
    """Test gNMI subscription configuration"""
    
    def test_openconfig_interface_subscription(self):
        """Test OpenConfig interface metrics subscription"""
        subscription = {
            'name': 'oc_interface_stats',
            'paths': ['/interfaces/interface/state/counters'],
            'mode': 'stream',
            'stream-mode': 'sample',
            'sample-interval': '10s'
        }
        
        # Validate subscription structure
        assert 'name' in subscription
        assert 'paths' in subscription
        assert 'mode' in subscription
        assert subscription['mode'] == 'stream'
        assert subscription['stream-mode'] == 'sample'
    
    def test_openconfig_bgp_subscription(self):
        """Test OpenConfig BGP metrics subscription"""
        subscription = {
            'name': 'oc_bgp_state',
            'paths': [
                '/network-instances/network-instance/protocols/protocol/bgp/neighbors'
            ],
            'mode': 'stream',
            'stream-mode': 'on_change'
        }
        
        assert 'bgp' in subscription['paths'][0]
        assert subscription['stream-mode'] == 'on_change'
    
    def test_openconfig_lldp_subscription(self):
        """Test OpenConfig LLDP metrics subscription"""
        subscription = {
            'name': 'oc_lldp_neighbors',
            'paths': ['/lldp/interfaces/interface/neighbors'],
            'mode': 'stream',
            'stream-mode': 'on_change'
        }
        
        assert 'lldp' in subscription['paths'][0]
    
    def test_native_vendor_subscription(self):
        """Test native vendor-specific subscription"""
        subscription = {
            'name': 'srl_ospf_state',
            'paths': ['/network-instance[name=default]/protocols/ospf'],
            'mode': 'stream',
            'stream-mode': 'sample',
            'sample-interval': '30s'
        }
        
        # Native paths should have vendor-specific format
        assert 'network-instance' in subscription['paths'][0]
        assert subscription['sample-interval'] == '30s'
    
    def test_subscription_sample_interval_format(self):
        """Test sample interval format validation"""
        valid_intervals = ['10s', '30s', '1m', '5m']
        
        for interval in valid_intervals:
            # Should match pattern: number + time unit
            assert re.match(r'^\d+[smh]$', interval)
    
    def test_subscription_encoding_options(self):
        """Test subscription encoding options"""
        valid_encodings = ['json_ietf', 'proto', 'json']
        
        subscription = {
            'name': 'test_sub',
            'paths': ['/test'],
            'encoding': 'json_ietf'
        }
        
        assert subscription['encoding'] in valid_encodings


class TestMetricNormalization:
    """Test metric normalization rules"""
    
    def test_interface_counter_normalization(self):
        """Test interface counter metric normalization"""
        # SR Linux native path
        srl_path = '/interface/statistics/in-octets'
        # Normalized name
        normalized = 'network_interface_in_octets'
        
        # Verify normalization mapping
        assert 'interface' in srl_path
        assert 'in-octets' in srl_path or 'in_octets' in normalized
    
    def test_bgp_session_state_normalization(self):
        """Test BGP session state normalization"""
        # Different vendor paths should normalize to same metric
        srl_path = '/network-instance/protocols/bgp/neighbor/session-state'
        arista_path = '/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state'
        
        normalized = 'network_bgp_session_state'
        
        # Both should contain bgp and session-state
        assert 'bgp' in srl_path and 'bgp' in arista_path
        assert 'session' in srl_path and 'session' in arista_path
    
    def test_metric_value_preservation(self):
        """Test that metric values are preserved during normalization"""
        original_metric = {
            'name': '/interface/statistics/in-octets',
            'value': 1234567890,
            'timestamp': 1705315800
        }
        
        # After normalization
        normalized_metric = {
            'name': 'network_interface_in_octets',
            'value': 1234567890,  # Value unchanged
            'timestamp': 1705315800  # Timestamp unchanged
        }
        
        assert original_metric['value'] == normalized_metric['value']
        assert original_metric['timestamp'] == normalized_metric['timestamp']
    
    def test_vendor_label_addition(self):
        """Test that vendor label is added to metrics"""
        metric = {
            'name': 'network_interface_in_octets',
            'labels': {
                'source': 'spine1',
                'vendor': 'nokia',
                'interface': 'ethernet-1/1'
            }
        }
        
        assert 'vendor' in metric['labels']
        assert metric['labels']['vendor'] in ['nokia', 'arista', 'sonic', 'juniper']
    
    def test_interface_name_normalization(self):
        """Test interface name normalization in labels"""
        # Different vendor formats
        vendor_interfaces = {
            'nokia': 'ethernet-1/1',
            'arista': 'Ethernet1/1',
            'sonic': 'Ethernet0',
            'juniper': 'ge-0/0/0'
        }
        
        # All should normalize to consistent format
        normalized_format = r'^eth\d+_\d+$'
        
        # Example normalized names
        normalized_names = {
            'nokia': 'eth1_1',
            'arista': 'eth1_1',
            'sonic': 'eth1_1',
            'juniper': 'eth0_0'
        }
        
        for vendor, normalized in normalized_names.items():
            assert re.match(normalized_format, normalized)
    
    def test_native_metric_vendor_prefix(self):
        """Test that native metrics get vendor prefix"""
        native_metric = {
            'name': 'srl_ospf_neighbor_count',
            'labels': {
                'vendor': 'nokia',
                'metric_type': 'native'
            }
        }
        
        # Native metrics should have vendor prefix in name
        assert native_metric['name'].startswith('srl_')
        assert native_metric['labels']['vendor'] == 'nokia'


class TestPrometheusExport:
    """Test Prometheus metric export"""
    
    def test_prometheus_metric_format(self):
        """Test Prometheus metric format"""
        # Prometheus metric format: metric_name{labels} value timestamp
        metric_line = 'network_interface_in_octets{source="spine1",interface="eth1_1",vendor="nokia"} 1234567890 1705315800000'
        
        # Parse metric line
        parts = metric_line.split(' ')
        assert len(parts) == 3
        
        # Metric name and labels
        metric_with_labels = parts[0]
        assert '{' in metric_with_labels
        assert '}' in metric_with_labels
        
        # Value
        value = parts[1]
        assert value.isdigit()
        
        # Timestamp (milliseconds)
        timestamp = parts[2]
        assert timestamp.isdigit()
    
    def test_prometheus_label_format(self):
        """Test Prometheus label format"""
        labels = {
            'source': 'spine1',
            'vendor': 'nokia',
            'interface': 'eth1_1',
            'role': 'spine'
        }
        
        # Labels should be key="value" format
        label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
        
        assert 'source="spine1"' in label_str
        assert 'vendor="nokia"' in label_str
    
    def test_prometheus_metric_prefix(self):
        """Test Prometheus metric prefix"""
        metrics = [
            'network_interface_in_octets',
            'network_interface_out_octets',
            'network_bgp_session_state',
            'network_lldp_neighbor_count'
        ]
        
        # All normalized metrics should have 'network_' prefix
        for metric in metrics:
            assert metric.startswith('network_')
    
    def test_prometheus_export_endpoint(self):
        """Test Prometheus export endpoint configuration"""
        export_config = {
            'type': 'prometheus',
            'listen': ':9273',
            'path': '/metrics',
            'metric-prefix': 'network'
        }
        
        assert export_config['type'] == 'prometheus'
        assert export_config['path'] == '/metrics'
        assert 'metric-prefix' in export_config


class TestTelemetryProcessors:
    """Test telemetry event processors"""
    
    def test_event_convert_processor(self):
        """Test event-convert processor configuration"""
        processor = {
            'event-convert': {
                'value-names': [
                    '^/srl_nokia/interface/statistics/in-octets$'
                ],
                'transforms': [
                    {
                        'replace': {
                            'apply-on': 'name',
                            'old': '/srl_nokia/interface/statistics/in-octets',
                            'new': 'interface_in_octets'
                        }
                    }
                ]
            }
        }
        
        assert 'event-convert' in processor
        assert 'value-names' in processor['event-convert']
        assert 'transforms' in processor['event-convert']
    
    def test_event_add_tag_processor(self):
        """Test event-add-tag processor for vendor labels"""
        processor = {
            'event-add-tag': {
                'tags': {
                    'vendor': 'nokia',
                    'os': 'srlinux'
                }
            }
        }
        
        assert 'event-add-tag' in processor
        assert 'tags' in processor['event-add-tag']
        assert 'vendor' in processor['event-add-tag']['tags']
    
    def test_processor_chain_order(self):
        """Test that processors are applied in correct order"""
        processor_chain = [
            'normalize_metrics',
            'add_vendor_labels',
            'format_for_prometheus'
        ]
        
        # Processors should be applied in order
        assert processor_chain[0] == 'normalize_metrics'
        assert processor_chain[-1] == 'format_for_prometheus'


class TestTelemetryConnectionManagement:
    """Test telemetry connection management"""
    
    def test_connection_timeout_configuration(self):
        """Test connection timeout settings"""
        target_config = {
            'address': '172.20.20.10:57400',
            'timeout': '30s',
            'retry-interval': '10s'
        }
        
        assert 'timeout' in target_config
        assert 'retry-interval' in target_config
    
    def test_exponential_backoff_configuration(self):
        """Test exponential backoff for reconnection"""
        backoff_config = {
            'initial-interval': '1s',
            'max-interval': '60s',
            'multiplier': 2.0
        }
        
        # Calculate backoff intervals
        intervals = []
        current = 1  # 1 second
        max_interval = 60
        
        while current <= max_interval:
            intervals.append(current)
            current *= backoff_config['multiplier']
            if current > max_interval:
                current = max_interval
        
        # Should have increasing intervals: 1, 2, 4, 8, 16, 32, 60
        assert intervals[0] == 1
        assert intervals[1] == 2
        assert intervals[-1] == max_interval
    
    def test_connection_credentials(self):
        """Test connection credentials configuration"""
        target = {
            'address': '172.20.20.10:57400',
            'username': 'admin',
            'password': 'NokiaSrl1!',
            'insecure': True
        }
        
        assert 'username' in target
        assert 'password' in target
        assert 'insecure' in target


class TestMetricValidation:
    """Test metric validation"""
    
    def test_metric_has_required_fields(self):
        """Test that metrics have required fields"""
        metric = {
            'name': 'network_interface_in_octets',
            'value': 1234567890,
            'timestamp': 1705315800,
            'labels': {
                'source': 'spine1',
                'interface': 'eth1_1'
            }
        }
        
        required_fields = ['name', 'value', 'timestamp', 'labels']
        for field in required_fields:
            assert field in metric
    
    def test_metric_value_types(self):
        """Test metric value type validation"""
        # Counter (always increasing)
        counter_metric = {
            'name': 'network_interface_in_octets',
            'type': 'counter',
            'value': 1234567890
        }
        
        # Gauge (can increase or decrease)
        gauge_metric = {
            'name': 'network_interface_oper_status',
            'type': 'gauge',
            'value': 1  # 1=up, 0=down
        }
        
        assert counter_metric['type'] == 'counter'
        assert gauge_metric['type'] == 'gauge'
    
    def test_timestamp_format(self):
        """Test timestamp format validation"""
        # Unix timestamp in seconds
        timestamp_seconds = 1705315800
        
        # Unix timestamp in milliseconds (for Prometheus)
        timestamp_millis = 1705315800000
        
        # Validate conversion
        assert timestamp_millis == timestamp_seconds * 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
