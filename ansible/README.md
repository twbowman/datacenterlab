# Ansible Network Automation - Multi-Method Structure

A role-based Ansible project supporting multiple configuration methods for network devices.

## Overview

This project supports multiple configuration deployment methods, allowing you to test and compare different approaches:

- **srlinux_gnmi Method** (`methods/srlinux_gnmi/`) - ✅ Implemented - Uses gnmic CLI tool with native SR Linux YANG paths
- **gNMI Modules Method** (`methods/gnmi_modules/`) - 🚧 Planned - Uses Ansible gNMI modules
- **NETCONF Method** (`methods/netconf/`) - ❌ N/A - SR Linux doesn't support NETCONF
- **REST Method** (`methods/rest/`) - 💡 Possible - Uses JSON-RPC API

### Important: SR Linux and OpenConfig Limitations

⚠️ **SR Linux OpenConfig Support**: SR Linux only supports OpenConfig YANG models for **read operations** (monitoring/telemetry). Configuration changes **must use native SR Linux YANG paths**.

- ✅ OpenConfig GET operations work (reading state, monitoring)
- ❌ OpenConfig SET operations fail with "OpenConfig management interface is not operational"
- ✅ Native SR Linux paths work for all configuration operations

This is why the srlinux_gnmi method uses native SR Linux paths like:
- `/interface[name=X]` instead of OpenConfig `/interfaces/interface[name=X]`
- `/network-instance[name=default]/protocols/bgp` instead of OpenConfig BGP paths

For vendor-neutral configuration, you would need to:
1. Use native paths per vendor (SR Linux, Arista, etc.)
2. Abstract the differences in Ansible roles/templates
3. Use OpenConfig only for monitoring/verification

## Quick Start

### Deploy with srlinux_gnmi Method (Default)
```bash
# From host machine
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/site.yml

# From within VM
cd ansible
ansible-playbook site.yml
# or explicitly
ansible-playbook methods/srlinux_gnmi/site.yml
```

### Deploy with Specific Method
```bash
# srlinux_gnmi method (uses gnmic CLI tool)
ansible-playbook methods/srlinux_gnmi/site.yml

# gNMI modules method (when available)
ansible-playbook methods/gnmi_modules/site.yml
```

## Structure

```
ansible/
├── site.yml                    # Main playbook (uses srlinux_gnmi by default)
├── inventory.yml               # Shared device inventory
├── ansible.cfg                 # Shared configuration
├── group_vars/                 # Shared variables
│
├── methods/                    # Configuration methods
│   ├── srlinux_gnmi/                # ✅ gnmic CLI tool (implemented)
│   │   ├── site.yml
│   │   ├── playbooks/
│   │   │   ├── configure-interfaces.yml
│   │   │   ├── configure-bgp.yml
│   │   │   └── configure-lldp.yml
│   │   ├── roles/
│   │   │   ├── srlinux_interfaces/
│   │   │   ├── srlinux_bgp/
│   │   │   └── srlinux_lldp/
│   │   └── README.md
│   │
│   ├── gnmi_modules/           # 🚧 Ansible gNMI modules (planned)
│   │   └── README.md
│   │
│   ├── netconf/                # ❌ Not applicable
│   │   └── README.md
│   │
│   └── rest/                   # 💡 Possible future
│       └── README.md
│
├── playbooks/                  # Shared utility playbooks
│   └── verify.yml
│
└── docs/
    ├── README.md               # This file
    ├── METHODS.md              # Method overview
    └── COMPARISON.md           # Detailed comparison
```

### Verify Configuration
```bash
ansible-playbook playbooks/verify.yml
```

## Common Tasks

### Full Deployment
```bash
# Deploy complete configuration (CLI method)
ansible-playbook site.yml
# or explicitly
ansible-playbook methods/cli/site.yml

# Deploy to specific hosts
ansible-playbook methods/cli/site.yml --limit spines
ansible-playbook methods/cli/site.yml --limit leaf1
```

### Deploy Components
```bash
# Interfaces only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml

# BGP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml

# LLDP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-lldp.yml
```

### Using Tags
```bash
# Deploy only BGP across all devices
ansible-playbook methods/srlinux_gnmi/site.yml --tags bgp

# Deploy only LLDP
ansible-playbook methods/srlinux_gnmi/site.yml --tags lldp

# Deploy interfaces and BGP
ansible-playbook methods/srlinux_gnmi/site.yml --tags interfaces,bgp

# Skip LLDP
ansible-playbook methods/srlinux_gnmi/site.yml --skip-tags lldp
```

### Verification
```bash
# Verify everything
ansible-playbook playbooks/verify.yml

# Verify only LLDP
ansible-playbook playbooks/verify.yml --tags lldp

# Verify only BGP
ansible-playbook playbooks/verify.yml --tags bgp
```

### Debug Mode
```bash
# Enable verbose output
ansible-playbook site.yml -vvv

# Enable role debug
ansible-playbook site.yml -e "openconfig_bgp_debug=true"
```

### Dry Run
```bash
# Check what would change
ansible-playbook site.yml --check

# Check syntax
ansible-playbook site.yml --syntax-check
```

## Available Tags

| Tag | Description |
|-----|-------------|
| `config` | All configuration tasks |
| `verify` | All verification tasks |
| `interfaces` | Interface configuration |
| `bgp` | BGP configuration |
| `routing` | Routing protocols (BGP) |
| `lldp` | LLDP configuration |
| `discovery` | Discovery protocols (LLDP) |

## Available Methods

See [METHODS.md](METHODS.md) for detailed information about each method.

### srlinux_gnmi Method (Current Default)
- ✅ Implemented and tested
- Uses gnmic CLI tool for gNMI operations
- True idempotency via gNMI protocol
- Simple and reliable
- See [methods/srlinux_gnmi/README.md](methods/srlinux_gnmi/README.md)

### gNMI Modules Method (Planned)
- 🚧 Awaiting stable Ansible modules
- Uses native Ansible gNMI modules
- More "Ansible-native" experience
- Better integration with Ansible features
- See [methods/gnmi_modules/README.md](methods/gnmi_modules/README.md)

### Method Comparison
See [COMPARISON.md](COMPARISON.md) for detailed comparison of all methods.

## Switching Between Methods

All methods use the same inventory and variables:

```bash
# Use srlinux_gnmi method
ansible-playbook methods/srlinux_gnmi/site.yml

# Use gNMI modules method (when available)
ansible-playbook methods/gnmi_modules/site.yml

# Default (currently srlinux_gnmi)
ansible-playbook site.yml
```

## Roles

### srlinux_gnmi Method Roles

#### srlinux_interfaces
Configures network interfaces using CLI commands.

**What it does:**
- Configures loopback interfaces (system0)
- Configures physical interfaces
- Assigns IPv4 addresses

**Variables:**
- `interfaces`: List of interfaces
- `loopback_ip`: Loopback IP (optional)

#### srlinux_bgp
Configures BGP routing protocol using CLI commands.

**What it does:**
- Configures BGP global settings (AS, router-id)
- Configures BGP neighbors
- Enables IPv4 unicast

**Variables:**
- `asn`: BGP AS number
- `router_id`: BGP router ID
- `interfaces`: List with neighbor info

#### srlinux_lldp
Configures LLDP discovery protocol using CLI commands.

**What it does:**
- Enables LLDP globally
- Enables LLDP per interface
- Enables neighbor discovery

**Variables:**
- `interfaces`: List of interfaces

## Examples

### Deploy to Production
```bash
# Deploy with confirmation
ansible-playbook methods/cli/site.yml --check
ansible-playbook methods/cli/site.yml

# Verify
ansible-playbook playbooks/verify.yml
```

### Deploy to Staging
```bash
# Use different inventory
ansible-playbook -i inventory-staging.yml methods/cli/site.yml
```

### Rollback Strategy
```bash
# Save current config first (manual)
# Then deploy
ansible-playbook methods/cli/site.yml

# If issues, restore from backup
```

### Incremental Deployment
```bash
# Deploy to one spine first
ansible-playbook methods/cli/site.yml --limit spine1

# Verify
ansible-playbook playbooks/verify.yml --limit spine1

# Deploy to all spines
ansible-playbook methods/cli/site.yml --limit spines

# Deploy to all leafs
ansible-playbook methods/cli/site.yml --limit leafs
```

## Best Practices

1. **Choose the right method for your use case**
   - CLI for development/learning
   - gNMI for production (when implemented)

2. **Always verify after deployment**
   ```bash
   ansible-playbook methods/cli/site.yml && ansible-playbook playbooks/verify.yml
   ```

3. **Use tags for targeted updates**
   ```bash
   ansible-playbook methods/cli/site.yml --tags bgp
   ```

4. **Test with --check first**
   ```bash
   ansible-playbook methods/cli/site.yml --check
   ```

5. **Deploy incrementally in production**
   ```bash
   ansible-playbook methods/cli/site.yml --limit spine1
   ```

6. **Use version control**
   - Commit inventory changes
   - Tag releases
   - Document changes

7. **Keep methods in sync**
   - If you update one method, update others
   - Use same inventory and variables

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
ansible all -m ping

# Check inventory
ansible-inventory --list
```

### Role Issues
```bash
# List available roles
ansible-galaxy list

# Check role path
ansible-config dump | grep ROLES_PATH
```

### Debugging
```bash
# Verbose output
ansible-playbook methods/cli/site.yml -vvv

# Step through tasks
ansible-playbook methods/cli/site.yml --step

# Start at specific task
ansible-playbook methods/cli/site.yml --start-at-task="Configure BGP"
```

## Documentation

- **README.md** (this file): Main documentation
- **METHODS.md**: Overview of all configuration methods
- **COMPARISON.md**: Detailed comparison of methods
- **methods/cli/README.md**: CLI method details
- **methods/gnmi/README.md**: gNMI method details
- **STRUCTURE.md**: Project structure notes
- **QUICK-START.md**: Quick reference guide

## Support

For issues or questions:
1. Check the documentation
2. Review role defaults in `roles/*/defaults/main.yml`
3. Enable debug mode: `-e "openconfig_*_debug=true"`
4. Use verbose output: `-vvv`
