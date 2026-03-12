"""
Pytest configuration for integration tests

Provides fixtures for integration testing with actual lab deployment.
"""

import pytest
import subprocess
import time
import os
import sys
import yaml
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add scripts directory to path
scripts_dir = project_root / 'scripts'
sys.path.insert(0, str(scripts_dir))


@pytest.fixture(scope="session")
def orb_prefix():
    """Return the ORB command prefix for macOS ARM"""
    return "orb -m clab"


@pytest.fixture(scope="session")
def lab_deployed(orb_prefix):
    """
    Deploy lab for integration tests (session-scoped)
    
    This fixture deploys the lab once per test session and tears it down at the end.
    """
    # Check if lab is already running
    result = subprocess.run(
        f"{orb_prefix} docker ps --filter name=clab-gnmi-clos --format '{{{{.Names}}}}'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print("Lab already running, skipping deployment")
        yield True
        return
    
    # Deploy lab
    print("Deploying lab for integration tests...")
    deploy_result = subprocess.run(
        f"{orb_prefix} sudo containerlab deploy -t topology.yml",
        shell=True,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if deploy_result.returncode != 0:
        pytest.fail(f"Lab deployment failed: {deploy_result.stderr}")
    
    # Wait for devices to be ready
    print("Waiting for devices to be ready...")
    time.sleep(30)
    
    yield True
    
    # Teardown: destroy lab
    # Note: Commented out to allow inspection after tests
    # Uncomment if you want automatic cleanup
    # print("Destroying lab after integration tests...")
    # subprocess.run(
    #     f"{orb_prefix} sudo containerlab destroy -t topology.yml",
    #     shell=True,
    #     cwd=project_root
    # )


@pytest.fixture(scope="session")
def monitoring_deployed(orb_prefix, lab_deployed):
    """
    Deploy monitoring stack for integration tests (session-scoped)
    """
    # Check if monitoring is already running
    result = subprocess.run(
        f"{orb_prefix} docker ps --filter name=clab-monitoring --format '{{{{.Names}}}}'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print("Monitoring stack already running, skipping deployment")
        yield True
        return
    
    # Deploy monitoring stack
    print("Deploying monitoring stack for integration tests...")
    deploy_result = subprocess.run(
        f"{orb_prefix} sudo containerlab deploy -t topology-monitoring.yml",
        shell=True,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if deploy_result.returncode != 0:
        pytest.fail(f"Monitoring deployment failed: {deploy_result.stderr}")
    
    # Wait for monitoring services to be ready
    print("Waiting for monitoring services to be ready...")
    time.sleep(20)
    
    yield True
    
    # Teardown: destroy monitoring
    # Note: Commented out to allow inspection after tests
    # print("Destroying monitoring stack after integration tests...")
    # subprocess.run(
    #     f"{orb_prefix} sudo containerlab destroy -t topology-monitoring.yml",
    #     shell=True,
    #     cwd=project_root
    # )


@pytest.fixture
def topology_config():
    """Load topology configuration"""
    topology_file = project_root / "topology.yml"
    with open(topology_file, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def device_list(topology_config):
    """Extract list of devices from topology"""
    nodes = topology_config.get('topology', {}).get('nodes', {})
    return list(nodes.keys())


@pytest.fixture
def prometheus_url():
    """Prometheus URL for queries"""
    return "http://localhost:9090"


@pytest.fixture
def grafana_url():
    """Grafana URL for dashboard access"""
    return "http://localhost:3000"


@pytest.fixture
def gnmic_url():
    """gNMIc metrics endpoint URL"""
    return "http://localhost:9273"


def wait_for_service(url, timeout=60, interval=5):
    """
    Wait for a service to become available
    
    Args:
        url: Service URL to check
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
    
    Returns:
        bool: True if service is available, False otherwise
    """
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
    """Wait for Prometheus to be ready"""
    if not wait_for_service(f"{prometheus_url}/-/ready"):
        pytest.fail("Prometheus did not become ready in time")
    return True


@pytest.fixture
def wait_for_grafana(grafana_url):
    """Wait for Grafana to be ready"""
    if not wait_for_service(f"{grafana_url}/api/health"):
        pytest.fail("Grafana did not become ready in time")
    return True
