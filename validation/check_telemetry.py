#!/usr/bin/env python3
"""
Telemetry Streaming Verification Script

This script validates that telemetry streaming is working correctly by:
1. Querying Prometheus for recent metrics from each expected device
2. Identifying devices not streaming telemetry
3. Checking telemetry collection latency is below threshold
4. Verifying metric freshness (received within last 60 seconds)
5. Verifying each device produces all expected metric families

Requirements: 8.1, 8.2, 8.5, 8.6

Run from ORB VM context:
  orb -m clab python3 validation/check_telemetry.py --expected-devices spine1,spine2,leaf1,leaf2
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class TelemetryCheck:
    """Result of a telemetry check"""

    name: str
    passed: bool
    message: str
    details: dict | None = None


class TelemetryStreamingValidator:
    """Validates telemetry streaming from network devices"""

    # Representative metric used to detect device streaming
    STREAMING_METRIC = "network_interface_in_octets"

    def __init__(
        self, prometheus_url: str, expected_devices: list[str], latency_threshold: float = 10.0
    ):
        self.prometheus_url = prometheus_url
        self.expected_devices = expected_devices
        self.latency_threshold = latency_threshold
        self.checks: list[TelemetryCheck] = []

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
                TelemetryCheck(
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
                TelemetryCheck(
                    name="Prometheus Connectivity",
                    passed=False,
                    message=f"Connection failed: {e}",
                )
            )
            return False

    def check_devices_streaming(self) -> bool:
        """Check which expected devices are streaming telemetry in the last 60 seconds"""
        # Query for any device that has reported the streaming metric recently
        data = self.query_prometheus(f"count by (source) ({self.STREAMING_METRIC}[60s])")

        streaming_devices: set[str] = set()
        if data and data.get("result"):
            for result in data["result"]:
                source = result["metric"].get("source", "")
                if source:
                    streaming_devices.add(source)

        missing_devices = [d for d in self.expected_devices if d not in streaming_devices]
        active_devices = [d for d in self.expected_devices if d in streaming_devices]

        passed = len(missing_devices) == 0

        details = {
            "expected_devices": self.expected_devices,
            "streaming_devices": sorted(streaming_devices),
            "active_expected": active_devices,
            "missing_devices": missing_devices,
        }

        if passed:
            message = f"All {len(self.expected_devices)} expected devices are streaming telemetry"
        else:
            message = (
                f"{len(missing_devices)} device(s) not streaming: {', '.join(missing_devices)}"
            )

        self.checks.append(
            TelemetryCheck(
                name="Devices Streaming",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    def check_telemetry_latency(self) -> bool:
        """Verify telemetry collection latency is below threshold"""
        # Use timestamp() to get the last scrape time of metrics and compare
        # with the current server time to determine collection latency
        data = self.query_prometheus(f"time() - timestamp({self.STREAMING_METRIC})")

        if not data or not data.get("result"):
            self.checks.append(
                TelemetryCheck(
                    name="Telemetry Latency",
                    passed=False,
                    message="No telemetry metrics found to measure latency",
                )
            )
            return False

        high_latency = []
        latencies: dict[str, float] = {}

        for result in data["result"]:
            source = result["metric"].get("source", "unknown")
            try:
                latency = float(result["value"][1])
            except (IndexError, ValueError, TypeError):
                continue

            # Track per-device max latency
            if source not in latencies or latency > latencies[source]:
                latencies[source] = latency

        for source, latency in latencies.items():
            if latency > self.latency_threshold:
                high_latency.append({"device": source, "latency_seconds": round(latency, 2)})

        passed = len(high_latency) == 0 and len(latencies) > 0

        details = {
            "threshold_seconds": self.latency_threshold,
            "device_latencies": {k: round(v, 2) for k, v in sorted(latencies.items())},
            "high_latency_devices": high_latency,
        }

        if passed:
            max_latency = max(latencies.values()) if latencies else 0
            message = (
                f"All devices below {self.latency_threshold}s latency threshold "
                f"(max: {max_latency:.2f}s)"
            )
        else:
            message = (
                f"{len(high_latency)} device(s) exceed {self.latency_threshold}s latency threshold"
            )

        self.checks.append(
            TelemetryCheck(
                name="Telemetry Latency",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    def check_metric_freshness(self) -> bool:
        """Verify metrics were received in last 60 seconds for each expected device"""
        stale_devices = []
        fresh_devices = []

        for device in self.expected_devices:
            data = self.query_prometheus(f'{self.STREAMING_METRIC}{{source="{device}"}}')

            if not data or not data.get("result"):
                stale_devices.append({"device": device, "reason": "no metrics found"})
                continue

            # Check the most recent sample timestamp
            most_recent = 0.0
            for result in data["result"]:
                try:
                    ts = float(result["value"][0])
                    if ts > most_recent:
                        most_recent = ts
                except (IndexError, ValueError, TypeError):
                    continue

            current_time = datetime.now().timestamp()
            age = current_time - most_recent

            if age > 60:
                stale_devices.append({"device": device, "reason": f"last metric {int(age)}s ago"})
            else:
                fresh_devices.append(device)

        passed = len(stale_devices) == 0 and len(fresh_devices) > 0

        details = {
            "fresh_devices": fresh_devices,
            "stale_devices": stale_devices,
            "freshness_window_seconds": 60,
        }

        if passed:
            message = f"All {len(fresh_devices)} expected devices have fresh metrics (within 60s)"
        else:
            stale_names = [d["device"] for d in stale_devices]
            message = (
                f"{len(stale_devices)} device(s) with stale/missing metrics: "
                f"{', '.join(stale_names)}"
            )

        self.checks.append(
            TelemetryCheck(
                name="Metric Freshness",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    # Expected metric families that every device should produce
    EXPECTED_METRICS = [
        "network_interface_in_octets",
        "network_interface_out_octets",
        "network_interface_in_packets",
        "network_interface_out_packets",
        "network_bgp_session_state",
    ]

    def check_expected_metrics_per_device(self) -> bool:
        """Verify each expected device produces all expected metric families.

        Queries Prometheus for each metric type per device using a
        {source="<device>"} filter and reports per-device metric coverage.

        Requirements: 8.2, 8.5
        """
        devices_missing: dict[str, list[str]] = {}
        devices_present: dict[str, list[str]] = {}

        for device in self.expected_devices:
            missing: list[str] = []
            present: list[str] = []

            for metric in self.EXPECTED_METRICS:
                data = self.query_prometheus(f'{metric}{{source="{device}"}}')
                if data and data.get("result"):
                    present.append(metric)
                else:
                    missing.append(metric)

            devices_present[device] = present
            if missing:
                devices_missing[device] = missing

        passed = len(devices_missing) == 0

        details = {
            "expected_metrics": self.EXPECTED_METRICS,
            "per_device_coverage": {
                device: {
                    "present": devices_present[device],
                    "missing": devices_missing.get(device, []),
                    "coverage": f"{len(devices_present[device])}/{len(self.EXPECTED_METRICS)}",
                }
                for device in self.expected_devices
            },
            "devices_with_missing_metrics": list(devices_missing.keys()),
        }

        if passed:
            message = (
                f"All {len(self.expected_devices)} devices have all "
                f"{len(self.EXPECTED_METRICS)} expected metric families"
            )
        else:
            summaries = [
                f"{dev} missing {', '.join(metrics)}" for dev, metrics in devices_missing.items()
            ]
            message = f"{len(devices_missing)} device(s) with missing metrics: " + "; ".join(
                summaries
            )

        self.checks.append(
            TelemetryCheck(
                name="Expected Metrics Per Device",
                passed=passed,
                message=message,
                details=details,
            )
        )
        return passed

    def run_all_checks(self) -> bool:
        """Run all telemetry validation checks"""
        print("=" * 70)
        print("Telemetry Streaming Verification")
        print("=" * 70)
        print()

        # Connectivity is a prerequisite
        if not self.check_prometheus_connectivity():
            print("❌ Cannot connect to Prometheus. Aborting remaining checks.")
            return False

        self.check_devices_streaming()
        self.check_expected_metrics_per_device()
        self.check_telemetry_latency()
        self.check_metric_freshness()

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
            print("✅ All telemetry checks passed!")
        else:
            print("❌ Some telemetry checks failed. See details above.")

        return all_passed

    def get_report(self) -> dict:
        """Get validation report as dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "prometheus_url": self.prometheus_url,
            "expected_devices": self.expected_devices,
            "latency_threshold_seconds": self.latency_threshold,
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
        description="Validate telemetry streaming from network devices via Prometheus"
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)",
    )
    parser.add_argument(
        "--expected-devices",
        required=True,
        help="Comma-separated list of expected device names (e.g. spine1,spine2,leaf1,leaf2)",
    )
    parser.add_argument(
        "--latency-threshold",
        type=float,
        default=10.0,
        help="Maximum acceptable telemetry latency in seconds (default: 10)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    devices = [d.strip() for d in args.expected_devices.split(",") if d.strip()]
    if not devices:
        print("Error: --expected-devices must contain at least one device name")
        sys.exit(1)

    validator = TelemetryStreamingValidator(
        prometheus_url=args.prometheus_url,
        expected_devices=devices,
        latency_threshold=args.latency_threshold,
    )
    all_passed = validator.run_all_checks()

    if args.json:
        print()
        print(json.dumps(validator.get_report(), indent=2))

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
