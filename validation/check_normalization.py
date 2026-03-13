#!/usr/bin/env python3
"""
Metric Normalization Verification Script

This script validates that metric normalization is working correctly by:
1. Querying Prometheus for normalized metrics
2. Verifying all vendors produce expected metric names
3. Checking that metric values are preserved
4. Providing clear pass/fail output with details

Requirements: 8.3
"""

import sys
import json
import requests
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizationCheck:
    """Result of a normalization check"""
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None


class MetricNormalizationValidator:
    """Validates metric normalization across vendors"""
    
    # Expected normalized metric names
    EXPECTED_METRICS = [
        "network_interface_in_octets",
        "network_interface_out_octets",
        "network_interface_in_packets",
        "network_interface_out_packets",
        "network_interface_in_errors",
        "network_interface_out_errors",
    ]
    
    # Expected vendors
    EXPECTED_VENDORS = ["nokia", "arista", "dellemc", "juniper"]
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.checks: List[NormalizationCheck] = []
    
    def query_prometheus(self, query: str) -> Optional[Dict]:
        """Query Prometheus and return results"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "success":
                return None
            
            return data["data"]
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return None
    
    def check_prometheus_connectivity(self) -> bool:
        """Verify Prometheus is accessible"""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            passed = response.status_code == 200
            
            self.checks.append(NormalizationCheck(
                name="Prometheus Connectivity",
                passed=passed,
                message="Prometheus is accessible" if passed else "Cannot connect to Prometheus"
            ))
            return passed
        except Exception as e:
            self.checks.append(NormalizationCheck(
                name="Prometheus Connectivity",
                passed=False,
                message=f"Connection failed: {e}"
            ))
            return False
    
    def check_normalized_metrics_exist(self) -> bool:
        """Verify normalized metrics exist in Prometheus"""
        missing_metrics = []
        found_metrics = []
        
        for metric in self.EXPECTED_METRICS:
            data = self.query_prometheus(metric)
            if data and data["result"]:
                found_metrics.append(metric)
            else:
                missing_metrics.append(metric)
        
        passed = len(missing_metrics) == 0
        
        details = {
            "found": found_metrics,
            "missing": missing_metrics,
            "total_expected": len(self.EXPECTED_METRICS),
            "total_found": len(found_metrics)
        }
        
        message = (
            f"All {len(self.EXPECTED_METRICS)} normalized metrics found"
            if passed
            else f"Missing {len(missing_metrics)} metrics: {', '.join(missing_metrics)}"
        )
        
        self.checks.append(NormalizationCheck(
            name="Normalized Metrics Exist",
            passed=passed,
            message=message,
            details=details
        ))
        return passed
    
    def check_vendor_coverage(self) -> bool:
        """Verify all vendors produce normalized metrics"""
        vendor_metrics = {}
        
        for metric in self.EXPECTED_METRICS:
            data = self.query_prometheus(f'{metric}{{vendor!=""}}')
            if not data or not data["result"]:
                continue
            
            for result in data["result"]:
                vendor = result["metric"].get("vendor", "unknown")
                if vendor not in vendor_metrics:
                    vendor_metrics[vendor] = set()
                vendor_metrics[vendor].add(metric)
        
        # Check which expected vendors are present
        found_vendors = set(vendor_metrics.keys())
        missing_vendors = set(self.EXPECTED_VENDORS) - found_vendors
        
        # Check if each vendor has all expected metrics
        incomplete_vendors = {}
        for vendor in found_vendors:
            vendor_metric_set = vendor_metrics[vendor]
            missing_for_vendor = set(self.EXPECTED_METRICS) - vendor_metric_set
            if missing_for_vendor:
                incomplete_vendors[vendor] = list(missing_for_vendor)
        
        passed = len(missing_vendors) == 0 and len(incomplete_vendors) == 0
        
        details = {
            "found_vendors": list(found_vendors),
            "missing_vendors": list(missing_vendors),
            "incomplete_vendors": incomplete_vendors,
            "vendor_metrics": {v: list(m) for v, m in vendor_metrics.items()}
        }
        
        if passed:
            message = f"All {len(found_vendors)} vendors producing all normalized metrics"
        elif missing_vendors:
            message = f"Missing vendors: {', '.join(missing_vendors)}"
        else:
            message = f"Incomplete metrics for vendors: {', '.join(incomplete_vendors.keys())}"
        
        self.checks.append(NormalizationCheck(
            name="Vendor Coverage",
            passed=passed,
            message=message,
            details=details
        ))
        return passed
    
    def check_metric_values_preserved(self) -> bool:
        """Verify metric values are reasonable (not zero, have timestamps)"""
        issues = []
        checked_metrics = 0
        
        for metric in self.EXPECTED_METRICS:
            data = self.query_prometheus(metric)
            if not data or not data["result"]:
                continue
            
            for result in data["result"]:
                checked_metrics += 1
                metric_name = result["metric"].get("__name__", "unknown")
                vendor = result["metric"].get("vendor", "unknown")
                source = result["metric"].get("source", "unknown")
                
                # Check if value exists
                if "value" not in result:
                    issues.append(f"{metric_name} from {vendor}/{source}: no value")
                    continue
                
                timestamp, value = result["value"]
                
                # Check timestamp is recent (within last 5 minutes)
                current_time = datetime.now().timestamp()
                if current_time - timestamp > 300:
                    issues.append(
                        f"{metric_name} from {vendor}/{source}: stale data "
                        f"(age: {int(current_time - timestamp)}s)"
                    )
                
                # Check value is numeric
                try:
                    float(value)
                except (ValueError, TypeError):
                    issues.append(f"{metric_name} from {vendor}/{source}: non-numeric value '{value}'")
        
        passed = len(issues) == 0 and checked_metrics > 0
        
        details = {
            "checked_metrics": checked_metrics,
            "issues": issues
        }
        
        message = (
            f"All {checked_metrics} metric values are valid and current"
            if passed
            else f"Found {len(issues)} issues with metric values"
        )
        
        self.checks.append(NormalizationCheck(
            name="Metric Values Preserved",
            passed=passed,
            message=message,
            details=details
        ))
        return passed
    
    def check_interface_name_normalization(self) -> bool:
        """Verify interface names are normalized correctly"""
        # Query for interface metrics with interface labels
        data = self.query_prometheus('network_interface_in_octets{interface!=""}')
        
        if not data or not data["result"]:
            self.checks.append(NormalizationCheck(
                name="Interface Name Normalization",
                passed=False,
                message="No interface metrics found with interface labels"
            ))
            return False
        
        normalized_count = 0
        unnormalized_count = 0
        unnormalized_examples = []
        
        for result in data["result"]:
            interface = result["metric"].get("interface", "")
            
            # Check if interface name follows normalized pattern (ethX_Y or ethX_Y_Z)
            if interface.startswith("eth") and "_" in interface:
                normalized_count += 1
            else:
                unnormalized_count += 1
                if len(unnormalized_examples) < 5:
                    vendor = result["metric"].get("vendor", "unknown")
                    unnormalized_examples.append(f"{interface} ({vendor})")
        
        passed = unnormalized_count == 0 and normalized_count > 0
        
        details = {
            "normalized_count": normalized_count,
            "unnormalized_count": unnormalized_count,
            "unnormalized_examples": unnormalized_examples
        }
        
        message = (
            f"All {normalized_count} interface names are normalized"
            if passed
            else f"{unnormalized_count} unnormalized interfaces found: {', '.join(unnormalized_examples)}"
        )
        
        self.checks.append(NormalizationCheck(
            name="Interface Name Normalization",
            passed=passed,
            message=message,
            details=details
        ))
        return passed
    
    def check_cross_vendor_consistency(self) -> bool:
        """Verify same metric names are used across all vendors"""
        metric_vendors = {}
        
        for metric in self.EXPECTED_METRICS:
            data = self.query_prometheus(f'{metric}{{vendor!=""}}')
            if not data or not data["result"]:
                continue
            
            vendors = set()
            for result in data["result"]:
                vendor = result["metric"].get("vendor", "unknown")
                vendors.add(vendor)
            
            metric_vendors[metric] = vendors
        
        # Check if all metrics have the same set of vendors
        if not metric_vendors:
            self.checks.append(NormalizationCheck(
                name="Cross-Vendor Consistency",
                passed=False,
                message="No metrics found with vendor labels"
            ))
            return False
        
        all_vendors = set()
        for vendors in metric_vendors.values():
            all_vendors.update(vendors)
        
        inconsistent_metrics = {}
        for metric, vendors in metric_vendors.items():
            missing = all_vendors - vendors
            if missing:
                inconsistent_metrics[metric] = list(missing)
        
        passed = len(inconsistent_metrics) == 0
        
        details = {
            "all_vendors": list(all_vendors),
            "inconsistent_metrics": inconsistent_metrics
        }
        
        message = (
            f"All metrics consistent across {len(all_vendors)} vendors"
            if passed
            else f"{len(inconsistent_metrics)} metrics have inconsistent vendor coverage"
        )
        
        self.checks.append(NormalizationCheck(
            name="Cross-Vendor Consistency",
            passed=passed,
            message=message,
            details=details
        ))
        return passed
    
    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("=" * 70)
        print("Metric Normalization Verification")
        print("=" * 70)
        print()
        
        # Run checks in order
        if not self.check_prometheus_connectivity():
            print("❌ Cannot connect to Prometheus. Aborting remaining checks.")
            return False
        
        self.check_normalized_metrics_exist()
        self.check_vendor_coverage()
        self.check_metric_values_preserved()
        self.check_interface_name_normalization()
        self.check_cross_vendor_consistency()
        
        # Print results
        print()
        print("Check Results:")
        print("-" * 70)
        
        passed_count = 0
        failed_count = 0
        
        for check in self.checks:
            status = "✅ PASS" if check.passed else "❌ FAIL"
            print(f"{status} | {check.name}")
            print(f"       {check.message}")
            
            if check.passed:
                passed_count += 1
            else:
                failed_count += 1
                if check.details:
                    print(f"       Details: {json.dumps(check.details, indent=2)}")
            print()
        
        # Print summary
        print("=" * 70)
        print(f"Summary: {passed_count} passed, {failed_count} failed")
        print("=" * 70)
        
        all_passed = failed_count == 0
        if all_passed:
            print("✅ All normalization checks passed!")
        else:
            print("❌ Some normalization checks failed. See details above.")
        
        return all_passed
    
    def get_report(self) -> Dict:
        """Get validation report as dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "prometheus_url": self.prometheus_url,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.checks
            ],
            "summary": {
                "total": len(self.checks),
                "passed": sum(1 for c in self.checks if c.passed),
                "failed": sum(1 for c in self.checks if not c.passed)
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate metric normalization in Prometheus"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    validator = MetricNormalizationValidator(prometheus_url=args.prometheus_url)
    all_passed = validator.run_all_checks()
    
    if args.json:
        print()
        print(json.dumps(validator.get_report(), indent=2))
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
