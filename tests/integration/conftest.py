"""
Pytest configuration for integration tests

Provides fixtures for integration testing with actual lab deployment.
Tests assume the lab is running on a remote server, accessed via ./lab wrapper.
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add scripts directory to path
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(scripts_dir))

LAB_SCRIPT = str(project_root / "scripts" / "lab")


@pytest.fixture(scope="session")
def lab_deployed():
    """
    Deploy lab for integration tests (session-scoped)

    Uses the ./lab wrapper to deploy on the remote server.
    """
    # Check if lab is already running
    result = subprocess.run(
        [LAB_SCRIPT, "status"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and "clab-gnmi-clos" in result.stdout:
        print("Lab already running, skipping deployment")
        yield True
        return

    # Deploy lab
    print("Deploying lab for integration tests...")
    deploy_result = subprocess.run(
        [LAB_SCRIPT, "deploy"],
        capture_output=True,
        text=True,
    )

    if deploy_result.returncode != 0:
        pytest.fail(f"Lab deployment failed: {deploy_result.stderr}")

    # Wait for devices to be ready
    print("Waiting for devices to be ready...")
    time.sleep(30)

    yield True


@pytest.fixture(scope="session")
def monitoring_deployed(lab_deployed):
    """
    Verify monitoring stack is running (session-scoped).
    Monitoring is included in the topology, so just check it's up.
    """
    result = subprocess.run(
        [LAB_SCRIPT, "exec", "docker ps --filter name=clab-monitoring --format '{{.Names}}'"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout.strip():
        print("Monitoring stack is running")
        yield True
        return

    pytest.fail("Monitoring stack is not running. Deploy with: ./lab deploy")


@pytest.fixture
def topology_config():
    """Load topology configuration"""
    topology_file = project_root / "topologies/topology-srlinux.yml"
    with open(topology_file) as f:
        return yaml.safe_load(f)


@pytest.fixture
def device_list(topology_config):
    """Extract list of devices from topology"""
    nodes = topology_config.get("topology", {}).get("nodes", {})
    return list(nodes.keys())


@pytest.fixture
def prometheus_url():
    """Prometheus URL (via SSH tunnel from ./lab tunnel)"""
    return "http://localhost:9090"


@pytest.fixture
def grafana_url():
    """Grafana URL (via SSH tunnel from ./lab tunnel)"""
    return "http://localhost:3000"


@pytest.fixture
def gnmic_url():
    """gNMIc metrics endpoint URL (via SSH tunnel from ./lab tunnel)"""
    return "http://localhost:9273"


def wait_for_service(url, timeout=60, interval=5):
    """Wait for a service to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    return False


@pytest.fixture
def wait_for_prometheus(prometheus_url):
    """Wait for Prometheus to be ready (requires ./lab tunnel)"""
    if not wait_for_service(f"{prometheus_url}/-/ready"):
        pytest.fail("Prometheus not reachable. Run: ./lab tunnel")
    return True


@pytest.fixture
def wait_for_grafana(grafana_url):
    """Wait for Grafana to be ready (requires ./lab tunnel)"""
    if not wait_for_service(f"{grafana_url}/api/health"):
        pytest.fail("Grafana not reachable. Run: ./lab tunnel")
    return True
