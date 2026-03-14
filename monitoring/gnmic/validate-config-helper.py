#!/usr/bin/env python3
"""
Helper script for validating gNMIc configuration
Used by validate-transformation-rules.sh
"""

import sys

import yaml


def main():
    if len(sys.argv) < 3:
        print("Usage: validate-config-helper.py <config_file> <command> [args...]", file=sys.stderr)
        sys.exit(1)

    config_file = sys.argv[1]
    command = sys.argv[2]

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    if command == "check_processors":
        # Check if processors section exists
        if "processors" in config and config["processors"]:
            print("true")
        else:
            print("false")

    elif command == "check_processor":
        # Check if specific processor exists
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""
        if "processors" in config and processor_name in config["processors"]:
            print("true")
        else:
            print("false")

    elif command == "count_transforms":
        # Count event-convert transformations in a processor
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""
        if "processors" not in config or processor_name not in config["processors"]:
            print("0")
            sys.exit(0)

        processor = config["processors"][processor_name]
        if "event-processors" not in processor:
            print("0")
            sys.exit(0)

        count = 0
        for ep in processor["event-processors"]:
            if "event-convert" in ep and "value-names" in ep["event-convert"]:
                count += 1
        print(count)

    elif command == "check_vendor_tag":
        # Check if vendor tag exists
        vendor = sys.argv[3] if len(sys.argv) > 3 else ""
        if "processors" not in config or "add_vendor_tags" not in config["processors"]:
            print("false")
            sys.exit(0)

        processor = config["processors"]["add_vendor_tags"]
        if "event-processors" not in processor:
            print("false")
            sys.exit(0)

        for ep in processor["event-processors"]:
            if "event-add-tag" in ep:
                tag = ep["event-add-tag"]
                if "value" in tag and tag["value"] == vendor:
                    print("true")
                    sys.exit(0)
        print("false")

    elif command == "check_pattern":
        # Check if a specific regex pattern exists
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""
        pattern = sys.argv[4] if len(sys.argv) > 4 else ""

        if "processors" not in config or processor_name not in config["processors"]:
            print("false")
            sys.exit(0)

        processor = config["processors"][processor_name]
        if "event-processors" not in processor:
            print("false")
            sys.exit(0)

        for ep in processor["event-processors"]:
            if "event-convert" in ep:
                ec = ep["event-convert"]
                if "transforms" in ec:
                    for transform in ec["transforms"]:
                        if (
                            "replace" in transform
                            and "old" in transform["replace"]
                            and transform["replace"]["old"] == pattern
                        ):
                            print("true")
                            sys.exit(0)
        print("false")

    elif command == "check_metric_transform":
        # Check if a specific metric transformation exists
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""
        new_name = sys.argv[4] if len(sys.argv) > 4 else ""

        if "processors" not in config or processor_name not in config["processors"]:
            print("false")
            sys.exit(0)

        processor = config["processors"][processor_name]
        if "event-processors" not in processor:
            print("false")
            sys.exit(0)

        for ep in processor["event-processors"]:
            if "event-convert" in ep:
                ec = ep["event-convert"]
                if "transforms" in ec:
                    for transform in ec["transforms"]:
                        if (
                            "replace" in transform
                            and "new" in transform["replace"]
                            and transform["replace"]["new"] == new_name
                        ):
                            print("true")
                            sys.exit(0)
        print("false")

    elif command == "check_output_processor":
        # Check if processor is applied to output
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""

        if "outputs" not in config or "prom" not in config["outputs"]:
            print("false")
            sys.exit(0)

        output = config["outputs"]["prom"]
        if "event-processors" not in output:
            print("false")
            sys.exit(0)

        if processor_name in output["event-processors"]:
            print("true")
        else:
            print("false")

    elif command == "check_vendor_path":
        # Check if vendor-specific path exists in transformations
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""
        path_pattern = sys.argv[4] if len(sys.argv) > 4 else ""

        if "processors" not in config or processor_name not in config["processors"]:
            print("false")
            sys.exit(0)

        processor = config["processors"][processor_name]
        if "event-processors" not in processor:
            print("false")
            sys.exit(0)

        for ep in processor["event-processors"]:
            if "event-convert" in ep and "value-names" in ep["event-convert"]:
                for value_name in ep["event-convert"]["value-names"]:
                    if path_pattern in value_name:
                        print("true")
                        sys.exit(0)
        print("false")

    elif command == "list_value_names":
        # List all value-names from a processor
        processor_name = sys.argv[3] if len(sys.argv) > 3 else ""

        if "processors" not in config or processor_name not in config["processors"]:
            sys.exit(0)

        processor = config["processors"][processor_name]
        if "event-processors" not in processor:
            sys.exit(0)

        value_names = []
        for ep in processor["event-processors"]:
            if "event-convert" in ep and "value-names" in ep["event-convert"]:
                value_names.extend(ep["event-convert"]["value-names"])

        for vn in value_names:
            print(vn)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
