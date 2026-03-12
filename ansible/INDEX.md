# Ansible Project Index

Quick reference to all documentation and files.

## 📚 Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | Main documentation - start here |
| [QUICK-START.md](QUICK-START.md) | Quick reference guide |
| [ROLES-README.md](ROLES-README.md) | Detailed role documentation |
| [STRUCTURE.md](STRUCTURE.md) | Project structure explanation |
| [OPENCONFIG-MIGRATION.md](OPENCONFIG-MIGRATION.md) | OpenConfig conversion notes |
| [INDEX.md](INDEX.md) | This file |

## 🎯 Main Files

| File | Purpose | Usage |
|------|---------|-------|
| `site.yml` | Main playbook | `ansible-playbook site.yml` |
| `inventory.yml` | Device inventory | Auto-loaded by ansible.cfg |
| `ansible.cfg` | Ansible config | Auto-loaded |

## 📁 Playbooks

| File | Purpose | Usage |
|------|---------|-------|
| `playbooks/configure-interfaces.yml` | Configure interfaces only | `ansible-playbook playbooks/configure-interfaces.yml` |
| `playbooks/configure-bgp.yml` | Configure BGP only | `ansible-playbook playbooks/configure-bgp.yml` |
| `playbooks/configure-lldp.yml` | Configure LLDP only | `ansible-playbook playbooks/configure-lldp.yml` |
| `playbooks/verify.yml` | Verify configuration | `ansible-playbook playbooks/verify.yml` |

## 🎭 Roles

| Role | Purpose | Path |
|------|---------|------|
| `openconfig_interfaces` | Configure interfaces | `roles/openconfig_interfaces/` |
| `openconfig_bgp` | Configure BGP | `roles/openconfig_bgp/` |
| `openconfig_lldp` | Configure LLDP | `roles/openconfig_lldp/` |

## 🏷️ Tags

| Tag | Purpose | Usage |
|-----|---------|-------|
| `config` | All configuration | `--tags config` |
| `verify` | All verification | `--tags verify` |
| `interfaces` | Interface config | `--tags interfaces` |
| `bgp` | BGP config | `--tags bgp` |
| `routing` | Routing protocols | `--tags routing` |
| `lldp` | LLDP config | `--tags lldp` |
| `discovery` | Discovery protocols | `--tags discovery` |

## 🚀 Common Commands

```bash
# Deploy everything
ansible-playbook site.yml

# Deploy specific component
ansible-playbook site.yml --tags bgp

# Deploy to specific hosts
ansible-playbook site.yml --limit spines

# Verify configuration
ansible-playbook playbooks/verify.yml

# Dry run
ansible-playbook site.yml --check

# Debug mode
ansible-playbook site.yml -vvv
```

## 📦 Archive

Old playbooks are in `archive/` directory. These are deprecated and kept for reference only.

## 🆘 Getting Help

1. Start with [README.md](README.md)
2. Check [QUICK-START.md](QUICK-START.md) for common tasks
3. Review [ROLES-README.md](ROLES-README.md) for role details
4. See [STRUCTURE.md](STRUCTURE.md) for project organization

## 🔄 Quick Reference

**Most common use case:**
```bash
ansible-playbook site.yml
```

**Verify after deployment:**
```bash
ansible-playbook playbooks/verify.yml
```

**Deploy incrementally:**
```bash
ansible-playbook site.yml --limit spine1
ansible-playbook site.yml --limit spines
ansible-playbook site.yml --limit leafs
```

**Use tags for targeted updates:**
```bash
ansible-playbook site.yml --tags bgp
ansible-playbook site.yml --tags lldp
ansible-playbook site.yml --tags interfaces,bgp
```
