#!/usr/bin/env python3
"""
Migrate state snapshots between format versions.

This script converts snapshots from one format version to another,
handling schema changes and data transformations.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from version import LAB_VERSION, parse_version, validate_snapshot_version


def migrate_1_0_to_2_0(snapshot: dict) -> dict:
    """
    Migrate snapshot from format 1.0 to 2.0.

    Changes in 2.0:
    - Add lab_version field
    - Enhance metadata structure
    - Standardize device configuration format

    Args:
        snapshot: Snapshot in 1.0 format

    Returns:
        Snapshot in 2.0 format
    """
    migrated = snapshot.copy()

    # Update version
    migrated["version"] = "2.0"

    # Add lab_version if not present
    if "lab_version" not in migrated:
        migrated["lab_version"] = LAB_VERSION

    # Enhance metadata
    if "metadata" not in migrated:
        migrated["metadata"] = {}

    metadata = migrated["metadata"]

    # Add migration information
    metadata["migrated_from"] = "1.0"
    metadata["migrated_at"] = datetime.utcnow().isoformat() + "Z"
    metadata["migrated_by"] = "migrate-snapshots.py"

    # Add component versions if not present
    if "component_versions" not in metadata:
        metadata["component_versions"] = {
            "state_snapshot_format": "2.0",
            "gnmic_config_format": "1.0",
            "ansible_inventory_format": "1.0",
        }

    # Preserve original creation info
    if "created_with_version" not in metadata and "lab_version" in snapshot:
        metadata["original_lab_version"] = snapshot["lab_version"]

    return migrated


def migrate_snapshot(snapshot: dict, from_version: str, to_version: str) -> dict:
    """
    Migrate snapshot from one version to another.

    Args:
        snapshot: Original snapshot
        from_version: Source version
        to_version: Target version

    Returns:
        Migrated snapshot

    Raises:
        ValueError: If migration path is not supported
    """
    from_parsed = parse_version(from_version)
    to_parsed = parse_version(to_version)

    # Check if migration is needed
    if from_parsed == to_parsed:
        return snapshot

    # Check if migration is supported
    if from_parsed > to_parsed:
        raise ValueError(f"Cannot downgrade from {from_version} to {to_version}")

    # Perform migration
    migrated = snapshot.copy()

    # 1.0 -> 2.0
    if from_parsed == (1, 0, 0) and to_parsed == (2, 0, 0):
        migrated = migrate_1_0_to_2_0(migrated)
    else:
        raise ValueError(f"Migration from {from_version} to {to_version} is not implemented")

    return migrated


def load_snapshot(filepath: str) -> dict:
    """Load snapshot from YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def save_snapshot(snapshot: dict, filepath: str):
    """Save snapshot to YAML file."""
    with open(filepath, "w") as f:
        yaml.dump(snapshot, f, default_flow_style=False, sort_keys=False, indent=2)


def migrate_file(
    input_path: str,
    output_path: str,
    from_version: str,
    to_version: str,
    validate: bool = True,
    dry_run: bool = False,
) -> bool:
    """
    Migrate a snapshot file.

    Args:
        input_path: Input snapshot file
        output_path: Output snapshot file
        from_version: Source version
        to_version: Target version
        validate: Validate snapshot before and after migration
        dry_run: Don't write output file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load snapshot
        print(f"Loading {input_path}...")
        snapshot = load_snapshot(input_path)

        # Validate input
        if validate:
            is_valid, message = validate_snapshot_version(snapshot)
            if not is_valid:
                print(f"✗ Input validation failed: {message}")
                return False
            print("✓ Input snapshot is valid")

        # Check version
        current_version = snapshot.get("version", "unknown")
        if current_version != from_version:
            print(f"⚠ Warning: Snapshot version is {current_version}, expected {from_version}")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != "y":
                return False

        # Migrate
        print(f"Migrating from {from_version} to {to_version}...")
        migrated = migrate_snapshot(snapshot, from_version, to_version)

        # Validate output
        if validate:
            is_valid, message = validate_snapshot_version(migrated)
            if not is_valid:
                print(f"✗ Output validation failed: {message}")
                return False
            print("✓ Migrated snapshot is valid")

        # Save
        if not dry_run:
            print(f"Writing {output_path}...")
            save_snapshot(migrated, output_path)
            print("✓ Migration complete")
        else:
            print("✓ Dry run complete (no file written)")

        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate state snapshots between format versions")
    parser.add_argument(
        "--from", dest="from_version", required=True, help="Source version (e.g., 1.0)"
    )
    parser.add_argument("--to", dest="to_version", required=True, help="Target version (e.g., 2.0)")
    parser.add_argument("--input", required=True, help="Input snapshot file or directory")
    parser.add_argument(
        "--output", help="Output snapshot file or directory (default: <input>-migrated)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate snapshots before and after migration (default: True)",
    )
    parser.add_argument(
        "--no-validate", action="store_false", dest="validate", help="Skip validation"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform migration without writing output files"
    )

    args = parser.parse_args()

    # Normalize version strings
    from_version = args.from_version
    to_version = args.to_version

    # Add .0 if needed for patch version (to support both X.Y and X.Y.Z formats)
    # The parse_version function will handle both formats

    # Validate version format
    try:
        parse_version(from_version)
        parse_version(to_version)
    except ValueError as e:
        print(f"✗ Invalid version format: {e}")
        sys.exit(1)

    # Determine input/output paths
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"✗ Input path does not exist: {input_path}")
        sys.exit(1)

    # Handle directory vs file
    if input_path.is_dir():
        # Migrate all YAML files in directory
        output_dir = (
            Path(args.output) if args.output else input_path.parent / f"{input_path.name}-migrated"
        )

        if not args.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Migrating snapshots from {input_path} to {output_dir}")
        print()

        yaml_files = list(input_path.glob("*.yml")) + list(input_path.glob("*.yaml"))

        if not yaml_files:
            print(f"✗ No YAML files found in {input_path}")
            sys.exit(1)

        success_count = 0
        fail_count = 0

        for yaml_file in yaml_files:
            output_file = output_dir / yaml_file.name
            print(f"Processing {yaml_file.name}...")

            if migrate_file(
                str(yaml_file),
                str(output_file),
                from_version,
                to_version,
                args.validate,
                args.dry_run,
            ):
                success_count += 1
            else:
                fail_count += 1

            print()

        # Summary
        print("Summary:")
        print(f"  ✓ Successful: {success_count}")
        print(f"  ✗ Failed: {fail_count}")

        sys.exit(0 if fail_count == 0 else 1)

    else:
        # Migrate single file
        output_path = (
            args.output
            if args.output
            else str(input_path.parent / f"{input_path.stem}-migrated{input_path.suffix}")
        )

        success = migrate_file(
            str(input_path), output_path, from_version, to_version, args.validate, args.dry_run
        )

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
