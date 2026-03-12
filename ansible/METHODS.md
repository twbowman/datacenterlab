# Configuration Methods

This ansible project supports multiple configuration deployment methods. Each method is organized in its own directory structure, allowing you to test and compare different approaches.

## Available Methods

### 1. srlinux_gnmi Method (`methods/srlinux_gnmi/`)
Uses gnmic CLI tool for gNMI operations.

**Pros:**
- Simple CLI tool
- True idempotency via gNMI
- Fast and efficient
- Easy to debug
- No Ansible collection dependencies

**Cons:**
- Requires gnmic installation
- Shell commands in playbooks
- Certificate management

**Use when:**
- You need reliable automation now
- Want true idempotency
- Prefer simple, working solutions
- Development or production

### 2. gNMI Modules Method (`methods/gnmi_modules/`)
Uses native Ansible gNMI modules.

**Pros:**
- Native Ansible experience
- Better integration (check mode, diff, etc.)
- Type-safe module parameters
- Cleaner playbooks

**Cons:**
- Requires stable Ansible modules
- nokia.grpc collection currently has bugs
- More complex setup

**Use when:**
- Ansible modules become stable
- You want native Ansible experience
- Need advanced Ansible features
- Production deployments

### 3. NETCONF Method (`methods/netconf/`)
Uses NETCONF protocol (if/when SR Linux supports it).

**Status:** Not applicable - SR Linux doesn't support NETCONF

### 4. REST API Method (`methods/rest/`)
Uses JSON-RPC or REST API (if available).

**Status:** Placeholder for future implementation

## Directory Structure

```
ansible/
├── inventory.yml                    # Shared inventory
├── ansible.cfg                      # Shared configuration
├── group_vars/                      # Shared variables
│   ├── all.yml
│   ├── spines.yml
│   └── leafs.yml
│
├── methods/                         # Configuration methods
│   ├── srlinux_gnmi/                     # gnmic CLI tool method
│   │   ├── site.yml                 # Main playbook
│   │   ├── playbooks/               # Component playbooks
│   │   │   ├── configure-interfaces.yml
│   │   │   ├── configure-bgp.yml
│   │   │   ├── configure-lldp.yml
│   │   │   └── verify.yml
│   │   └── roles/                   # srlinux_gnmi-specific roles
│   │       ├── srlinux_interfaces/
│   │       ├── srlinux_bgp/
│   │       └── srlinux_lldp/
│   │
│   ├── gnmi_modules/                # Ansible gNMI modules method
│   │   ├── site.yml
│   │   ├── playbooks/
│   │   └── roles/
│   │       ├── gnmi_interfaces/
│   │       ├── gnmi_bgp/
│   │       └── gnmi_lldp/
│   │
│   ├── netconf/                     # NETCONF method (future)
│   │   └── README.md
│   │
│   └── rest/                        # REST API method (future)
│       └── README.md
│
├── playbooks/                       # Shared utility playbooks
│   └── verify.yml                   # Verification (method-agnostic)
│
└── docs/                            # Documentation
    ├── README.md
    ├── METHODS.md                   # This file
    └── COMPARISON.md                # Method comparison
```

## Usage

### Deploy with srlinux_gnmi Method
```bash
cd ansible
ansible-playbook methods/srlinux_gnmi/site.yml
```

### Deploy with gNMI Modules Method
```bash
cd ansible
ansible-playbook methods/gnmi_modules/site.yml
```

### Deploy Specific Component
```bash
# srlinux_gnmi method - interfaces only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml

# gNMI modules method - BGP only
ansible-playbook methods/gnmi_modules/playbooks/configure-bgp.yml
```

### Compare Methods
```bash
# Deploy with CLI
ansible-playbook methods/cli/site.yml
ansible-playbook playbooks/verify.yml > cli-results.txt

# Redeploy with gNMI
./redeploy-datacenter.sh
ansible-playbook methods/gnmi/site.yml
ansible-playbook playbooks/verify.yml > gnmi-results.txt

# Compare
diff cli-results.txt gnmi-results.txt
```

## Testing Different Methods

### Scenario 1: Test CLI Method
```bash
./redeploy-datacenter.sh
ansible-playbook methods/cli/site.yml
ansible-playbook playbooks/verify.yml
```

### Scenario 2: Test gNMI Method
```bash
./redeploy-datacenter.sh
ansible-playbook methods/gnmi/site.yml
ansible-playbook playbooks/verify.yml
```

### Scenario 3: Mixed Methods
```bash
./redeploy-datacenter.sh
# Use CLI for interfaces
ansible-playbook methods/cli/playbooks/configure-interfaces.yml
# Use gNMI for BGP
ansible-playbook methods/gnmi/playbooks/configure-bgp.yml
ansible-playbook playbooks/verify.yml
```

## Method Selection Guide

| Requirement | Recommended Method |
|-------------|-------------------|
| Maximum compatibility | CLI |
| True idempotency | gNMI |
| Fastest execution | gNMI |
| Easiest debugging | CLI |
| Multi-vendor | gNMI (OpenConfig) |
| Production use | gNMI |
| Development/testing | CLI |
| Learning SR Linux | CLI |

## Adding a New Method

1. Create method directory:
   ```bash
   mkdir -p ansible/methods/newmethod/{playbooks,roles}
   ```

2. Create site.yml:
   ```yaml
   ---
   - name: Configure datacenter network
     hosts: all
     gather_facts: false
     roles:
       - role: newmethod_interfaces
       - role: newmethod_bgp
       - role: newmethod_lldp
   ```

3. Create roles following the pattern in existing methods

4. Document in this file

## Migration Between Methods

All methods use the same inventory and variables, making it easy to switch:

```bash
# Currently using CLI
ansible-playbook methods/cli/site.yml

# Switch to gNMI (same inventory, same variables)
ansible-playbook methods/gnmi/site.yml
```

## Best Practices

1. **Use one method per deployment** - Don't mix methods in production
2. **Test in lab first** - Try new methods in lab before production
3. **Document your choice** - Note which method you're using in runbooks
4. **Keep methods in sync** - If you update one method, update others
5. **Verify after deployment** - Always run verification playbook

## Future Methods

Potential methods to add:
- Terraform provider
- Python scripts (Nornir)
- Go-based automation
- Streaming telemetry configuration
- Intent-based networking (IBN)
