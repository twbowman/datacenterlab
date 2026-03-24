---
inclusion: auto
---

# Containerlab Command Execution Rules

## Platform Context

**Development happens on macOS ARM (Apple Silicon). The lab runs on a remote x86_64 Linux server.**

All containerlab, Docker, Ansible, and gNMI commands execute on the remote server via the `./lab` wrapper script. The wrapper handles SSH, rsync, and tunneling automatically.

### Why Remote Execution
- **ARM Limitation**: SONiC VS images are x86_64 only; SR Linux containers also require x86_64
- **Remote Server**: Hetzner Cloud (CPX31/CPX41) running Ubuntu, provisioned via Terraform (`terraform/create-lab.sh`) or `./scripts/lab setup`
- **Transparent**: `./lab` syncs the repo and runs commands remotely over SSH

## CRITICAL: Use the `./lab` Wrapper for All Remote Commands

**NEVER** run containerlab, Docker, or Ansible commands directly. Always use the `./lab` wrapper.

### Command Patterns

#### Lab Lifecycle
```bash
# Deploy a topology (default vendor from .env, or specify)
./lab deploy
./lab deploy srlinux
./lab deploy sonic

# Destroy a topology
./lab destroy
./lab destroy sonic

# Check running containers
./lab status
```

#### Configuration and Validation
```bash
# Run the main site playbook (syncs repo first)
./lab configure

# Run a specific playbook
./lab configure ansible/methods/srlinux_gnmi/playbooks/configure-evpn.yml

# Run validation checks
./lab validate
```

#### Remote Access
```bash
# Open SSH session to the remote server
./lab ssh

# Run an arbitrary command on the remote server
./lab exec "docker exec clab-gnmi-clos-leaf1 sr_cli 'show version'"
./lab exec "docker ps"
./lab exec "gnmic -a clab-gnmi-clos-leaf1 get --path /system/name"

# Sync repo without deploying
./lab sync
```

#### Monitoring Tunnels
```bash
# Open SSH tunnels for Grafana (3000), Prometheus (9090), gNMIc (9273)
./lab tunnel
# Then open http://localhost:3000 in your browser
```

#### First-Time Server Setup
```bash
# Provision the remote server (Docker, containerlab, gnmic, Ansible, Python deps)
./lab setup
```

### When NOT to Use `./lab`

- Reading/writing files in the local workspace (use normal file tools)
- Git operations (run locally)
- Editing configuration files (edit locally, `./lab sync` pushes changes)
- Local Python scripts that don't interact with containers

### Quick Reference

| Task | Command |
|------|---------|
| Deploy lab | `./lab deploy [srlinux\|sonic]` |
| Destroy lab | `./lab destroy [srlinux\|sonic]` |
| Configure fabric | `./lab configure` |
| Validate state | `./lab validate` |
| Check containers | `./lab status` |
| SSH to server | `./lab ssh` |
| Run remote command | `./lab exec "<cmd>"` |
| Sync repo | `./lab sync` |
| Open dashboards | `./lab tunnel` |
| Setup server | `./lab setup` |

### Configuration

The `./lab` wrapper reads from `.env` (copy from `.env.example`):
```bash
LAB_HOST=65.108.x.x          # Remote server IP
LAB_USER=root                 # SSH user
LAB_SSH_KEY=~/.ssh/id_ed25519 # SSH key
LAB_VENDOR=srlinux            # Default vendor
LAB_REMOTE_DIR=/opt/containerlab
```

### Container Naming Convention

All lab containers follow this pattern:
- Network devices: `clab-gnmi-clos-<device>` (e.g., `clab-gnmi-clos-leaf1`)
- Clients: `clab-gnmi-clos-client<N>` (e.g., `clab-gnmi-clos-client1`)
- Monitoring: `clab-monitoring-<service>` (e.g., `clab-monitoring-grafana`)

### Common Mistakes to Avoid

1. ❌ Running docker/containerlab/ansible commands directly (use `./lab` wrapper)
2. ❌ Forgetting to `./lab sync` after local edits before running remote commands (deploy/configure auto-sync)
3. ❌ Using `cd` command (use `cwd` parameter instead)
4. ❌ Editing `.env` and committing it (it contains secrets, is in `.gitignore`)
