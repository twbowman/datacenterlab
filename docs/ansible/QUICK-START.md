# Quick Start Guide - Role-Based Ansible

## TL;DR

```bash
# Deploy everything
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Or from within the VM
orb -m clab
cd ansible
ansible-playbook site.yml
```

## What Changed?

We've migrated from flat playbooks to a role-based structure following Ansible best practices.

### Old Way (Deprecated)
```bash
ansible-playbook configure-interfaces.yml
ansible-playbook configure-bgp.yml
ansible-playbook configure-lldp.yml
```

### New Way (Recommended)
```bash
# Deploy everything at once
ansible-playbook site.yml

# Or individual components
ansible-playbook playbooks/configure-interfaces.yml
ansible-playbook playbooks/configure-bgp.yml
ansible-playbook playbooks/configure-lldp.yml
```

## Directory Structure

```
ansible/
├── site.yml                          # Main playbook (use this!)
├── playbooks/                        # Individual playbooks
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml
│   └── configure-lldp.yml
├── roles/                            # Reusable roles
│   ├── openconfig_interfaces/
│   ├── openconfig_bgp/
│   └── openconfig_lldp/
└── inventory.yml                     # Device inventory
```

## Common Commands

### Deploy Complete Configuration
```bash
ansible-playbook site.yml
```

### Deploy to Specific Hosts
```bash
# Only spine switches
ansible-playbook site.yml --limit spines

# Only leaf switches
ansible-playbook site.yml --limit leafs

# Single device
ansible-playbook site.yml --limit leaf1
```

### Deploy Individual Components
```bash
# Just interfaces
ansible-playbook playbooks/configure-interfaces.yml

# Just BGP
ansible-playbook playbooks/configure-bgp.yml

# Just LLDP
ansible-playbook playbooks/configure-lldp.yml
```

### Debug Mode
```bash
# Enable debug output
ansible-playbook site.yml -e "openconfig_interfaces_debug=true openconfig_bgp_debug=true openconfig_lldp_debug=true"

# Verbose output
ansible-playbook site.yml -vvv
```

### Dry Run
```bash
# Check what would change without applying
ansible-playbook site.yml --check
```

## Benefits of Role-Based Structure

1. **Reusable**: Roles can be used in multiple playbooks
2. **Modular**: Each role does one thing well
3. **Testable**: Test roles independently
4. **Shareable**: Publish roles to Ansible Galaxy
5. **Maintainable**: Easier to update and debug
6. **Standard**: Follows Ansible best practices

## Need Help?

- Full documentation: [ROLES-README.md](ROLES-README.md)
- OpenConfig migration: [OPENCONFIG-MIGRATION.md](OPENCONFIG-MIGRATION.md)
- General info: [README.md](README.md)
