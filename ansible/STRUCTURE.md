# Ansible Project Structure

Clean, role-based structure following Ansible best practices.

## Current Structure

```
ansible/
├── site.yml                    # ⭐ Main playbook - use this!
├── inventory.yml               # Device inventory
├── ansible.cfg                 # Configuration
│
├── playbooks/                  # Component playbooks (optional)
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml
│   ├── configure-lldp.yml
│   └── verify.yml
│
├── roles/                      # Reusable roles
│   ├── openconfig_interfaces/
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   ├── openconfig_bgp/
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   └── openconfig_lldp/
│       ├── tasks/main.yml
│       ├── defaults/main.yml
│       └── meta/main.yml
│
├── archive/                    # Old playbooks (deprecated)
│   └── *.yml
│
└── docs/                       # Documentation
    ├── README.md               # Main documentation
    ├── ROLES-README.md         # Role details
    ├── QUICK-START.md          # Quick reference
    └── OPENCONFIG-MIGRATION.md # Migration notes
```

## File Count

**Active files:**
- 1 main playbook (`site.yml`)
- 4 component playbooks (in `playbooks/`)
- 3 roles (in `roles/`)
- 1 inventory file
- 1 config file

**Total: 10 active files** (down from 20+ old playbooks)

## What to Use

### For Most Cases
```bash
ansible-playbook site.yml
```

### For Specific Components
```bash
ansible-playbook playbooks/configure-bgp.yml
ansible-playbook playbooks/verify.yml
```

### With Tags
```bash
ansible-playbook site.yml --tags bgp
ansible-playbook site.yml --tags lldp
```

## What Was Removed

Moved to `archive/`:
- `configure-gnmi.yml`
- `configure-grpc-insecure.yml`
- `configure-telemetry.yml`
- `verify-all.yml`
- `verify-bgp-detailed.yml`
- `verify-connectivity.yml`
- `verify-lldp.yml`
- `verify-routing.yml`
- `verify-simple.yml`
- Old `configure-*.yml` files

These are kept for reference but should not be used.

## Benefits of Clean Structure

1. **Simplicity**: One main playbook for most use cases
2. **Clarity**: Clear separation of roles and playbooks
3. **Maintainability**: Easy to find and update code
4. **Reusability**: Roles can be shared and reused
5. **Standards**: Follows Ansible Galaxy conventions
6. **Scalability**: Easy to add new roles

## Adding New Functionality

### Add a New Role
```bash
mkdir -p ansible/roles/openconfig_ospf/{tasks,defaults,meta}
# Create tasks/main.yml, defaults/main.yml, meta/main.yml
```

### Add to site.yml
```yaml
roles:
  - role: openconfig_interfaces
  - role: openconfig_bgp
  - role: openconfig_lldp
  - role: openconfig_ospf  # New role
```

### Create Optional Playbook
```bash
cat > ansible/playbooks/configure-ospf.yml <<EOF
---
- name: Configure OSPF protocol
  hosts: all
  gather_facts: no
  roles:
    - role: openconfig_ospf
      tags: ['ospf', 'routing', 'config']
EOF
```

## Comparison

### Before (20+ files)
```
ansible/
├── configure-interfaces.yml
├── configure-interfaces-openconfig.yml
├── configure-bgp.yml
├── configure-lldp.yml
├── configure-lldp-openconfig.yml
├── configure-gnmi.yml
├── configure-grpc-insecure.yml
├── configure-telemetry.yml
├── deploy-config.yml
├── verify-all.yml
├── verify-bgp-detailed.yml
├── verify-connectivity.yml
├── verify-lldp.yml
├── verify-lldp-openconfig.yml
├── verify-routing.yml
├── verify-simple.yml
└── ... (more files)
```

### After (10 files)
```
ansible/
├── site.yml                    # Main playbook
├── playbooks/                  # 4 component playbooks
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml
│   ├── configure-lldp.yml
│   └── verify.yml
└── roles/                      # 3 roles
    ├── openconfig_interfaces/
    ├── openconfig_bgp/
    └── openconfig_lldp/
```

## Migration Path

If you're used to the old structure:

| Old Command | New Command |
|-------------|-------------|
| `ansible-playbook configure-interfaces.yml` | `ansible-playbook site.yml --tags interfaces` |
| `ansible-playbook configure-bgp.yml` | `ansible-playbook site.yml --tags bgp` |
| `ansible-playbook configure-lldp.yml` | `ansible-playbook site.yml --tags lldp` |
| `ansible-playbook deploy-config.yml` | `ansible-playbook site.yml` |
| `ansible-playbook verify-all.yml` | `ansible-playbook playbooks/verify.yml` |

## Next Steps

1. Review the new structure
2. Test with: `ansible-playbook site.yml --check`
3. Deploy: `ansible-playbook site.yml`
4. Verify: `ansible-playbook playbooks/verify.yml`
5. Remove archive directory when comfortable
