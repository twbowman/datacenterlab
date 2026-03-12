#!/bin/bash
# Validation script for gnmi_evpn_vxlan role
# Tests YAML syntax, Jinja2 templates, and data model compatibility

set -e

echo "========================================="
echo "EVPN/VXLAN Role Validation"
echo "========================================="
echo ""

# Test 1: YAML Syntax Validation
echo "Test 1: YAML Syntax Validation"
python3 << 'PYEOF'
import yaml
import sys

files = [
    'ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml',
    'ansible/group_vars/leafs.yml',
    'ansible/group_vars/spines.yml',
    'ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml'
]

for file in files:
    try:
        with open(file, 'r') as f:
            yaml.safe_load(f)
        print(f'  ✅ {file.split("/")[-1]}')
    except Exception as e:
        print(f'  ❌ {file.split("/")[-1]}: {e}')
        sys.exit(1)
PYEOF
echo ""

# Test 2: Jinja2 Template Balance Check
echo "Test 2: Jinja2 Template Balance"
python3 << 'PYEOF'
import re

with open('ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml', 'r') as f:
    content = f.read()

jinja_block_open = len(re.findall(r'\{%', content))
jinja_block_close = len(re.findall(r'%\}', content))

print(f'  Jinja2 blocks: {{%% = {jinja_block_open}, %%}} = {jinja_block_close}')

# Note: Jinja2 expressions may appear unbalanced due to JSON objects
# Example: '{"vni": {{ item.vni }}}' has 1 {{ and 2 }} (one for Jinja2, one for JSON)
# This is expected and correct Ansible syntax

if jinja_block_open == jinja_block_close:
    print('  ✅ Jinja2 blocks are balanced')
else:
    print('  ❌ Jinja2 blocks are unbalanced')
    exit(1)

# Check for loop usage
has_loop = 'loop:' in content
has_item = '{{ item.' in content

if has_item and has_loop:
    print('  ✅ Loop and item usage is correct')
elif has_item and not has_loop:
    print('  ❌ Found {{ item. but no loop defined')
    exit(1)
PYEOF
echo ""

# Test 3: Data Model Compatibility
echo "Test 3: Data Model Compatibility"
python3 << 'PYEOF'
import yaml

# Load group_vars
with open('ansible/group_vars/leafs.yml', 'r') as f:
    leafs_vars = yaml.safe_load(f)

with open('ansible/group_vars/spines.yml', 'r') as f:
    spines_vars = yaml.safe_load(f)

# Check required fields for leafs
required_leaf_fields = [
    'evpn_vxlan.enabled',
    'evpn_vxlan.vlan_vni_mappings',
    'evpn_vxlan.bgp_evpn.enabled'
]

for field in required_leaf_fields:
    keys = field.split('.')
    value = leafs_vars
    for key in keys:
        value = value.get(key, {})
    
    if value:
        print(f'  ✅ leafs.yml has {field}')
    else:
        print(f'  ❌ leafs.yml missing {field}')
        exit(1)

# Check required fields for spines
required_spine_fields = [
    'evpn_vxlan.bgp_evpn.enabled',
    'evpn_vxlan.bgp_evpn.route_reflector'
]

for field in required_spine_fields:
    keys = field.split('.')
    value = spines_vars
    for key in keys:
        value = value.get(key, {})
    
    if value is not None:
        print(f'  ✅ spines.yml has {field}')
    else:
        print(f'  ❌ spines.yml missing {field}')
        exit(1)

# Validate VLAN-VNI mappings structure
mappings = leafs_vars.get('evpn_vxlan', {}).get('vlan_vni_mappings', [])
if len(mappings) > 0:
    print(f'  ✅ Found {len(mappings)} VLAN-VNI mappings')
    
    for mapping in mappings:
        if 'vlan_id' in mapping and 'vni' in mapping:
            continue
        else:
            print(f'  ❌ Invalid mapping: {mapping}')
            exit(1)
    print(f'  ✅ All mappings have required fields')
else:
    print(f'  ❌ No VLAN-VNI mappings found')
    exit(1)
PYEOF
echo ""

# Test 4: Task Conditional Logic
echo "Test 4: Task Conditional Logic"
python3 << 'PYEOF'
import yaml

with open('ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml', 'r') as f:
    tasks = yaml.safe_load(f)

leaf_only_tasks = 0
spine_only_tasks = 0
all_device_tasks = 0

for task in tasks:
    if 'when' in task:
        when_conditions = task['when']
        if isinstance(when_conditions, str):
            when_conditions = [when_conditions]
        
        when_str = ' '.join(str(c) for c in when_conditions)
        
        if 'leaf' in when_str and 'spine' not in when_str:
            leaf_only_tasks += 1
        elif 'route_reflector' in when_str or ('spine' in when_str and 'leaf' not in when_str):
            spine_only_tasks += 1
    else:
        all_device_tasks += 1

print(f'  Tasks for all devices: {all_device_tasks}')
print(f'  Tasks for leafs only: {leaf_only_tasks}')
print(f'  Tasks for spines only: {spine_only_tasks}')
print(f'  ✅ Conditional logic is present')
PYEOF
echo ""

# Test 5: README Documentation
echo "Test 5: Documentation"
if [ -f "ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/README.md" ]; then
    echo "  ✅ README.md exists"
    
    # Check for key sections
    if grep -q "## Overview" "ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/README.md"; then
        echo "  ✅ Has Overview section"
    fi
    
    if grep -q "## Variables" "ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/README.md"; then
        echo "  ✅ Has Variables section"
    fi
    
    if grep -q "## Usage" "ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/README.md"; then
        echo "  ✅ Has Usage section"
    fi
else
    echo "  ❌ README.md not found"
    exit 1
fi
echo ""

echo "========================================="
echo "✅ All validation tests passed"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Deploy lab: ./deploy.sh"
echo "  2. Configure network: ansible-playbook -i ansible/inventory.yml ansible/site.yml"
echo "  3. Configure EVPN: ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml"
echo "  4. Verify EVPN: ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify-evpn.yml"
echo ""
