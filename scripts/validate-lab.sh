#!/bin/bash
# Comprehensive lab validation script
# Runs config validation (Ansible), telemetry validation, and normalization validation
# Merges results into a single validation-report.json
#
# Requirements: 7.7, 8.7
#
# Usage (from ORB VM context):
#   orb -m clab ./scripts/validate-lab.sh
#   orb -m clab ./scripts/validate-lab.sh --inventory ansible/inventory-dynamic.yml
#   orb -m clab ./scripts/validate-lab.sh --prometheus-url http://localhost:9090
#   orb -m clab ./scripts/validate-lab.sh --expected-devices spine1,spine2,leaf1,leaf2

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Defaults
INVENTORY="ansible/inventory-dynamic.yml"
PROMETHEUS_URL="http://localhost:9090"
EXPECTED_DEVICES="spine1,spine2,leaf1,leaf2,leaf3,leaf4"
REPORT_FILE="validation-report.json"

# Temp directory for intermediate results
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --inventory|-i)
            INVENTORY="$2"
            shift 2
            ;;
        --prometheus-url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        --expected-devices)
            EXPECTED_DEVICES="$2"
            shift 2
            ;;
        --report-file|-o)
            REPORT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --inventory, -i FILE       Ansible inventory file (default: ansible/inventory-dynamic.yml)"
            echo "  --prometheus-url URL        Prometheus URL (default: http://localhost:9090)"
            echo "  --expected-devices DEVICES  Comma-separated device names (default: spine1,spine2,leaf1,leaf2,leaf3,leaf4)"
            echo "  --report-file, -o FILE      Output report file (default: validation-report.json)"
            echo "  --help, -h                  Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Fall back to static inventory if dynamic doesn't exist
if [ ! -f "$INVENTORY" ]; then
    if [ -f "ansible/inventory.yml" ]; then
        echo -e "${YELLOW}Dynamic inventory not found, using ansible/inventory.yml${NC}"
        INVENTORY="ansible/inventory.yml"
    else
        echo -e "${RED}No inventory file found at $INVENTORY${NC}"
        exit 1
    fi
fi

# Track results
CONFIG_PASSED=0
TELEMETRY_PASSED=0
NORMALIZATION_PASSED=0
CONFIG_RAN=0
TELEMETRY_RAN=0
NORMALIZATION_RAN=0

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Lab Validation - Comprehensive Check             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Inventory:        ${INVENTORY}"
echo -e "  Prometheus URL:   ${PROMETHEUS_URL}"
echo -e "  Expected devices: ${EXPECTED_DEVICES}"
echo -e "  Report file:      ${REPORT_FILE}"
echo ""

# ─────────────────────────────────────────────────────────────
# 1. Configuration Validation (Ansible playbook)
# ─────────────────────────────────────────────────────────────
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[1/3] Configuration Validation (Ansible)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

CONFIG_REPORT="$TMPDIR/config-report.json"

if [ -f "ansible/playbooks/validate.yml" ]; then
    CONFIG_RAN=1
    # The validation_report callback plugin writes validation-report.json
    # We redirect it to our temp location
    if ANSIBLE_CALLBACK_PLUGINS=ansible/callback_plugins \
       ANSIBLE_CALLBACKS_ENABLED=validation_report \
       ansible-playbook -i "$INVENTORY" ansible/playbooks/validate.yml 2>&1; then
        CONFIG_PASSED=1
        echo ""
        echo -e "  ${GREEN}✔ Configuration validation passed${NC}"
    else
        echo ""
        echo -e "  ${RED}✘ Configuration validation failed${NC}"
    fi

    # Move the callback-generated report to temp
    if [ -f "validation-report.json" ] && [ "$REPORT_FILE" != "validation-report.json" ]; then
        cp validation-report.json "$CONFIG_REPORT"
    elif [ -f "validation-report.json" ]; then
        cp validation-report.json "$CONFIG_REPORT"
    fi
else
    echo -e "  ${YELLOW}⚠ ansible/playbooks/validate.yml not found, skipping${NC}"
fi
echo ""

# ─────────────────────────────────────────────────────────────
# 2. Telemetry Validation (Python script)
# ─────────────────────────────────────────────────────────────
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[2/3] Telemetry Validation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TELEMETRY_REPORT="$TMPDIR/telemetry-report.json"

if [ -f "validation/check_telemetry.py" ]; then
    TELEMETRY_RAN=1
    if python3 validation/check_telemetry.py \
        --prometheus-url "$PROMETHEUS_URL" \
        --expected-devices "$EXPECTED_DEVICES" \
        --json > "$TELEMETRY_REPORT" 2>&1; then
        TELEMETRY_PASSED=1
        echo -e "  ${GREEN}✔ Telemetry validation passed${NC}"
    else
        echo -e "  ${RED}✘ Telemetry validation failed${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ validation/check_telemetry.py not found, skipping${NC}"
fi
echo ""

# ─────────────────────────────────────────────────────────────
# 3. Normalization Validation (Python script)
# ─────────────────────────────────────────────────────────────
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}[3/3] Normalization Validation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

NORMALIZATION_REPORT="$TMPDIR/normalization-report.json"

if [ -f "validation/check_normalization.py" ]; then
    NORMALIZATION_RAN=1
    if python3 validation/check_normalization.py \
        --prometheus-url "$PROMETHEUS_URL" \
        --json > "$NORMALIZATION_REPORT" 2>&1; then
        NORMALIZATION_PASSED=1
        echo -e "  ${GREEN}✔ Normalization validation passed${NC}"
    else
        echo -e "  ${RED}✘ Normalization validation failed${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ validation/check_normalization.py not found, skipping${NC}"
fi
echo ""

# ─────────────────────────────────────────────────────────────
# Merge results into a single report
# ─────────────────────────────────────────────────────────────
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Generating merged validation report${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Use Python to merge the JSON reports
python3 -c "
import json, sys, os
from datetime import datetime, timezone

report = {
    'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'categories': {},
    'summary': {
        'total_categories': 0,
        'categories_passed': 0,
        'categories_failed': 0,
        'categories_skipped': 0,
    }
}

# Configuration validation
config_report_path = '$CONFIG_REPORT'
if os.path.isfile(config_report_path):
    try:
        with open(config_report_path) as f:
            config_data = json.load(f)
        report['categories']['configuration'] = {
            'status': 'pass' if $CONFIG_PASSED else 'fail',
            'report': config_data,
        }
    except (json.JSONDecodeError, OSError):
        report['categories']['configuration'] = {
            'status': 'fail' if $CONFIG_RAN else 'skipped',
            'report': None,
        }
elif $CONFIG_RAN:
    report['categories']['configuration'] = {
        'status': 'pass' if $CONFIG_PASSED else 'fail',
        'report': None,
    }
else:
    report['categories']['configuration'] = {'status': 'skipped', 'report': None}

# Telemetry validation
telemetry_report_path = '$TELEMETRY_REPORT'
if os.path.isfile(telemetry_report_path):
    try:
        with open(telemetry_report_path) as f:
            content = f.read()
        # The --json output may include human-readable text before the JSON
        # Find the last JSON object in the output
        json_start = content.rfind('{')
        if json_start >= 0:
            telemetry_data = json.loads(content[json_start:])
        else:
            telemetry_data = None
        report['categories']['telemetry'] = {
            'status': 'pass' if $TELEMETRY_PASSED else 'fail',
            'report': telemetry_data,
        }
    except (json.JSONDecodeError, OSError):
        report['categories']['telemetry'] = {
            'status': 'fail' if $TELEMETRY_RAN else 'skipped',
            'report': None,
        }
elif $TELEMETRY_RAN:
    report['categories']['telemetry'] = {
        'status': 'pass' if $TELEMETRY_PASSED else 'fail',
        'report': None,
    }
else:
    report['categories']['telemetry'] = {'status': 'skipped', 'report': None}

# Normalization validation
norm_report_path = '$NORMALIZATION_REPORT'
if os.path.isfile(norm_report_path):
    try:
        with open(norm_report_path) as f:
            content = f.read()
        json_start = content.rfind('{')
        if json_start >= 0:
            norm_data = json.loads(content[json_start:])
        else:
            norm_data = None
        report['categories']['normalization'] = {
            'status': 'pass' if $NORMALIZATION_PASSED else 'fail',
            'report': norm_data,
        }
    except (json.JSONDecodeError, OSError):
        report['categories']['normalization'] = {
            'status': 'fail' if $NORMALIZATION_RAN else 'skipped',
            'report': None,
        }
elif $NORMALIZATION_RAN:
    report['categories']['normalization'] = {
        'status': 'pass' if $NORMALIZATION_PASSED else 'fail',
        'report': None,
    }
else:
    report['categories']['normalization'] = {'status': 'skipped', 'report': None}

# Compute summary
for cat_name, cat_data in report['categories'].items():
    report['summary']['total_categories'] += 1
    if cat_data['status'] == 'pass':
        report['summary']['categories_passed'] += 1
    elif cat_data['status'] == 'fail':
        report['summary']['categories_failed'] += 1
    else:
        report['summary']['categories_skipped'] += 1

with open('$REPORT_FILE', 'w') as f:
    json.dump(report, f, indent=2, default=str)
"

echo -e "  Report written to: ${REPORT_FILE}"
echo ""

# ─────────────────────────────────────────────────────────────
# Final Summary
# ─────────────────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Validation Summary                       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

TOTAL_RAN=$((CONFIG_RAN + TELEMETRY_RAN + NORMALIZATION_RAN))
TOTAL_PASSED=$((CONFIG_PASSED + TELEMETRY_PASSED + NORMALIZATION_PASSED))
TOTAL_FAILED=$((TOTAL_RAN - TOTAL_PASSED))

# Configuration
if [ "$CONFIG_RAN" -eq 1 ]; then
    if [ "$CONFIG_PASSED" -eq 1 ]; then
        echo -e "  ${GREEN}✔ Configuration Validation  PASSED${NC}"
    else
        echo -e "  ${RED}✘ Configuration Validation  FAILED${NC}"
    fi
else
    echo -e "  ${YELLOW}⊘ Configuration Validation  SKIPPED${NC}"
fi

# Telemetry
if [ "$TELEMETRY_RAN" -eq 1 ]; then
    if [ "$TELEMETRY_PASSED" -eq 1 ]; then
        echo -e "  ${GREEN}✔ Telemetry Validation      PASSED${NC}"
    else
        echo -e "  ${RED}✘ Telemetry Validation      FAILED${NC}"
    fi
else
    echo -e "  ${YELLOW}⊘ Telemetry Validation      SKIPPED${NC}"
fi

# Normalization
if [ "$NORMALIZATION_RAN" -eq 1 ]; then
    if [ "$NORMALIZATION_PASSED" -eq 1 ]; then
        echo -e "  ${GREEN}✔ Normalization Validation  PASSED${NC}"
    else
        echo -e "  ${RED}✘ Normalization Validation  FAILED${NC}"
    fi
else
    echo -e "  ${YELLOW}⊘ Normalization Validation  SKIPPED${NC}"
fi

echo ""
echo -e "  Total: ${TOTAL_PASSED}/${TOTAL_RAN} passed"
echo ""

if [ "$TOTAL_FAILED" -gt 0 ]; then
    echo -e "${RED}✘ Validation completed with failures${NC}"
    exit 1
else
    echo -e "${GREEN}✔ All validations passed${NC}"
    exit 0
fi
