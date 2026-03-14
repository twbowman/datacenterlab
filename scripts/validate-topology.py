#!/usr/bin/env python3
"""
Topology Validator for ContainerLab

Validates topology definition files before deployment to catch errors early.
Checks for:
- Required fields (kind, image)
- Supported device types
- Circular dependencies in links
- Provides specific error messages for validation failures
"""

import argparse
import sys
from pathlib import Path

import yaml


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, component: str, message: str, remediation: str = ""):
        self.component = component
        self.message = message
        self.remediation = remediation
        super().__init__(f"{component}: {message}")


class TopologyValidator:
    """Validates ContainerLab topology definitions"""

    SUPPORTED_KINDS = {"nokia_srlinux", "arista_ceos", "sonic-vs", "juniper_crpd", "linux"}

    REQUIRED_NODE_FIELDS = ["kind"]

    def __init__(self, topology_file: str):
        self.topology_file = Path(topology_file)
        self.topology = None
        self.errors = []
        self.warnings = []

    def validate(self) -> bool:
        """Run all validation checks"""
        try:
            self._load_topology()
            self._validate_structure()
            self._validate_nodes()
            self._validate_links()
            self._check_circular_dependencies()

            return not self.errors

        except Exception as e:
            self.errors.append(
                ValidationError(
                    component="topology_validator",
                    message=f"Unexpected error: {str(e)}",
                    remediation="Check topology file syntax and structure",
                )
            )
            return False

    def _load_topology(self):
        """Load and parse topology YAML file"""
        if not self.topology_file.exists():
            raise ValidationError(
                component="file_loader",
                message=f"Topology file not found: {self.topology_file}",
                remediation="Provide a valid topology file path",
            )

        try:
            with open(self.topology_file) as f:
                self.topology = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(
                component="yaml_parser",
                message=f"Invalid YAML syntax: {str(e)}",
                remediation="Fix YAML syntax errors in topology file",
            ) from e

    def _validate_structure(self):
        """Validate top-level topology structure"""
        if not isinstance(self.topology, dict):
            raise ValidationError(
                component="structure_validator",
                message="Topology must be a YAML dictionary",
                remediation="Ensure topology file has proper YAML structure",
            )

        if "name" not in self.topology:
            self.errors.append(
                ValidationError(
                    component="structure_validator",
                    message="Missing required field: 'name'",
                    remediation="Add 'name' field to topology definition",
                )
            )

        if "topology" not in self.topology:
            raise ValidationError(
                component="structure_validator",
                message="Missing required field: 'topology'",
                remediation="Add 'topology' section to topology definition",
            )

        if "nodes" not in self.topology.get("topology", {}):
            raise ValidationError(
                component="structure_validator",
                message="Missing required field: 'topology.nodes'",
                remediation="Add 'nodes' section under 'topology'",
            )

    def _validate_nodes(self):
        """Validate node definitions"""
        nodes = self.topology["topology"].get("nodes", {})
        groups = self.topology["topology"].get("groups", {})

        if not nodes:
            self.warnings.append("No nodes defined in topology")
            return

        for node_name, node_config in nodes.items():
            self._validate_node(node_name, node_config, groups)

    def _validate_node(self, node_name: str, node_config: dict, groups: dict):
        """Validate individual node configuration"""
        # Check if node uses a group
        if "group" in node_config:
            group_name = node_config["group"]
            if group_name not in groups:
                self.errors.append(
                    ValidationError(
                        component=f"node:{node_name}",
                        message=f"References undefined group: '{group_name}'",
                        remediation=f"Define group '{group_name}' in topology.groups or remove group reference",
                    )
                )
                return

            # Merge group config with node config
            group_config = groups[group_name]
            effective_config = {**group_config, **node_config}
        else:
            effective_config = node_config

        # Check required fields
        for field in self.REQUIRED_NODE_FIELDS:
            if field not in effective_config:
                self.errors.append(
                    ValidationError(
                        component=f"node:{node_name}",
                        message=f"Missing required field: '{field}'",
                        remediation=f"Add '{field}' field to node '{node_name}' or its group",
                    )
                )

        # Validate kind
        kind = effective_config.get("kind")
        if kind and kind not in self.SUPPORTED_KINDS:
            self.errors.append(
                ValidationError(
                    component=f"node:{node_name}",
                    message=f"Unsupported device kind: '{kind}'",
                    remediation=f"Use one of supported kinds: {', '.join(sorted(self.SUPPORTED_KINDS))}",
                )
            )

        # Validate image is specified for network devices
        if kind and kind != "linux" and "image" not in effective_config:
            self.errors.append(
                ValidationError(
                    component=f"node:{node_name}",
                    message=f"Missing required field: 'image' for kind '{kind}'",
                    remediation=f"Add 'image' field to node '{node_name}' or its group",
                )
            )

    def _validate_links(self):
        """Validate link definitions"""
        links = self.topology["topology"].get("links", [])
        nodes = self.topology["topology"].get("nodes", {})

        if not links:
            self.warnings.append("No links defined in topology")
            return

        for idx, link in enumerate(links):
            self._validate_link(idx, link, nodes)

    def _validate_link(self, idx: int, link: dict, nodes: dict):
        """Validate individual link configuration"""
        if "endpoints" not in link:
            self.errors.append(
                ValidationError(
                    component=f"link:{idx}",
                    message="Missing required field: 'endpoints'",
                    remediation=f"Add 'endpoints' field to link at index {idx}",
                )
            )
            return

        endpoints = link["endpoints"]
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            self.errors.append(
                ValidationError(
                    component=f"link:{idx}",
                    message="Link must have exactly 2 endpoints",
                    remediation=f"Ensure link at index {idx} has 'endpoints' list with 2 items",
                )
            )
            return

        # Validate endpoint format and node existence
        for endpoint in endpoints:
            if ":" not in endpoint:
                self.errors.append(
                    ValidationError(
                        component=f"link:{idx}",
                        message=f"Invalid endpoint format: '{endpoint}'",
                        remediation="Use format 'node_name:interface_name'",
                    )
                )
                continue

            node_name = endpoint.split(":")[0]
            if node_name not in nodes:
                self.errors.append(
                    ValidationError(
                        component=f"link:{idx}",
                        message=f"Link references undefined node: '{node_name}'",
                        remediation=f"Define node '{node_name}' or fix link endpoint",
                    )
                )

    def _check_circular_dependencies(self):
        """Check for circular dependencies in links"""
        links = self.topology["topology"].get("links", [])

        # Build adjacency graph
        graph: dict[str, set[str]] = {}
        for link in links:
            if "endpoints" not in link or len(link["endpoints"]) != 2:
                continue

            node1 = link["endpoints"][0].split(":")[0]
            node2 = link["endpoints"][1].split(":")[0]

            if node1 not in graph:
                graph[node1] = set()
            if node2 not in graph:
                graph[node2] = set()

            graph[node1].add(node2)
            graph[node2].add(node1)

        # Check for self-loops
        for node, neighbors in graph.items():
            if node in neighbors:
                self.errors.append(
                    ValidationError(
                        component="link_validator",
                        message=f"Self-loop detected: node '{node}' links to itself",
                        remediation=f"Remove self-referencing link for node '{node}'",
                    )
                )

    def print_results(self):
        """Print validation results"""
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print("\n❌ Validation Errors:")
            for error in self.errors:
                print(f"\n  Component: {error.component}")
                print(f"  Error: {error.message}")
                if error.remediation:
                    print(f"  Fix: {error.remediation}")
            return False
        else:
            print("\n✅ Topology validation passed!")
            return True


def main():
    parser = argparse.ArgumentParser(description="Validate ContainerLab topology definition")
    parser.add_argument("topology_file", help="Path to topology YAML file")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress output, only return exit code"
    )

    args = parser.parse_args()

    validator = TopologyValidator(args.topology_file)
    is_valid = validator.validate()

    if not args.quiet:
        validator.print_results()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
