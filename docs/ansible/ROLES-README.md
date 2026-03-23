# Ansible Roles for OpenConfig Network Configuration

This directory contains Ansible roles for configuring network devices using OpenConfig YANG models.

## Directory Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory.yml            # Device inventory
├── site.yml                 # Main playbook (deploys everything)
├── playbooks/               # Individual playbooks
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml
│   └── configure-lldp.yml
└── roles/                   # Reusable roles
    ├── openconfig_interfaces/
    ├── openconfig_bgp/
    └── openconfig_lldp/
```

## Roles

### openconfig_interfaces
Configures network interfaces using OpenConfig YANG models.

**Features:**
- Loopback interface configuration (system0)
- Physical interface configuration
- IPv4 address assignment
- Interface descriptions

**Variables:**
- `interfaces`: List of interfaces to configure
- `loopback_ip`: Loopback IP address (optional, for leafs)
- `gnmi_port`: gNMI/JSON-RPC port (default: 57400)
- `gnmi_username`: Authentication username (default: admin)
- `gnmi_password`: Authentication password
- `openconfig_interfaces_debug`: Enable debug output (default: false)

### openconfig_bgp
Configures BGP protocol using OpenConfig YANG models.

**Features:**
- BGP global configuration (AS number, router-id)
- BGP neighbor configuration
- IPv4 unicast address family

**Variables:**
- `asn`: BGP AS number
- `router_id`: BGP router ID
- `interfaces`: List of interfaces with neighbor information
- `gnmi_port`: gNMI/JSON-RPC port (default: 57400)
- `gnmi_username`: Authentication username (default: admin)
- `gnmi_password`: Authentication password
- `openconfig_bgp_debug`: Enable debug output (default: false)

### openconfig_lldp
Configures LLDP protocol using OpenConfig YANG models.

**Features:**
- Global LLDP enablement
- Per-interface LLDP configuration
- Automatic neighbor discovery

**Variables:**
- `interfaces`: List of interfaces to enable LLDP on
- `gnmi_port`: gNMI/JSON-RPC port (default: 57400)
- `gnmi_username`: Authentication username (default: admin)
- `gnmi_password`: Authentication password
- `openconfig_lldp_debug`: Enable debug output (default: false)

## Usage

### Deploy Complete Configuration

```bash
# From your host machine
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# From within the remote server
cd /vagrant/containerlab/ansible
ansible-playbook site.yml
```

### Deploy Individual Components

```bash
# Configure interfaces only
ansible-playbook playbooks/configure-interfaces.yml

# Configure BGP only
ansible-playbook playbooks/configure-bgp.yml

# Configure LLDP only
ansible-playbook playbooks/configure-lldp.yml
```

### Target Specific Hosts

```bash
# Configure only spine switches
ansible-playbook site.yml --limit spines

# Configure only leaf1
ansible-playbook site.yml --limit leaf1

# Configure all leafs
ansible-playbook site.yml --limit leafs
```

### Enable Debug Output

```bash
# Enable debug for specific role
ansible-playbook playbooks/configure-bgp.yml -e "openconfig_bgp_debug=true"

# Enable debug for all roles
ansible-playbook site.yml -e "openconfig_interfaces_debug=true openconfig_bgp_debug=true openconfig_lldp_debug=true"
```

## Role Development

### Creating a New Role

```bash
# Create role structure
mkdir -p ansible/roles/my_role/{tasks,defaults,handlers,meta,templates,files}

# Create main task file
cat > ansible/roles/my_role/tasks/main.yml <<EOF
---
# tasks file for my_role
- name: Example task
  ansible.builtin.debug:
    msg: "Hello from my_role"
EOF

# Create defaults
cat > ansible/roles/my_role/defaults/main.yml <<EOF
---
# defaults file for my_role
my_variable: default_value
EOF

# Create metadata
cat > ansible/roles/my_role/meta/main.yml <<EOF
---
galaxy_info:
  author: Your Name
  description: Role description
  license: MIT
  min_ansible_version: "2.9"
dependencies: []
EOF
```

### Testing Roles

```bash
# Test role syntax
ansible-playbook --syntax-check playbooks/configure-bgp.yml

# Dry run (check mode)
ansible-playbook --check playbooks/configure-bgp.yml

# Run with increased verbosity
ansible-playbook -vvv playbooks/configure-bgp.yml
```

## Benefits of Role-Based Structure

1. **Reusability**: Roles can be used across multiple playbooks
2. **Modularity**: Each role handles a specific function
3. **Maintainability**: Easier to update and test individual components
4. **Scalability**: Easy to add new roles for additional protocols
5. **Sharing**: Roles can be published to Ansible Galaxy
6. **Testing**: Each role can be tested independently
7. **Documentation**: Self-contained with defaults and metadata

## OpenConfig Compliance

All roles use OpenConfig YANG models:
- **Interfaces**: `openconfig-interfaces`
- **BGP**: `openconfig-bgp`, `openconfig-network-instance`
- **LLDP**: `openconfig-lldp`

This ensures vendor-neutral configuration that works across different network devices.

## Troubleshooting

### Role Not Found

```bash
# Check roles path
ansible-config dump | grep ROLES_PATH

# Verify role exists
ls -la ansible/roles/
```

### Connection Issues

```bash
# Test connectivity to devices
ansible all -m ping

# Check inventory
ansible-inventory --list
```

### Debug gNMI/JSON-RPC

```bash
# Enable verbose output
ansible-playbook -vvv playbooks/configure-bgp.yml

# Check if gNMI port is accessible
docker exec clab-gnmi-clos-spine1 netstat -tlnp | grep 57400
```

## Migration from Old Playbooks

Old playbooks in the root `ansible/` directory are deprecated. Use the new role-based playbooks:

| Old Playbook | New Playbook |
|-------------|--------------|
| `configure-interfaces.yml` | `playbooks/configure-interfaces.yml` |
| `configure-bgp.yml` | `playbooks/configure-bgp.yml` |
| `configure-lldp.yml` | `playbooks/configure-lldp.yml` |
| N/A | `site.yml` (deploys all) |

## Contributing

When adding new roles:
1. Follow the existing role structure
2. Use OpenConfig YANG models
3. Add proper defaults and documentation
4. Test thoroughly before committing
5. Update this README
