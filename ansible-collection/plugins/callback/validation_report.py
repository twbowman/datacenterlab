#!/usr/bin/python

# Copyright: (c) 2024, Network Lab Team
# GNU General Public License v3.0+

"""
validation_report - Ansible callback plugin that aggregates gnmi_validate
results across all hosts and tasks into a structured JSON report.

Requirements: 7.7, 8.7
"""

DOCUMENTATION = r"""
---
callback: validation_report
type: aggregate
short_description: Aggregates gnmi_validate results into a JSON report
description:
  - Collects results from gnmi_validate module tasks across all hosts.
  - Produces a structured JSON report with per-device checks, diffs,
    remediation hints, and summary statistics.
  - Writes the report to validation-report.json in the current directory.
requirements:
  - The gnmi_validate module must be used in the playbook.
"""

import json  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

from ansible.plugins.callback import CallbackBase  # noqa: E402


class CallbackModule(CallbackBase):
    """Aggregate gnmi_validate results into a JSON validation report."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "validation_report"
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        self._start_time = None
        self._devices = {}  # host -> { checks: [], vendor, os }
        self._inventory_source = ""

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def v2_playbook_on_start(self, playbook):
        self._start_time = time.monotonic()
        sources = (
            playbook._loader._FILE_CACHE.keys() if hasattr(playbook._loader, "_FILE_CACHE") else []
        )
        if sources:
            self._inventory_source = str(next(iter(sources), ""))

    def v2_playbook_on_stats(self, stats):  # noqa: ARG002
        """Called at the very end of the playbook — write the report."""
        self._write_report()

    # ------------------------------------------------------------------
    # Task result handlers
    # ------------------------------------------------------------------

    def _process_result(self, result):
        """Extract gnmi_validate result from a task result object."""
        task_result = result._result
        # Only process results that contain our gnmi_validate 'result' key
        if "result" not in task_result:
            return
        check = task_result["result"]
        if not isinstance(check, dict) or "check_name" not in check:
            return

        host = result._host.get_name()
        host_vars = result._host.vars if hasattr(result._host, "vars") else {}

        if host not in self._devices:
            self._devices[host] = {
                "name": host,
                "vendor": host_vars.get("vendor", "unknown"),
                "os": host_vars.get("ansible_network_os", "unknown"),
                "checks": [],
            }

        self._devices[host]["checks"].append(
            {
                "name": check.get("check_name", ""),
                "status": check.get("status", "unknown"),
                "path": check.get("path", ""),
                "origin": check.get("origin", ""),
                "expected": check.get("expected", {}),
                "actual": check.get("actual", {}),
                "diffs": check.get("diffs", []),
                "remediation": check.get("remediation", ""),
            }
        )

    def v2_runner_on_ok(self, result):
        self._process_result(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):  # noqa: ARG002
        self._process_result(result)

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def _write_report(self):
        """Build and write the JSON validation report."""
        duration = time.monotonic() - self._start_time if self._start_time else 0

        devices_list = []
        total_checks = 0
        total_passed = 0
        total_failed = 0

        for host_data in self._devices.values():
            checks = host_data["checks"]
            passed = sum(1 for c in checks if c["status"] == "pass")
            failed = sum(1 for c in checks if c["status"] == "fail")
            total_checks += len(checks)
            total_passed += passed
            total_failed += failed

            devices_list.append(
                {
                    "name": host_data["name"],
                    "vendor": host_data["vendor"],
                    "os": host_data["os"],
                    "checks": checks,
                    "summary": {
                        "total": len(checks),
                        "passed": passed,
                        "failed": failed,
                    },
                }
            )

        report = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "inventory": self._inventory_source,
            "devices": devices_list,
            "summary": {
                "total_devices": len(devices_list),
                "total_checks": total_checks,
                "passed": total_passed,
                "failed": total_failed,
                "duration_seconds": round(duration, 2),
            },
        }

        report_path = os.path.join(os.getcwd(), "validation-report.json")
        try:
            with open(report_path, "w") as fh:
                json.dump(report, fh, indent=2, default=str)
            self._display.display(f"Validation report written to {report_path}", color="green")
        except OSError as exc:
            self._display.warning(f"Failed to write validation report: {exc}")
