---
inclusion: auto
---

# Containerlab Command Execution Rules

## Platform Context

**This lab runs on macOS with ARM processor (Apple Silicon).**

Containerlab does not run natively on ARM Macs, so we use **ORB** (a lightweight VM manager) to run containerlab in an x86_64 Linux VM with emulation.

### Why ORB is Required
- **ARM Limitation**: Containerlab and SR Linux containers require x86_64 architecture
- **ORB Solution**: Creates a Linux VM with proper emulation for containerlab
- **Transparent**: Commands run in VM but files sync with local workspace

### When ORB is NOT Needed
If you were running on:
- **Linux x86_64**: Run containerlab commands directly (no `orb -m clab` prefix)
- **Intel Mac**: May run natively with Docker Desktop (no `orb -m clab` prefix)
- **Windows with WSL2**: Run containerlab in WSL2 directly (no `orb -m clab` prefix)

## CRITICAL: All Commands Must Run in ORB VM Context

**ALWAYS** prefix containerlab-related commands with `orb -m clab` to execute them in the correct VM context.

### Command Patterns

#### Docker Commands
```bash
# CORRECT
orb -m clab docker exec clab-gnmi-clos-leaf1 sr_cli "show version"
orb -m clab docker ps
orb -m clab docker logs clab-monitoring-grafana

# WRONG - Will fail or run in wrong context
docker exec clab-gnmi-clos-leaf1 sr_cli "show version"
```

#### Containerlab Commands
```bash
# CORRECT
orb -m clab sudo containerlab deploy -t topology.yml
orb -m clab sudo containerlab destroy -t topology.yml
orb -m clab sudo containerlab inspect

# WRONG
sudo containerlab deploy -t topology.yml
```

#### Ansible Commands
```bash
# CORRECT
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/site.yml

# WRONG
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/site.yml
```

#### Shell Scripts
```bash
# CORRECT
orb -m clab ./generate-traffic.sh
orb -m clab ./check-monitoring.sh

# WRONG
./generate-traffic.sh
```

#### File Operations in VM
```bash
# CORRECT - For files that need to be in the VM
orb -m clab cat /path/to/file
orb -m clab ls -la

# Local file operations don't need orb prefix
cat README.md
ls -la
```

### When NOT to Use `orb -m clab`

- Reading/writing files in the local workspace (use normal file tools)
- Git operations
- Local Python scripts that don't interact with containers
- Editing configuration files

### Quick Reference

| Task | Command Prefix |
|------|----------------|
| Docker operations | `orb -m clab docker ...` |
| Containerlab CLI | `orb -m clab sudo containerlab ...` |
| Ansible playbooks | `orb -m clab ansible-playbook ...` |
| Shell scripts | `orb -m clab ./script.sh` |
| SR Linux CLI | `orb -m clab docker exec clab-gnmi-clos-<device> sr_cli ...` |
| gNMI commands | `orb -m clab gnmic ...` |
| Local files | No prefix needed |

### Common Mistakes to Avoid

1. ❌ Running docker commands without `orb -m clab`
2. ❌ Running ansible without `orb -m clab`
3. ❌ Forgetting `sudo` for containerlab commands
4. ❌ Using `cd` command (use `cwd` parameter instead)

### Container Naming Convention

All lab containers follow this pattern:
- Network devices: `clab-gnmi-clos-<device>` (e.g., `clab-gnmi-clos-leaf1`)
- Clients: `clab-gnmi-clos-client<N>` (e.g., `clab-gnmi-clos-client1`)
- Monitoring: `clab-monitoring-<service>` (e.g., `clab-monitoring-grafana`)

### Verification

To verify you're in the correct context:
```bash
orb -m clab docker ps | grep clab-gnmi-clos
```

This should show all running lab containers.
