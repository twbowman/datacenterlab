#!/usr/bin/env python3
"""
Dynamic Ansible Inventory Plugin with gNMI OS Detection

This plugin queries containerlab-deployed devices via gNMI capabilities
to automatically detect their operating system and generate an Ansible
inventory with the appropriate ansible_network_os variable.

Validates: Requirements 1.4
"""

import json
import subprocess
import sys

import yaml


class DeviceOSDetector:
    """Detects device OS via gNMI capabilities"""

    # Mapping of gNMI capability strings to OS types
    OS_MAPPINGS = {
        "Nokia": "srlinux",
        "Arista": "eos",
        "SONiC": "sonic",
        "Juniper": "junos",
    }

    def __init__(self, topology_file="topology-srlinux.yml"):
        self.topology_file = topology_file
        self.topology_data = None

    def load_topology(self):
        """Load containerlab topology file"""
        try:
            with open(self.topology_file) as f:
                self.topology_data = yaml.safe_load(f)
            return True
        except FileNotFoundError:
            print(f"Error: Topology file {self.topology_file} not found", file=sys.stderr)
            return False
        except yaml.YAMLError as e:
            print(f"Error parsing topology file: {e}", file=sys.stderr)
            return False

    def get_gnmi_capabilities(self, host, port=57400, username="admin", password="NokiaSrl1!"):  # noqa: S107
        """
        Query gNMI capabilities from a device

        Returns the supported models/encodings from the device
        """
        try:
            # Use gnmic to query capabilities
            cmd = [
                "gnmic",
                "-a",
                f"{host}:{port}",
                "-u",
                username,
                "-p",
                password,
                "--insecure",
                "capabilities",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return result.stdout
            else:
                print(
                    f"Warning: Failed to get capabilities from {host}: {result.stderr}",
                    file=sys.stderr,
                )
                return None

        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout querying {host}", file=sys.stderr)
            return None
        except FileNotFoundError:
            print("Error: gnmic command not found. Please install gnmic.", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Warning: Error querying {host}: {e}", file=sys.stderr)
            return None

    def detect_os_from_capabilities(self, capabilities_output):
        """
        Parse gNMI capabilities output and detect OS type

        Args:
            capabilities_output: String output from gnmic capabilities command

        Returns:
            OS type string (srlinux, eos, sonic, junos) or 'unknown'
        """
        if not capabilities_output:
            return "unknown"

        # Check for vendor-specific strings in capabilities
        for vendor_key, os_type in self.OS_MAPPINGS.items():
            if vendor_key.lower() in capabilities_output.lower():
                return os_type

        return "unknown"

    def detect_os_from_labels(self, node_config):
        """
        Fallback: Detect OS from containerlab labels

        Args:
            node_config: Node configuration from topology file

        Returns:
            OS type string or None
        """
        if "labels" in node_config and "os" in node_config["labels"]:
            return node_config["labels"]["os"]
        return None

    def detect_os_from_kind(self, node_config, groups):
        """
        Fallback: Detect OS from containerlab kind

        Args:
            node_config: Node configuration from topology file
            groups: Groups configuration from topology file

        Returns:
            OS type string or None
        """
        # Check if node has a group
        if "group" in node_config and groups:
            group_name = node_config["group"]
            kind = groups[group_name].get("kind") if group_name in groups else None
        else:
            kind = node_config.get("kind")

        # Map kind to OS
        kind_mappings = {
            "nokia_srlinux": "srlinux",
            "arista_ceos": "eos",
            "sonic-vs": "sonic",
            "juniper_crpd": "junos",
        }

        return kind_mappings.get(kind)

    def detect_device_os(self, node_name, node_config, groups):
        """
        Detect device OS using multiple methods in order of preference:
        1. gNMI capabilities query (most reliable)
        2. Containerlab labels (if present)
        3. Containerlab kind (fallback)

        Args:
            node_name: Name of the node
            node_config: Node configuration from topology
            groups: Groups configuration from topology

        Returns:
            OS type string
        """
        # Skip non-network devices (clients, etc.)
        kind = node_config.get("kind", "")
        if "group" in node_config and groups:
            group_name = node_config["group"]
            if group_name in groups:
                kind = groups[group_name].get("kind", kind)

        if kind == "linux":
            return None  # Skip Linux containers

        # Get management IP
        mgmt_ip = node_config.get("mgmt-ipv4") or node_config.get("mgmt_ipv4")

        if not mgmt_ip:
            print(
                f"Warning: No management IP for {node_name}, using fallback detection",
                file=sys.stderr,
            )
        else:
            # Try gNMI capabilities detection
            capabilities = self.get_gnmi_capabilities(mgmt_ip)
            detected_os = self.detect_os_from_capabilities(capabilities)

            if detected_os != "unknown":
                print(
                    f"Detected {node_name} as {detected_os} via gNMI capabilities", file=sys.stderr
                )
                return detected_os

        # Fallback to labels
        os_from_labels = self.detect_os_from_labels(node_config)
        if os_from_labels:
            print(f"Detected {node_name} as {os_from_labels} via labels", file=sys.stderr)
            return os_from_labels

        # Fallback to kind
        os_from_kind = self.detect_os_from_kind(node_config, groups)
        if os_from_kind:
            print(f"Detected {node_name} as {os_from_kind} via kind", file=sys.stderr)
            return os_from_kind

        print(f"Warning: Could not detect OS for {node_name}", file=sys.stderr)
        return "unknown"

    def generate_inventory(self):
        """
        Generate Ansible inventory with detected OS types

        Returns:
            Dictionary in Ansible inventory format
        """
        if not self.topology_data and not self.load_topology():
            return None

        topology = self.topology_data.get("topology", {})
        nodes = topology.get("nodes", {})
        groups = topology.get("groups", {})

        # Initialize inventory structure
        inventory = {
            "all": {
                "children": {},
                "vars": {
                    "ansible_python_interpreter": "/usr/bin/python3",
                },
            }
        }

        # Group devices by OS
        os_groups = {}

        for node_name, node_config in nodes.items():
            detected_os = self.detect_device_os(node_name, node_config, groups)

            if not detected_os:
                continue  # Skip non-network devices

            # Get management IP
            mgmt_ip = node_config.get("mgmt-ipv4") or node_config.get("mgmt_ipv4")

            if not mgmt_ip:
                print(f"Warning: Skipping {node_name} - no management IP", file=sys.stderr)
                continue

            # Create OS group if it doesn't exist
            if detected_os not in os_groups:
                os_groups[detected_os] = {"hosts": {}, "vars": self._get_os_vars(detected_os)}

            # Add host to OS group
            os_groups[detected_os]["hosts"][node_name] = {
                "ansible_host": mgmt_ip,
                "ansible_network_os": detected_os,
            }

            # Add labels if present
            if "labels" in node_config:
                for key, value in node_config["labels"].items():
                    os_groups[detected_os]["hosts"][node_name][key] = value

        # Add OS groups to inventory
        for os_name, os_group in os_groups.items():
            inventory["all"]["children"][f"{os_name}_devices"] = os_group

        return inventory

    def _get_os_vars(self, os_type):
        """
        Get OS-specific Ansible variables

        Args:
            os_type: OS type string

        Returns:
            Dictionary of Ansible variables for this OS
        """
        os_vars = {
            "srlinux": {
                "ansible_connection": "local",
                "gnmi_port": 57400,
                "gnmi_username": "admin",
                "gnmi_password": "NokiaSrl1!",
                "gnmi_skip_verify": True,
            },
            "eos": {
                "ansible_connection": "httpapi",
                "ansible_httpapi_use_ssl": True,
                "ansible_httpapi_validate_certs": False,
                "ansible_user": "admin",
                "ansible_password": "admin",
                "ansible_httpapi_port": 443,
            },
            "sonic": {
                "ansible_connection": "httpapi",
                "ansible_httpapi_use_ssl": True,
                "ansible_httpapi_validate_certs": False,
                "ansible_user": "admin",
                "ansible_password": "admin",
            },
            "junos": {
                "ansible_connection": "netconf",
                "ansible_user": "admin",
                "ansible_password": "admin",
                "ansible_port": 830,
            },
        }

        return os_vars.get(os_type, {})


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate dynamic Ansible inventory with OS detection"
    )
    parser.add_argument(
        "-t",
        "--topology",
        default="topology-srlinux.yml",
        help="Path to containerlab topology file (default: topology-srlinux.yml)",
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Output inventory in JSON format (for Ansible dynamic inventory)",
    )

    args = parser.parse_args()

    detector = DeviceOSDetector(topology_file=args.topology)
    inventory = detector.generate_inventory()

    if not inventory:
        print("Error: Failed to generate inventory", file=sys.stderr)
        sys.exit(1)

    # Output in requested format
    if args.list:
        output = json.dumps(inventory, indent=2)
    else:
        output = yaml.dump(inventory, default_flow_style=False, sort_keys=False)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Inventory written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
