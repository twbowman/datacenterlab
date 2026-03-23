#!/usr/bin/python

# Copyright: (c) 2024, Network Lab Team
# GNU General Public License v3.0+

"""
gnmi_validate - Ansible module for gNMI-based configuration validation.

Performs gNMI Get operations against network devices and compares actual
state against expected state using dictdiffer. Supports both OpenConfig
and vendor-native YANG schemas via the gNMI origin field.

Requirements: 7.1, 7.2, 7.3, 7.4, 16.6
"""

DOCUMENTATION = r"""
---
module: gnmi_validate
short_description: Validate network device state via gNMI Get
description:
  - Connects to a network device using pygnmi gNMIclient.
  - Performs a gNMI Get with optional origin field for dual-schema support
    (OpenConfig vs vendor-native YANG models).
  - Compares actual device state against expected state using dictdiffer.
  - Returns structured result with check_name, status, expected, actual,
    diffs, and remediation hints.
version_added: "1.0.0"
author:
  - Network Lab Team
options:
  host:
    description: Target device hostname or IP address.
    required: true
    type: str
  port:
    description: gNMI port on the target device.
    required: true
    type: int
  username:
    description: Username for gNMI authentication.
    required: true
    type: str
  password:
    description: Password for gNMI authentication.
    required: true
    type: str
  skip_verify:
    description: Skip TLS certificate verification.
    default: true
    type: bool
  check_name:
    description: Human-readable name for this validation check.
    required: true
    type: str
  path:
    description: gNMI path to query.
    required: true
    type: str
  origin:
    description: >
      gNMI origin field for schema selection.
      Use 'openconfig' for OpenConfig models, 'srl_nokia' for SR Linux native,
      'eos_native' for Arista native, 'juniper' for Juniper native.
    default: null
    type: str
  encoding:
    description: gNMI encoding format.
    default: json_ietf
    type: str
  expected:
    description: Expected state dictionary to compare against actual device state.
    required: true
    type: dict
  remediation_hint:
    description: Remediation suggestion displayed when validation fails.
    default: ''
    type: str
"""

EXAMPLES = r"""
- name: Validate BGP sessions via OpenConfig
  gnmi_validate:
    host: "{{ ansible_host }}"
    port: 57400
    username: admin
    password: admin
    check_name: bgp_sessions
    path: "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state"
    origin: openconfig
    expected:
      session_state: ESTABLISHED
    remediation_hint: "Check BGP config and OSPF underlay reachability"

- name: Validate EVPN state via SR Linux native path
  gnmi_validate:
    host: "{{ ansible_host }}"
    port: 57400
    username: admin
    password: admin
    check_name: evpn_state
    path: "/network-instance[name=default]/protocols/bgp/afi-safi[afi-safi-name=evpn]/admin-state"
    origin: srl_nokia
    expected:
      admin_state: enable
    remediation_hint: "Enable EVPN address family in BGP configuration"
"""

RETURN = r"""
result:
  description: Structured validation result.
  returned: always
  type: dict
  contains:
    check_name:
      description: Name of the validation check.
      type: str
    status:
      description: Validation status - 'pass' or 'fail'.
      type: str
    expected:
      description: Expected state provided as input.
      type: dict
    actual:
      description: Actual state retrieved from the device.
      type: dict
    diffs:
      description: List of differences found by dictdiffer.
      type: list
    remediation:
      description: Remediation hint if validation failed.
      type: str
    path:
      description: gNMI path that was queried.
      type: str
    origin:
      description: gNMI origin used for the query.
      type: str
"""

import traceback  # noqa: E402

from ansible.module_utils.basic import AnsibleModule  # noqa: E402

try:
    from pygnmi.client import gNMIclient

    HAS_PYGNMI = True
except ImportError:
    HAS_PYGNMI = False

try:
    import dictdiffer  # noqa: F401

    HAS_DICTDIFFER = True
except ImportError:
    HAS_DICTDIFFER = False


def extract_gnmi_value(response):
    """Extract the value payload from a pygnmi Get response.

    pygnmi returns a dict with a 'notification' key containing a list
    of notifications. Each notification has 'update' entries with
    'path' and 'val' keys. This function walks the response and
    returns a merged dict of all values.
    """
    if not response:
        return {}

    result = {}
    notifications = response.get("notification", [])
    for notification in notifications:
        updates = notification.get("update", [])
        for update in updates:
            val = update.get("val")
            if isinstance(val, dict):
                result.update(val)
            elif val is not None:
                # Scalar value — use the leaf path element as key
                path = update.get("path", "")
                key = path.rsplit("/", 1)[-1] if path else "value"
                result[key] = val
    return result


def _collect_values(tree, key):
    """Recursively collect all values for *key* found anywhere in *tree*.

    Handles dicts and lists. Returns a flat list of found values.
    """
    found = []
    if isinstance(tree, dict):
        for k, v in tree.items():
            if k == key:
                found.append(v)
            else:
                found.extend(_collect_values(v, key))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_collect_values(item, key))
    return found


def semantic_compare(expected, actual):
    """Compare expected state against a (possibly deeply nested) actual tree.

    For each key in *expected*:
    - If the key exists at the top level of *actual*, compare directly.
    - Otherwise, search the full *actual* tree for all occurrences of the
      key and compare the collected values against the expected value.

    Supported expected value types:
    - str / int / float / bool: every occurrence in actual must equal the
      expected value.
    - list: the set of collected values (or list items) must be a superset
      of the expected list.

    Returns a list of human-readable diff strings (empty == pass).
    """
    diffs = []

    for exp_key, exp_val in expected.items():
        # Normalise key: expected may use underscores, actual may use hyphens
        alt_key = exp_key.replace("_", "-")

        # Collect all occurrences of the key in the actual tree
        found = _collect_values(actual, exp_key)
        if not found:
            found = _collect_values(actual, alt_key)

        if not found:
            diffs.append(
                {
                    "field": exp_key,
                    "issue": "missing",
                    "expected": exp_val,
                    "actual": None,
                }
            )
            continue

        # Flatten: if found values are themselves lists, flatten one level
        flat = []
        for v in found:
            if isinstance(v, list):
                flat.extend(v)
            else:
                flat.append(v)

        if isinstance(exp_val, list):
            # List comparison: every expected item must appear in actual
            actual_set = {str(v) for v in flat}
            missing = [v for v in exp_val if str(v) not in actual_set]
            if missing:
                diffs.append(
                    {
                        "field": exp_key,
                        "issue": "missing_items",
                        "expected": exp_val,
                        "actual": list(actual_set),
                        "missing": missing,
                    }
                )
        else:
            # Scalar comparison: every occurrence must match
            mismatches = [v for v in flat if str(v) != str(exp_val)]
            if mismatches:
                diffs.append(
                    {
                        "field": exp_key,
                        "issue": "value_mismatch",
                        "expected": exp_val,
                        "actual": mismatches,
                    }
                )

    return diffs


def build_gnmi_path(path, origin=None):
    """Build a gNMI path string with optional origin prefix.

    When an origin is specified, pygnmi expects it as part of the
    path list element or handled via the path prefix. We return
    the path in a format suitable for pygnmi's get() method.
    """
    if origin:
        return f"{origin}:{path}"
    return path


def run_module():
    argument_spec = dict(  # noqa: C408
        host=dict(required=True, type="str"),  # noqa: C408
        port=dict(required=True, type="int"),  # noqa: C408
        username=dict(required=True, type="str"),  # noqa: C408
        password=dict(required=True, type="str", no_log=True),  # noqa: C408
        skip_verify=dict(default=True, type="bool"),  # noqa: C408
        check_name=dict(required=True, type="str"),  # noqa: C408
        path=dict(required=True, type="str"),  # noqa: C408
        origin=dict(default=None, type="str"),  # noqa: C408
        encoding=dict(default="json_ietf", type="str"),  # noqa: C408
        expected=dict(required=True, type="dict"),  # noqa: C408
        remediation_hint=dict(default="", type="str"),  # noqa: C408
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PYGNMI:
        module.fail_json(
            msg="pygnmi is required for this module. Install it with: pip install pygnmi"
        )

    if not HAS_DICTDIFFER:
        module.fail_json(
            msg="dictdiffer is required for this module. Install it with: pip install dictdiffer"
        )

    host = module.params["host"]
    port = module.params["port"]
    username = module.params["username"]
    password = module.params["password"]
    skip_verify = module.params["skip_verify"]
    check_name = module.params["check_name"]
    path = module.params["path"]
    origin = module.params["origin"]
    encoding = module.params["encoding"]
    expected = module.params["expected"]
    remediation_hint = module.params["remediation_hint"]

    # In check mode, return without connecting to the device
    if module.check_mode:
        module.exit_json(
            changed=False,
            result={  # noqa: C408
                "check_name": check_name,
                "status": "skipped",
                "expected": expected,
                "actual": {},
                "diffs": [],
                "remediation": "",
                "path": path,
                "origin": origin or "",
            },
        )

    gnmi_path = build_gnmi_path(path, origin)

    try:
        with gNMIclient(
            target=(host, port),
            username=username,
            password=password,
            insecure=False,
            skip_verify=skip_verify,
        ) as gc:
            response = gc.get(
                path=[gnmi_path],
                encoding=encoding,
            )
    except Exception as e:
        module.fail_json(
            msg=f"gNMI connection/query failed for {host}:{port} path={gnmi_path}: {str(e)}",
            exception=traceback.format_exc(),
            result={
                "check_name": check_name,
                "status": "error",
                "expected": expected,
                "actual": {},
                "diffs": [],
                "remediation": f"Verify device reachability and gNMI service. {remediation_hint}",
                "path": path,
                "origin": origin or "",
            },
        )

    actual = extract_gnmi_value(response)

    # Semantic comparison: search the nested actual tree for expected fields
    diffs = semantic_compare(expected, actual)

    status = "pass" if not diffs else "fail"

    result = {
        "check_name": check_name,
        "status": status,
        "expected": expected,
        "actual": actual,
        "diffs": diffs,
        "remediation": remediation_hint if status == "fail" else "",
        "path": path,
        "origin": origin or "",
    }

    # Module changed=False since validation is read-only.
    # We do NOT set failed=True on validation mismatch — the playbook
    # decides how to handle a 'fail' status via register + assert.
    module.exit_json(
        changed=False,
        result=result,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
