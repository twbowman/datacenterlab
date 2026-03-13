#!/usr/bin/env python3
"""
Version tracking and compatibility management for the Production Network Testing Lab.

This module provides version information, compatibility checking, and upgrade procedures
for lab state snapshots, configurations, and components.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# Current lab version (semantic versioning)
LAB_VERSION = "0.9.0"

# Component versions
COMPONENT_VERSIONS = {
    "state_snapshot_format": "1.0",
    "gnmic_config_format": "1.0",
    "ansible_inventory_format": "1.0",
    "api_version": "1.0",
}

# Minimum required versions for external dependencies
MINIMUM_DEPENDENCIES = {
    "python": "3.9.0",
    "containerlab": "0.48.0",
    "ansible": "2.14.0",
    "gnmic": "0.31.0",
}


class VersionCompatibility(Enum):
    """Version compatibility status"""
    COMPATIBLE = "compatible"
    UPGRADABLE = "upgradable"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class VersionInfo:
    """Version information for a component"""
    component: str
    version: str
    lab_version: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class CompatibilityResult:
    """Result of version compatibility check"""
    status: VersionCompatibility
    current_version: str
    required_version: str
    message: str
    upgrade_available: bool = False
    upgrade_path: Optional[List[str]] = None


def parse_version(version_string: str) -> Tuple[int, int, int]:
    """
    Parse semantic version string into tuple of (major, minor, patch).
    
    Supports both X.Y.Z and X.Y formats (X.Y is treated as X.Y.0).
    
    Args:
        version_string: Version string in format "X.Y.Z" or "X.Y"
        
    Returns:
        Tuple of (major, minor, patch) as integers
        
    Raises:
        ValueError: If version string is invalid
    """
    # Support both X.Y.Z and X.Y formats
    pattern_full = r'^(\d+)\.(\d+)\.(\d+)$'
    pattern_short = r'^(\d+)\.(\d+)$'
    
    match = re.match(pattern_full, version_string)
    if match:
        major, minor, patch = match.groups()
        return (int(major), int(minor), int(patch))
    
    match = re.match(pattern_short, version_string)
    if match:
        major, minor = match.groups()
        return (int(major), int(minor), 0)
    
    raise ValueError(f"Invalid version string: {version_string}")


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def is_compatible(current_version: str, required_version: str) -> bool:
    """
    Check if current version is compatible with required version.
    
    Compatibility rules (semantic versioning):
    - Major version must match
    - Minor version must be >= required
    - Patch version is ignored for compatibility
    
    Args:
        current_version: Current version string
        required_version: Required version string
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        current = parse_version(current_version)
        required = parse_version(required_version)
        
        # Major version must match
        if current[0] != required[0]:
            return False
        
        # Minor version must be >= required
        if current[1] < required[1]:
            return False
        
        return True
    except ValueError:
        return False


def check_snapshot_compatibility(snapshot_version: str) -> CompatibilityResult:
    """
    Check if a state snapshot version is compatible with current lab version.
    
    Args:
        snapshot_version: Version string from state snapshot
        
    Returns:
        CompatibilityResult with status and details
    """
    current = COMPONENT_VERSIONS["state_snapshot_format"]
    
    if snapshot_version == current:
        return CompatibilityResult(
            status=VersionCompatibility.COMPATIBLE,
            current_version=snapshot_version,
            required_version=current,
            message=f"Snapshot version {snapshot_version} is fully compatible"
        )
    
    if is_compatible(snapshot_version, current):
        return CompatibilityResult(
            status=VersionCompatibility.COMPATIBLE,
            current_version=snapshot_version,
            required_version=current,
            message=f"Snapshot version {snapshot_version} is compatible (current: {current})"
        )
    
    # Check if upgrade is possible
    try:
        snapshot_parsed = parse_version(snapshot_version)
        current_parsed = parse_version(current)
        
        # If snapshot is newer than current, it's forward compatible (for migration testing)
        if snapshot_parsed > current_parsed:
            return CompatibilityResult(
                status=VersionCompatibility.COMPATIBLE,
                current_version=snapshot_version,
                required_version=current,
                message=f"Snapshot version {snapshot_version} is newer than current {current} (forward compatible)"
            )
        
        # Can upgrade if major version is same or one behind
        if snapshot_parsed[0] == current_parsed[0] or snapshot_parsed[0] == current_parsed[0] - 1:
            upgrade_path = get_upgrade_path(snapshot_version, current)
            return CompatibilityResult(
                status=VersionCompatibility.UPGRADABLE,
                current_version=snapshot_version,
                required_version=current,
                message=f"Snapshot version {snapshot_version} can be upgraded to {current}",
                upgrade_available=True,
                upgrade_path=upgrade_path
            )
    except ValueError:
        pass
    
    return CompatibilityResult(
        status=VersionCompatibility.INCOMPATIBLE,
        current_version=snapshot_version,
        required_version=current,
        message=f"Snapshot version {snapshot_version} is incompatible with current version {current}"
    )


def get_upgrade_path(from_version: str, to_version: str) -> List[str]:
    """
    Get the upgrade path from one version to another.
    
    Args:
        from_version: Starting version
        to_version: Target version
        
    Returns:
        List of intermediate versions to upgrade through
    """
    # For now, direct upgrade is supported
    # In future, this could return intermediate versions
    return [to_version]


def check_dependency_versions() -> Dict[str, CompatibilityResult]:
    """
    Check versions of external dependencies.
    
    Returns:
        Dictionary mapping dependency name to CompatibilityResult
    """
    results = {}
    
    # Check Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    required_python = MINIMUM_DEPENDENCIES["python"]
    
    if compare_versions(python_version, required_python) >= 0:
        results["python"] = CompatibilityResult(
            status=VersionCompatibility.COMPATIBLE,
            current_version=python_version,
            required_version=required_python,
            message=f"Python {python_version} meets minimum requirement {required_python}"
        )
    else:
        results["python"] = CompatibilityResult(
            status=VersionCompatibility.INCOMPATIBLE,
            current_version=python_version,
            required_version=required_python,
            message=f"Python {python_version} is below minimum requirement {required_python}"
        )
    
    # Check other dependencies (would need to be implemented)
    # For now, mark as unknown
    for dep in ["containerlab", "ansible", "gnmic"]:
        results[dep] = CompatibilityResult(
            status=VersionCompatibility.UNKNOWN,
            current_version="unknown",
            required_version=MINIMUM_DEPENDENCIES[dep],
            message=f"Version check not implemented for {dep}"
        )
    
    return results


def get_version_info() -> Dict[str, str]:
    """
    Get version information for all components.
    
    Returns:
        Dictionary with version information
    """
    return {
        "lab_version": LAB_VERSION,
        **COMPONENT_VERSIONS,
        "minimum_dependencies": MINIMUM_DEPENDENCIES,
    }


def format_version_info() -> str:
    """
    Format version information as human-readable string.
    
    Returns:
        Formatted version information
    """
    info = get_version_info()
    
    output = [
        f"Production Network Testing Lab v{info['lab_version']}",
        "",
        "Component Versions:",
        f"  State Snapshot Format: {info['state_snapshot_format']}",
        f"  gNMIc Config Format: {info['gnmic_config_format']}",
        f"  Ansible Inventory Format: {info['ansible_inventory_format']}",
        f"  API Version: {info['api_version']}",
        "",
        "Minimum Dependencies:",
        f"  Python: {info['minimum_dependencies']['python']}",
        f"  Containerlab: {info['minimum_dependencies']['containerlab']}",
        f"  Ansible: {info['minimum_dependencies']['ansible']}",
        f"  gNMIc: {info['minimum_dependencies']['gnmic']}",
    ]
    
    return "\n".join(output)


def validate_snapshot_version(snapshot: Dict) -> Tuple[bool, str]:
    """
    Validate that a snapshot has proper version information.
    
    Args:
        snapshot: State snapshot dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if "version" not in snapshot:
        return False, "Snapshot missing 'version' field"
    
    version = snapshot["version"]
    
    # Validate version format
    try:
        parse_version(version)
    except ValueError:
        return False, f"Invalid version format: {version}"
    
    # Check compatibility
    result = check_snapshot_compatibility(version)
    
    if result.status == VersionCompatibility.INCOMPATIBLE:
        return False, result.message
    
    if result.status == VersionCompatibility.UPGRADABLE:
        return True, f"Warning: {result.message}"
    
    return True, "Snapshot version is valid and compatible"


def add_version_to_snapshot(snapshot: Dict) -> Dict:
    """
    Add version information to a state snapshot.
    
    Args:
        snapshot: State snapshot dictionary
        
    Returns:
        Snapshot with version information added
    """
    snapshot["version"] = COMPONENT_VERSIONS["state_snapshot_format"]
    snapshot["lab_version"] = LAB_VERSION
    
    if "metadata" not in snapshot:
        snapshot["metadata"] = {}
    
    snapshot["metadata"]["created_with_version"] = LAB_VERSION
    snapshot["metadata"]["component_versions"] = COMPONENT_VERSIONS.copy()
    
    return snapshot


if __name__ == "__main__":
    # Print version information when run directly
    print(format_version_info())
    print()
    
    # Check dependencies
    print("Dependency Check:")
    deps = check_dependency_versions()
    for dep, result in deps.items():
        status_symbol = {
            VersionCompatibility.COMPATIBLE: "✓",
            VersionCompatibility.INCOMPATIBLE: "✗",
            VersionCompatibility.UNKNOWN: "?",
        }.get(result.status, "?")
        
        print(f"  {status_symbol} {dep}: {result.message}")
