#!/usr/bin/env python3
"""
Universal Query Validation Script

This script validates that universal (vendor-agnostic) Prometheus queries
work correctly across all deployed vendors by:
1. Executing universal query patterns against Prometheus
2. Verifying data is returned from all expected vendors
3. Identifying vendor-specific query failures

Run from ORB VM context:
  orb -m clab python3 validation/check_universal_queries.py

Requirements: 8.4, 8.5
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class UniversalQueryCheck:
    """Result of a universal query check"""

    name: str
    passed: bool
    message: str
    details: dict | None = None


class UniversalQueryValidator:
    """Validates that universal queries return data from all vendors"""

    EXPECTED_VENDORS = ["nokia", "arista", "dellemc", "juniper"]

    UNIVERSAL_QUERIES = [
        {
            "name": "Interface Inbound Traffic Rate",
            "query": "rate(network_interface_in_octets[5m]) * 8",
            "description": "Bits per second inbound on all interfaces",
        },
        {
            "name": "Interface Outbound Traffic Rate",
            "query": "rate(network_interface_out_octets[5m]) * 8",
            "description": "Bits per second outbound on all interfaces",
        },
        {
            "name": "BGP Session State",
            "query": "network_bgp_session_state",
            "description": "BGP session state across all devices",
        },
        {
            "name": "Interface Error Rate",
            "query": "rate(network_interface_in_errors[5m])",
            "description": "Interface error rate across all devices",
        },
        {
            "name": "Interface Packet Rate",
            "query": "rate(network_interface_in_packets[5m])",
            "description": "Packets per second inbound on all interfaces",
        },
    ]

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        expected_vendors: list[str] | None = None,
    ):
        self.prometheus_url = prometheus_url
        self.expected_vendors = expected_vendors or self.EXPECTED_VENDORS
        self.checks: list[UniversalQueryCheck] = []

    def query_prometheus(self, query: str) -> dict | None:
        """Query Prometheus and return results"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10,
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

            self.checks.append(
                UniversalQueryCheck(
                    name="Prometheus Connectivity",
                    passed=passed,
                    message="Prometheus is accessible"
                    if passed
                    else "Cannot connect to Prometheus",
                )
            )
            return passed
        except Exception as e:
            self.checks.append(
                UniversalQueryCheck(
                    name="Prometheus Connectivity",
                    passed=False,
                    message=f"Connection failed: {e}",
                )
            )
            return False

    def check_universal_queries(self) -> bool:
        """Execute each universal query and verify all expected vendors are represented."""
        queries_missing_vendors: dict[str, list[str]] = {}

        per_query_details = []

        for uq in self.UNIVERSAL_QUERIES:
            data = self.query_prometheus(uq["query"])

            vendors_found: set[str] = set()
            result_count = 0
            if data and data.get("result"):
                result_count = len(data["result"])
                for result in data["result"]:
                    vendor = result.get("metric", {}).get("vendor", "")
                    if vendor:
                        vendors_found.add(vendor)

            missing = [v for v in self.expected_vendors if v not in vendors_found]
            if missing:
                queries_missing_vendors[uq["name"]] = missing

            per_query_details.append(
                {
                    "query_name": uq["name"],
                    "query": uq["query"],
                    "result_count": result_count,
                    "vendors_found": sorted(vendors_found),
                    "vendors_missing": missing,
                }
            )

        passed = len(queries_missing_vendors) == 0

        details = {
            "expected_vendors": self.expected_vendors,
            "per_query": per_query_details,
            "queries_missing_vendors": queries_missing_vendors,
        }

        if passed:
            message = (
                f"All {len(self.UNIVERSAL_QUERIES)} universal queries return data "
                f"from all {len(self.expected_vendors)} vendors"
            )
        else:
            summaries = [
                f"{name} missing {', '.join(vendors)}"
                for name, vendors in queries_missing_vendors.items()
            ]
            message = (
                f"{len(queries_missing_vendors)} query(ies) missing vendor data: "
                + "; ".join(summaries)
            )

        self.checks.append(
            UniversalQueryCheck(
                name="Universal Queries",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    def check_vendor_specific_failures(self) -> bool:
        """For each vendor, run each universal query filtered by vendor and identify failures."""
        vendor_failures: dict[str, list[str]] = {}

        per_vendor_details = {}

        for vendor in self.expected_vendors:
            failed_queries = []
            passed_queries = []

            for uq in self.UNIVERSAL_QUERIES:
                # Inject vendor filter into the query
                base_query = uq["query"]
                # Wrap the base metric with a vendor filter
                filtered_query = self._inject_vendor_filter(base_query, vendor)

                data = self.query_prometheus(filtered_query)
                if data and data.get("result"):
                    passed_queries.append(uq["name"])
                else:
                    failed_queries.append(uq["name"])

            per_vendor_details[vendor] = {
                "passed_queries": passed_queries,
                "failed_queries": failed_queries,
            }

            if failed_queries:
                vendor_failures[vendor] = failed_queries

        passed = len(vendor_failures) == 0

        details = {
            "per_vendor": per_vendor_details,
            "vendors_with_failures": vendor_failures,
        }

        if passed:
            message = f"All universal queries succeed for all {len(self.expected_vendors)} vendors"
        else:
            summaries = [
                f"{vendor} ({len(queries)} failed)" for vendor, queries in vendor_failures.items()
            ]
            message = f"Vendor-specific failures: {', '.join(summaries)}"

        self.checks.append(
            UniversalQueryCheck(
                name="Vendor-Specific Query Failures",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    @staticmethod
    def _inject_vendor_filter(query: str, vendor: str) -> str:
        """Inject a vendor label filter into a PromQL query.

        Handles simple metric names and rate/function wrappers by inserting
        {vendor="<vendor>"} after the metric name.
        """
        import re

        # Match metric name possibly inside a function like rate(metric_name[5m])
        # Insert {vendor="vendor"} or add to existing selectors
        pattern = r"(network_\w+)(\{[^}]*\})?"

        def replacer(m: re.Match) -> str:
            metric = m.group(1)
            existing = m.group(2)
            if existing:
                # Add vendor to existing selectors
                return f'{metric}{existing[:-1]},vendor="{vendor}"}}'
            return f'{metric}{{vendor="{vendor}"}}'

        return re.sub(pattern, replacer, query)

    def run_all_checks(self) -> bool:
        """Run all universal query validation checks"""
        print("=" * 70)
        print("Universal Query Validation")
        print("=" * 70)
        print()

        if not self.check_prometheus_connectivity():
            print("❌ Cannot connect to Prometheus. Aborting remaining checks.")
            return False

        self.check_universal_queries()
        self.check_vendor_specific_failures()

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
            print("✅ All universal query checks passed!")
        else:
            print("❌ Some universal query checks failed. See details above.")

        return all_passed

    def get_report(self) -> dict:
        """Get validation report as dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "prometheus_url": self.prometheus_url,
            "expected_vendors": self.expected_vendors,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "message": check.message,
                    "details": check.details,
                }
                for check in self.checks
            ],
            "summary": {
                "total": len(self.checks),
                "passed": sum(1 for c in self.checks if c.passed),
                "failed": sum(1 for c in self.checks if not c.passed),
            },
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate universal queries return data from all vendors via Prometheus"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)",
    )
    parser.add_argument(
        "--expected-vendors",
        default="nokia,arista,dellemc,juniper",
        help="Comma-separated list of expected vendors (default: nokia,arista,dellemc,juniper)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    vendors = [v.strip() for v in args.expected_vendors.split(",") if v.strip()]
    if not vendors:
        print("Error: --expected-vendors must contain at least one vendor name")
        sys.exit(1)

    validator = UniversalQueryValidator(
        prometheus_url=args.prometheus_url,
        expected_vendors=vendors,
    )
    all_passed = validator.run_all_checks()

    if args.json:
        print()
        print(json.dumps(validator.get_report(), indent=2))

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
