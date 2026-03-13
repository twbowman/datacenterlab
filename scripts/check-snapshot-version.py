#!/usr/bin/env python3
"""
Check version compatibility of state snapshots.

This script validates snapshot version information and checks compatibility
with the current lab version.
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from version import (
    validate_snapshot_version,
    check_snapshot_compatibility,
    VersionCompatibility,
    LAB_VERSION
)


def load_snapshot(filepath: str) -> Dict:
    """Load snapshot from YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def check_snapshot(filepath: str, verbose: bool = False) -> bool:
    """
    Check snapshot version compatibility.
    
    Args:
        filepath: Path to snapshot file
        verbose: Print detailed information
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        snapshot = load_snapshot(filepath)
    except Exception as e:
        print(f"✗ Error loading snapshot: {e}")
        return False
    
    # Validate version information
    is_valid, message = validate_snapshot_version(snapshot)
    
    if not is_valid:
        print(f"✗ {filepath}: {message}")
        return False
    
    # Check compatibility
    snapshot_version = snapshot.get('version', 'unknown')
    result = check_snapshot_compatibility(snapshot_version)
    
    # Print results
    status_symbols = {
        VersionCompatibility.COMPATIBLE: "✓",
        VersionCompatibility.UPGRADABLE: "⚠",
        VersionCompatibility.INCOMPATIBLE: "✗",
        VersionCompatibility.UNKNOWN: "?",
    }
    
    symbol = status_symbols.get(result.status, "?")
    print(f"{symbol} {filepath}: {result.message}")
    
    if verbose:
        print(f"  Snapshot version: {result.current_version}")
        print(f"  Required version: {result.required_version}")
        print(f"  Lab version: {LAB_VERSION}")
        
        if 'lab_version' in snapshot:
            print(f"  Created with lab version: {snapshot['lab_version']}")
        
        if result.upgrade_available:
            print(f"  Upgrade path: {' → '.join(result.upgrade_path)}")
        
        if 'metadata' in snapshot:
            metadata = snapshot['metadata']
            if 'created_with_version' in metadata:
                print(f"  Created with: {metadata['created_with_version']}")
            if 'description' in metadata:
                print(f"  Description: {metadata['description']}")
    
    # Return success if compatible or upgradable
    return result.status in [VersionCompatibility.COMPATIBLE, VersionCompatibility.UPGRADABLE]


def main():
    parser = argparse.ArgumentParser(
        description="Check version compatibility of state snapshots"
    )
    parser.add_argument(
        'snapshots',
        nargs='+',
        help='Snapshot file(s) to check'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed information'
    )
    parser.add_argument(
        '--fail-on-upgrade',
        action='store_true',
        help='Exit with error if snapshot needs upgrade'
    )
    
    args = parser.parse_args()
    
    print(f"Checking snapshot compatibility with lab version {LAB_VERSION}")
    print()
    
    all_compatible = True
    needs_upgrade = False
    
    for snapshot_path in args.snapshots:
        if not Path(snapshot_path).exists():
            print(f"✗ {snapshot_path}: File not found")
            all_compatible = False
            continue
        
        is_compatible = check_snapshot(snapshot_path, args.verbose)
        
        if not is_compatible:
            all_compatible = False
        
        # Check if upgrade is needed
        try:
            snapshot = load_snapshot(snapshot_path)
            result = check_snapshot_compatibility(snapshot.get('version', 'unknown'))
            if result.status == VersionCompatibility.UPGRADABLE:
                needs_upgrade = True
        except:
            pass
        
        if args.verbose and len(args.snapshots) > 1:
            print()
    
    # Print summary
    if len(args.snapshots) > 1:
        print()
        print("Summary:")
        if all_compatible:
            print("✓ All snapshots are compatible")
        else:
            print("✗ Some snapshots are incompatible")
        
        if needs_upgrade:
            print("⚠ Some snapshots can be upgraded")
    
    # Exit code
    if not all_compatible:
        sys.exit(1)
    
    if args.fail_on_upgrade and needs_upgrade:
        sys.exit(2)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
