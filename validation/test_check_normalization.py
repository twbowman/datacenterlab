#!/usr/bin/env python3
"""
Unit tests for metric normalization verification script

This demonstrates the validation logic works correctly with mock data.
"""

import unittest
from unittest.mock import Mock, patch
from check_normalization import MetricNormalizationValidator, NormalizationCheck


class TestMetricNormalizationValidator(unittest.TestCase):
    """Test cases for MetricNormalizationValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = MetricNormalizationValidator(prometheus_url="http://test:9090")
    
    def test_initialization(self):
        """Test validator initializes correctly"""
        self.assertEqual(self.validator.prometheus_url, "http://test:9090")
        self.assertEqual(len(self.validator.checks), 0)
        self.assertEqual(len(self.validator.EXPECTED_METRICS), 6)
        self.assertEqual(len(self.validator.EXPECTED_VENDORS), 4)
    
    @patch('check_normalization.requests.get')
    def test_prometheus_connectivity_success(self, mock_get):
        """Test successful Prometheus connectivity check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.validator.check_prometheus_connectivity()
        
        self.assertTrue(result)
        self.assertEqual(len(self.validator.checks), 1)
        self.assertTrue(self.validator.checks[0].passed)
        self.assertEqual(self.validator.checks[0].name, "Prometheus Connectivity")
    
    @patch('check_normalization.requests.get')
    def test_prometheus_connectivity_failure(self, mock_get):
        """Test failed Prometheus connectivity check"""
        mock_get.side_effect = Exception("Connection refused")
        
        result = self.validator.check_prometheus_connectivity()
        
        self.assertFalse(result)
        self.assertEqual(len(self.validator.checks), 1)
        self.assertFalse(self.validator.checks[0].passed)
    
    def test_query_prometheus_success(self):
        """Test successful Prometheus query"""
        with patch('check_normalization.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "data": {
                    "result": [
                        {
                            "metric": {"__name__": "network_interface_in_octets"},
                            "value": [1234567890, "1000"]
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            result = self.validator.query_prometheus("network_interface_in_octets")
            
            self.assertIsNotNone(result)
            self.assertIn("result", result)
            self.assertEqual(len(result["result"]), 1)
    
    def test_query_prometheus_failure(self):
        """Test failed Prometheus query"""
        with patch('check_normalization.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = self.validator.query_prometheus("test_metric")
            
            self.assertIsNone(result)
    
    def test_check_normalized_metrics_exist_all_found(self):
        """Test when all normalized metrics exist"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            # Mock all metrics as found
            mock_query.return_value = {"result": [{"metric": {}, "value": [0, "100"]}]}
            
            result = self.validator.check_normalized_metrics_exist()
            
            self.assertTrue(result)
            check = self.validator.checks[-1]
            self.assertEqual(check.name, "Normalized Metrics Exist")
            self.assertTrue(check.passed)
            self.assertEqual(check.details["total_found"], 6)
            self.assertEqual(len(check.details["missing"]), 0)
    
    def test_check_normalized_metrics_exist_some_missing(self):
        """Test when some normalized metrics are missing"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            # Mock only first 3 metrics as found
            call_count = [0]
            def side_effect(query):
                call_count[0] += 1
                if call_count[0] <= 3:
                    return {"result": [{"metric": {}, "value": [0, "100"]}]}
                return {"result": []}
            
            mock_query.side_effect = side_effect
            
            result = self.validator.check_normalized_metrics_exist()
            
            self.assertFalse(result)
            check = self.validator.checks[-1]
            self.assertFalse(check.passed)
            self.assertEqual(check.details["total_found"], 3)
            self.assertEqual(len(check.details["missing"]), 3)
    
    def test_check_vendor_coverage_all_vendors(self):
        """Test when all vendors produce all metrics"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            # Mock metrics from all 4 vendors
            mock_query.return_value = {
                "result": [
                    {"metric": {"vendor": "nokia"}, "value": [0, "100"]},
                    {"metric": {"vendor": "arista"}, "value": [0, "200"]},
                    {"metric": {"vendor": "dellemc"}, "value": [0, "300"]},
                    {"metric": {"vendor": "juniper"}, "value": [0, "400"]},
                ]
            }
            
            result = self.validator.check_vendor_coverage()
            
            self.assertTrue(result)
            check = self.validator.checks[-1]
            self.assertTrue(check.passed)
            self.assertEqual(len(check.details["found_vendors"]), 4)
            self.assertEqual(len(check.details["missing_vendors"]), 0)
    
    def test_check_vendor_coverage_missing_vendor(self):
        """Test when a vendor is missing"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            # Mock metrics from only 3 vendors
            mock_query.return_value = {
                "result": [
                    {"metric": {"vendor": "nokia"}, "value": [0, "100"]},
                    {"metric": {"vendor": "arista"}, "value": [0, "200"]},
                    {"metric": {"vendor": "dellemc"}, "value": [0, "300"]},
                ]
            }
            
            result = self.validator.check_vendor_coverage()
            
            self.assertFalse(result)
            check = self.validator.checks[-1]
            self.assertFalse(check.passed)
            self.assertIn("juniper", check.details["missing_vendors"])
    
    def test_check_interface_name_normalization_success(self):
        """Test when all interface names are normalized"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            mock_query.return_value = {
                "result": [
                    {"metric": {"interface": "eth1_1", "vendor": "nokia"}, "value": [0, "100"]},
                    {"metric": {"interface": "eth1_0", "vendor": "arista"}, "value": [0, "200"]},
                    {"metric": {"interface": "eth0_0", "vendor": "dellemc"}, "value": [0, "300"]},
                    {"metric": {"interface": "eth0_0_0", "vendor": "juniper"}, "value": [0, "400"]},
                ]
            }
            
            result = self.validator.check_interface_name_normalization()
            
            self.assertTrue(result)
            check = self.validator.checks[-1]
            self.assertTrue(check.passed)
            self.assertEqual(check.details["normalized_count"], 4)
            self.assertEqual(check.details["unnormalized_count"], 0)
    
    def test_check_interface_name_normalization_failure(self):
        """Test when interface names are not normalized"""
        with patch.object(self.validator, 'query_prometheus') as mock_query:
            mock_query.return_value = {
                "result": [
                    {"metric": {"interface": "ethernet-1/1", "vendor": "nokia"}, "value": [0, "100"]},
                    {"metric": {"interface": "Ethernet1", "vendor": "arista"}, "value": [0, "200"]},
                ]
            }
            
            result = self.validator.check_interface_name_normalization()
            
            self.assertFalse(result)
            check = self.validator.checks[-1]
            self.assertFalse(check.passed)
            self.assertEqual(check.details["unnormalized_count"], 2)
            self.assertGreater(len(check.details["unnormalized_examples"]), 0)
    
    def test_get_report(self):
        """Test report generation"""
        # Add some mock checks
        self.validator.checks = [
            NormalizationCheck("Test 1", True, "Passed"),
            NormalizationCheck("Test 2", False, "Failed"),
        ]
        
        report = self.validator.get_report()
        
        self.assertIn("timestamp", report)
        self.assertIn("prometheus_url", report)
        self.assertIn("checks", report)
        self.assertIn("summary", report)
        self.assertEqual(len(report["checks"]), 2)
        self.assertEqual(report["summary"]["total"], 2)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)


class TestNormalizationCheck(unittest.TestCase):
    """Test cases for NormalizationCheck dataclass"""
    
    def test_normalization_check_creation(self):
        """Test creating a NormalizationCheck"""
        check = NormalizationCheck(
            name="Test Check",
            passed=True,
            message="Test message",
            details={"key": "value"}
        )
        
        self.assertEqual(check.name, "Test Check")
        self.assertTrue(check.passed)
        self.assertEqual(check.message, "Test message")
        self.assertEqual(check.details["key"], "value")
    
    def test_normalization_check_without_details(self):
        """Test creating a NormalizationCheck without details"""
        check = NormalizationCheck(
            name="Test Check",
            passed=False,
            message="Test message"
        )
        
        self.assertIsNone(check.details)


if __name__ == "__main__":
    unittest.main()
