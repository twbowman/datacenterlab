"""Validation tests for gNMIc metric normalization config.

Validates that:
- All 10 processors exist in the gNMIc event-processors list
- Tier 1 processors are listed before Tier 2 processors
- No __name__ rewriting rules remain in Prometheus config
- Prometheus relabeling rule count is under 20
"""

from pathlib import Path

import pytest
import yaml

# Resolve paths relative to the monitoring/ directory
MONITORING_DIR = Path(__file__).parent.parent
GNMIC_CONFIG_PATH = MONITORING_DIR / "gnmic" / "gnmic-config.yml"
PROMETHEUS_CONFIG_PATH = MONITORING_DIR / "prometheus" / "prometheus.yml"

TIER_1_PROCESSORS = [
    "normalize-oc-interfaces",
    "normalize-oc-bgp",
    "normalize-oc-lldp",
    "normalize-oc-qos",
]

TIER_2_PROCESSORS = [
    "normalize-srl-ospf",
    "tag-srl-ospf",
    "normalize-srl-evpn",
    "tag-srl-evpn",
    "normalize-srl-vxlan",
    "tag-srl-vxlan",
]

ALL_PROCESSORS = TIER_1_PROCESSORS + TIER_2_PROCESSORS


@pytest.fixture()
def gnmic_config():
    """Load and return the parsed gNMIc config."""
    with open(GNMIC_CONFIG_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture()
def prometheus_config():
    """Load and return the parsed Prometheus config."""
    with open(PROMETHEUS_CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# gNMIc config validation
# ---------------------------------------------------------------------------


class TestGnmicProcessorsExist:
    """Verify all 10 processors are defined and wired to the output."""

    def test_all_processors_defined_in_processors_section(self, gnmic_config):
        defined = set(gnmic_config.get("processors", {}).keys())
        for name in ALL_PROCESSORS:
            assert name in defined, f"Processor '{name}' not found in processors section"

    def test_all_processors_in_event_processors_list(self, gnmic_config):
        ep_list = gnmic_config["outputs"]["prom"]["event-processors"]
        for name in ALL_PROCESSORS:
            assert name in ep_list, f"Processor '{name}' not in output event-processors list"

    def test_event_processors_count(self, gnmic_config):
        ep_list = gnmic_config["outputs"]["prom"]["event-processors"]
        assert len(ep_list) == len(ALL_PROCESSORS), (
            f"Expected {len(ALL_PROCESSORS)} event-processors, got {len(ep_list)}"
        )


class TestProcessorOrdering:
    """Verify Tier 1 processors appear before Tier 2 in the event-processors list."""

    def test_tier1_before_tier2(self, gnmic_config):
        ep_list = gnmic_config["outputs"]["prom"]["event-processors"]

        last_tier1_idx = -1
        for name in TIER_1_PROCESSORS:
            idx = ep_list.index(name)
            if idx > last_tier1_idx:
                last_tier1_idx = idx

        first_tier2_idx = len(ep_list)
        for name in TIER_2_PROCESSORS:
            idx = ep_list.index(name)
            if idx < first_tier2_idx:
                first_tier2_idx = idx

        assert last_tier1_idx < first_tier2_idx, (
            "Tier 1 processors must all appear before Tier 2 processors"
        )


# ---------------------------------------------------------------------------
# Prometheus config validation
# ---------------------------------------------------------------------------


class TestPrometheusNoNameRewriting:
    """Verify no target_label: __name__ rules remain in Prometheus config."""

    def _get_relabel_rules(self, prometheus_config):
        rules = []
        for job in prometheus_config.get("scrape_configs", []):
            rules.extend(job.get("metric_relabel_configs", []))
        return rules

    def test_no_name_target_label(self, prometheus_config):
        for rule in self._get_relabel_rules(prometheus_config):
            assert rule.get("target_label") != "__name__", (
                f"Found __name__ rewriting rule that should have been removed: {rule}"
            )


class TestPrometheusRuleCount:
    """Verify total Prometheus relabeling rule count is under 20."""

    def test_rule_count_under_20(self, prometheus_config):
        total = 0
        for job in prometheus_config.get("scrape_configs", []):
            total += len(job.get("metric_relabel_configs", []))
        assert total < 20, f"Expected fewer than 20 relabeling rules, got {total}"
