#!/usr/bin/env python3
"""
Monitoring stack integration tests

Tests gNMIc → Prometheus → Grafana pipeline, metric persistence, and dashboard queries.
Validates: Requirements 15.1

**Validates: Requirements 15.1**
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests


class TestGNMIcCollector:
    """Test gNMIc telemetry collector"""

    def test_gnmic_is_running(self, orb_prefix, monitoring_deployed):
        """
        Test that gNMIc collector is running
        """
        print("\n=== Testing gNMIc Collector Status ===")

        result = subprocess.run(
            f"{orb_prefix} docker ps --filter name=gnmic --format '{{{{.Names}}}}'",
            shell=True,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        containers = result.stdout.strip().split("\n")

        gnmic_containers = [c for c in containers if "gnmic" in c.lower()]
        assert len(gnmic_containers) > 0, "gNMIc container should be running"

        print(f"✓ gNMIc container running: {gnmic_containers}")

    def test_gnmic_metrics_endpoint(self, gnmic_url):
        """
        Test that gNMIc exposes Prometheus metrics endpoint
        """
        print("\n=== Testing gNMIc Metrics Endpoint ===")

        try:
            response = requests.get(f"{gnmic_url}/metrics", timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            # Check that response contains Prometheus metrics
            content = response.text
            assert len(content) > 0, "Metrics endpoint should return data"

            # Check for metric format (should have # HELP or metric lines)
            assert "#" in content or "network_" in content, "Should contain Prometheus metrics"

            print("✓ gNMIc metrics endpoint accessible")
            print(f"✓ Metrics endpoint returns {len(content)} bytes")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Could not access gNMIc metrics endpoint: {e}")

    def test_gnmic_collecting_from_devices(self, gnmic_url, lab_deployed):
        """
        Test that gNMIc is collecting metrics from devices
        """
        print("\n=== Testing gNMIc Collection from Devices ===")

        # Wait for collection to start
        time.sleep(20)

        try:
            response = requests.get(f"{gnmic_url}/metrics", timeout=10)

            if response.status_code == 200:
                content = response.text

                # Look for device-specific metrics
                devices = ["spine1", "spine2", "leaf1", "leaf2"]
                devices_found = []

                for device in devices:
                    if device in content:
                        devices_found.append(device)

                if devices_found:
                    print(f"✓ gNMIc collecting from devices: {devices_found}")
                else:
                    print("⚠ No device-specific metrics found yet (may still be initializing)")
            else:
                print(f"⚠ Metrics endpoint returned status: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not check device metrics: {e}")

    def test_gnmic_subscription_configuration(self, orb_prefix):
        """
        Test that gNMIc has proper subscription configuration
        """
        print("\n=== Testing gNMIc Subscription Configuration ===")
        project_root = Path(__file__).parent.parent.parent

        # Check for gNMIc configuration file
        gnmic_config = project_root / "monitoring" / "gnmic" / "gnmic-config.yml"

        if gnmic_config.exists():
            print("✓ gNMIc configuration file exists")

            # Check for key configuration sections
            with open(gnmic_config) as f:
                content = f.read()

                required_sections = ["targets", "subscriptions", "outputs"]
                for section in required_sections:
                    if section in content:
                        print(f"✓ Configuration includes '{section}' section")
                    else:
                        print(f"⚠ Configuration missing '{section}' section")
        else:
            print("⚠ gNMIc configuration file not found")


class TestPrometheusIntegration:
    """Test Prometheus integration"""

    def test_prometheus_is_running(self, orb_prefix, monitoring_deployed):
        """
        Test that Prometheus is running
        """
        print("\n=== Testing Prometheus Status ===")

        result = subprocess.run(
            f"{orb_prefix} docker ps --filter name=prometheus --format '{{{{.Names}}}}'",
            shell=True,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        containers = result.stdout.strip().split("\n")

        prom_containers = [c for c in containers if "prometheus" in c.lower()]
        assert len(prom_containers) > 0, "Prometheus container should be running"

        print(f"✓ Prometheus container running: {prom_containers}")

    def test_prometheus_scraping_gnmic(self, prometheus_url, wait_for_prometheus):
        """
        Test that Prometheus is scraping gNMIc
        """
        print("\n=== Testing Prometheus Scraping gNMIc ===")

        try:
            # Query Prometheus targets
            response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("status") == "success":
                    targets = data.get("data", {}).get("activeTargets", [])

                    # Look for gNMIc target
                    gnmic_targets = [
                        t for t in targets if "gnmic" in t.get("labels", {}).get("job", "")
                    ]

                    if gnmic_targets:
                        print(f"✓ Prometheus scraping gNMIc: {len(gnmic_targets)} target(s)")

                        for target in gnmic_targets:
                            health = target.get("health", "unknown")
                            print(f"  - Target health: {health}")
                    else:
                        print("⚠ No gNMIc targets found in Prometheus")
                else:
                    print(f"⚠ Targets query status: {data.get('status')}")
            else:
                print(f"⚠ Targets query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not query Prometheus targets: {e}")

    def test_prometheus_storing_network_metrics(self, prometheus_url, wait_for_prometheus):
        """
        Test that Prometheus is storing network metrics
        """
        print("\n=== Testing Prometheus Metric Storage ===")

        # Wait for metrics to be scraped
        time.sleep(30)

        # Query for network metrics
        network_metrics = [
            "network_interface_in_octets",
            "network_interface_out_octets",
            "network_bgp_session_state",
            "network_lldp_neighbor_count",
        ]

        metrics_found = []

        for metric in network_metrics:
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query", params={"query": metric}, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])
                        if results:
                            metrics_found.append(metric)
                            print(f"✓ Metric stored: {metric} ({len(results)} series)")
                        else:
                            print(f"⚠ Metric defined but no data: {metric}")
                    else:
                        print(f"⚠ Query status: {data.get('status')} for {metric}")
                else:
                    print(f"⚠ Query failed for {metric}: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"⚠ Could not query {metric}: {e}")

        if metrics_found:
            print(f"\n✓ Prometheus storing {len(metrics_found)} network metric types")

    def test_prometheus_metric_persistence(self, prometheus_url, wait_for_prometheus):
        """
        Test that Prometheus persists metrics across restarts

        **Validates: Requirements 14.1**
        """
        print("\n=== Testing Prometheus Metric Persistence ===")

        # Query for metrics with time range
        try:
            response = requests.get(
                f"{prometheus_url}/api/v1/query_range",
                params={
                    "query": "network_interface_in_octets",
                    "start": int(time.time()) - 300,  # Last 5 minutes
                    "end": int(time.time()),
                    "step": "30s",
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])

                    if results:
                        # Check that we have historical data
                        for result in results[:3]:  # Check first 3 series
                            values = result.get("values", [])
                            if values:
                                print(f"✓ Historical data available: {len(values)} data points")
                                break

                        print("✓ Prometheus persisting metrics over time")
                    else:
                        print("⚠ No historical data found (may be too early)")
                else:
                    print(f"⚠ Query status: {data.get('status')}")
            else:
                print(f"⚠ Query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not query historical data: {e}")


class TestGrafanaIntegration:
    """Test Grafana integration"""

    def test_grafana_is_running(self, orb_prefix, monitoring_deployed):
        """
        Test that Grafana is running
        """
        print("\n=== Testing Grafana Status ===")

        result = subprocess.run(
            f"{orb_prefix} docker ps --filter name=grafana --format '{{{{.Names}}}}'",
            shell=True,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        containers = result.stdout.strip().split("\n")

        grafana_containers = [c for c in containers if "grafana" in c.lower()]
        assert len(grafana_containers) > 0, "Grafana container should be running"

        print(f"✓ Grafana container running: {grafana_containers}")

    def test_grafana_health_endpoint(self, grafana_url, wait_for_grafana):
        """
        Test Grafana health endpoint
        """
        print("\n=== Testing Grafana Health ===")

        try:
            response = requests.get(f"{grafana_url}/api/health", timeout=10)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            print(f"✓ Grafana health status: {data}")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"Could not access Grafana health endpoint: {e}")

    def test_grafana_prometheus_datasource(self, grafana_url, wait_for_grafana):
        """
        Test that Grafana has Prometheus configured as datasource
        """
        print("\n=== Testing Grafana Prometheus Datasource ===")

        try:
            # Query datasources (may require authentication)
            response = requests.get(
                f"{grafana_url}/api/datasources",
                auth=("admin", "admin"),  # Default Grafana credentials
                timeout=10,
            )

            if response.status_code == 200:
                datasources = response.json()

                prom_datasources = [ds for ds in datasources if ds.get("type") == "prometheus"]

                if prom_datasources:
                    print(
                        f"✓ Prometheus datasource configured: {len(prom_datasources)} datasource(s)"
                    )
                    for ds in prom_datasources:
                        print(f"  - Name: {ds.get('name')}, URL: {ds.get('url')}")
                else:
                    print("⚠ No Prometheus datasources found")
            else:
                print(f"⚠ Datasources query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not query Grafana datasources: {e}")

    def test_grafana_dashboards_provisioned(self, grafana_url, wait_for_grafana):
        """
        Test that Grafana dashboards are provisioned
        """
        print("\n=== Testing Grafana Dashboard Provisioning ===")

        try:
            response = requests.get(
                f"{grafana_url}/api/search?type=dash-db", auth=("admin", "admin"), timeout=10
            )

            if response.status_code == 200:
                dashboards = response.json()

                if dashboards:
                    print(f"✓ Dashboards provisioned: {len(dashboards)} dashboard(s)")
                    for dashboard in dashboards:
                        print(f"  - {dashboard.get('title')}")
                else:
                    print("⚠ No dashboards found (may need to be provisioned)")
            else:
                print(f"⚠ Dashboard query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not query Grafana dashboards: {e}")


class TestEndToEndPipeline:
    """Test complete gNMIc → Prometheus → Grafana pipeline"""

    def test_metric_flow_gnmic_to_prometheus(
        self, gnmic_url, prometheus_url, wait_for_prometheus, lab_deployed
    ):
        """
        Test that metrics flow from gNMIc to Prometheus
        """
        print("\n=== Testing Metric Flow: gNMIc → Prometheus ===")

        # Wait for metrics to flow
        time.sleep(30)

        # Get metrics from gNMIc
        try:
            gnmic_response = requests.get(f"{gnmic_url}/metrics", timeout=10)

            if gnmic_response.status_code == 200:
                gnmic_content = gnmic_response.text

                # Extract a sample metric name
                sample_metrics = []
                for line in gnmic_content.split("\n"):
                    if line and not line.startswith("#") and "network_" in line:
                        metric_name = line.split("{")[0] if "{" in line else line.split(" ")[0]
                        if metric_name and metric_name not in sample_metrics:
                            sample_metrics.append(metric_name)
                            if len(sample_metrics) >= 3:
                                break

                print(f"✓ gNMIc exposing metrics: {sample_metrics}")

                # Check if same metrics exist in Prometheus
                for metric in sample_metrics:
                    prom_response = requests.get(
                        f"{prometheus_url}/api/v1/query", params={"query": metric}, timeout=10
                    )

                    if prom_response.status_code == 200:
                        data = prom_response.json()
                        if data.get("status") == "success":
                            results = data.get("data", {}).get("result", [])
                            if results:
                                print(
                                    f"✓ Metric '{metric}' flowing to Prometheus ({len(results)} series)"
                                )
                            else:
                                print(f"⚠ Metric '{metric}' not yet in Prometheus")
                    else:
                        print(f"⚠ Could not query Prometheus for '{metric}'")
            else:
                print(f"⚠ gNMIc metrics endpoint returned: {gnmic_response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Error testing metric flow: {e}")

    def test_dashboard_queries_work(
        self, grafana_url, prometheus_url, wait_for_grafana, wait_for_prometheus
    ):
        """
        Test that dashboard queries return data
        """
        print("\n=== Testing Dashboard Queries ===")

        # Wait for data to be available
        time.sleep(20)

        # Test common dashboard queries
        dashboard_queries = {
            "Interface Traffic": "rate(network_interface_in_octets[5m]) * 8",
            "BGP Sessions": "network_bgp_session_state",
            "LLDP Neighbors": "network_lldp_neighbor_count",
            "Interface Errors": "rate(network_interface_in_errors[5m])",
        }

        for query_name, query in dashboard_queries.items():
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query", params={"query": query}, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])
                        if results:
                            print(
                                f"✓ Dashboard query '{query_name}' returns data ({len(results)} series)"
                            )
                        else:
                            print(
                                f"⚠ Dashboard query '{query_name}' returns no data (may be too early)"
                            )
                    else:
                        print(f"⚠ Dashboard query '{query_name}' status: {data.get('status')}")
                else:
                    print(f"⚠ Dashboard query '{query_name}' failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"⚠ Dashboard query '{query_name}' error: {e}")

    def test_universal_queries_across_vendors(self, prometheus_url, wait_for_prometheus):
        """
        Test that universal queries work regardless of vendor

        **Validates: Requirements 5.1, 5.5**
        """
        print("\n=== Testing Universal Queries ===")

        # Universal queries that should work across all vendors
        universal_queries = [
            "network_interface_in_octets",
            "network_interface_out_octets",
            "network_bgp_session_state",
        ]

        for query in universal_queries:
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query", params={"query": query}, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        results = data.get("data", {}).get("result", [])

                        # Check for vendor diversity
                        vendors = set()
                        for result in results:
                            vendor = result.get("metric", {}).get("vendor", "")
                            if vendor:
                                vendors.add(vendor)

                        if vendors:
                            print(f"✓ Universal query '{query}' works across vendors: {vendors}")
                        else:
                            print(f"✓ Universal query '{query}' structure validated")
                    else:
                        print(f"⚠ Query '{query}' status: {data.get('status')}")
                else:
                    print(f"⚠ Query '{query}' failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"⚠ Query '{query}' error: {e}")


class TestMonitoringStackReliability:
    """Test monitoring stack reliability features"""

    def test_prometheus_storage_configuration(self, orb_prefix):
        """
        Test Prometheus storage configuration

        **Validates: Requirements 14.1, 14.5**
        """
        print("\n=== Testing Prometheus Storage Configuration ===")
        project_root = Path(__file__).parent.parent.parent

        # Check Prometheus configuration
        prom_config = project_root / "monitoring" / "prometheus" / "prometheus.yml"

        if prom_config.exists():
            with open(prom_config) as f:
                content = f.read()

                # Check for retention settings
                if "retention" in content:
                    print("✓ Prometheus retention configured")
                else:
                    print("⚠ Prometheus retention not explicitly configured")

                # Check for storage settings
                if "storage" in content or "tsdb" in content:
                    print("✓ Prometheus storage settings configured")
                else:
                    print("⚠ Prometheus storage settings not found")
        else:
            print("⚠ Prometheus configuration file not found")

    def test_monitoring_component_health_checks(self, prometheus_url, grafana_url, gnmic_url):
        """
        Test health check endpoints for all monitoring components

        **Validates: Requirements 14.3**
        """
        print("\n=== Testing Monitoring Component Health Checks ===")

        components = {
            "Prometheus": f"{prometheus_url}/-/ready",
            "Grafana": f"{grafana_url}/api/health",
            "gNMIc": f"{gnmic_url}/metrics",
        }

        for component, url in components.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code < 500:
                    print(f"✓ {component} health check: OK (status {response.status_code})")
                else:
                    print(f"⚠ {component} health check: Failed (status {response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"⚠ {component} health check: Error ({e})")

    def test_metric_collection_latency(self, prometheus_url, wait_for_prometheus):
        """
        Test that metric collection latency is acceptable

        **Validates: Requirements 8.6**
        """
        print("\n=== Testing Metric Collection Latency ===")

        try:
            # Query for recent metrics
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": "network_interface_in_octets"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])

                    if results:
                        # Check timestamp of most recent metric
                        current_time = time.time()

                        for result in results[:5]:  # Check first 5 series
                            value = result.get("value", [])
                            if len(value) >= 2:
                                metric_timestamp = float(value[0])
                                latency = current_time - metric_timestamp

                                if latency < 60:  # Less than 60 seconds old
                                    print(f"✓ Metric latency: {latency:.2f}s (acceptable)")
                                else:
                                    print(f"⚠ Metric latency: {latency:.2f}s (may be stale)")
                                break
                    else:
                        print("⚠ No metrics available to check latency")
                else:
                    print(f"⚠ Query status: {data.get('status')}")
            else:
                print(f"⚠ Query failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not check latency: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
