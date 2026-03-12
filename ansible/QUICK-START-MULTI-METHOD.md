# Quick Start: Multi-Method Configuration

## TL;DR

```bash
# Deploy everything with CLI method (default)
./deploy-datacenter.sh

# Or manually
cd ansible
ansible-playbook site.yml
```

## What Changed?

The ansible directory now supports multiple configuration methods. You can use CLI, gNMI, or REST methods to configure your network.

## Available Methods

| Method | Status | Command |
|--------|--------|---------|
| CLI | ✅ Ready | `ansible-playbook methods/cli/site.yml` |
| gNMI | 🚧 Planned | `ansible-playbook methods/gnmi/site.yml` |
| REST | 💡 Future | `ansible-playbook methods/rest/site.yml` |

## Quick Commands

### Deploy Everything
```bash
# Default (CLI method)
ansible-playbook site.yml

# Explicit CLI method
ansible-playbook methods/cli/site.yml
```

### Deploy Components
```bash
# Interfaces only
ansible-playbook methods/cli/playbooks/configure-interfaces.yml

# BGP only
ansible-playbook methods/cli/playbooks/configure-bgp.yml

# LLDP only
ansible-playbook methods/cli/playbooks/configure-lldp.yml
```

### Use Tags
```bash
# Deploy only BGP
ansible-playbook methods/cli/site.yml --tags bgp

# Deploy interfaces and LLDP
ansible-playbook methods/cli/site.yml --tags interfaces,lldp

# Skip LLDP
ansible-playbook methods/cli/site.yml --skip-tags lldp
```

### Limit to Devices
```bash
# Spines only
ansible-playbook methods/cli/site.yml --limit spines

# One device
ansible-playbook methods/cli/site.yml --limit spine1

# Leafs only
ansible-playbook methods/cli/site.yml --limit leafs
```

## Common Workflows

### Fresh Deployment
```bash
./deploy-datacenter.sh
```

This script:
1. Deploys containerlab topology
2. Waits for devices to boot
3. Configures network via CLI method
4. Verifies configuration

### Manual Deployment
```bash
# Deploy topology
./deploy.sh

# Wait for boot
sleep 120

# Configure
cd ansible
ansible-playbook methods/cli/site.yml

# Verify
ansible-playbook playbooks/verify.yml
```

### Redeploy from Scratch
```bash
./redeploy-datacenter.sh
```

This script:
1. Destroys existing lab
2. Deploys fresh topology
3. Configures network
4. Verifies configuration

### Update Configuration
```bash
# Edit inventory
vim ansible/inventory.yml

# Apply changes
cd ansible
ansible-playbook methods/cli/site.yml

# Verify
ansible-playbook playbooks/verify.yml
```

### Deploy Specific Component
```bash
cd ansible

# Update only interfaces
ansible-playbook methods/cli/playbooks/configure-interfaces.yml

# Update only BGP
ansible-playbook methods/cli/playbooks/configure-bgp.yml
```

## Testing Different Methods

### Test CLI Method
```bash
./redeploy-datacenter.sh
# Uses CLI method by default
```

### Test gNMI Method (when implemented)
```bash
# Deploy topology
./deploy.sh
sleep 120

# Configure with gNMI
cd ansible
ansible-playbook methods/gnmi/site.yml

# Verify
ansible-playbook playbooks/verify.yml
```

### Compare Methods
```bash
# Test CLI
ansible-playbook methods/cli/site.yml
ansible-playbook playbooks/verify.yml > cli-results.txt

# Redeploy
cd ..
./redeploy-datacenter.sh

# Test gNMI
cd ansible
ansible-playbook methods/gnmi/site.yml
ansible-playbook playbooks/verify.yml > gnmi-results.txt

# Compare
diff cli-results.txt gnmi-results.txt
```

## Troubleshooting

### Check Syntax
```bash
ansible-playbook methods/cli/site.yml --syntax-check
```

### Dry Run
```bash
ansible-playbook methods/cli/site.yml --check
```

### Verbose Output
```bash
ansible-playbook methods/cli/site.yml -vvv
```

### Test Connectivity
```bash
ansible all -m ping
```

### List Inventory
```bash
ansible-inventory --list
```

## Method Selection Guide

### Use CLI Method When:
- Learning SR Linux
- Development and testing
- Debugging configuration issues
- Need simple, reliable automation
- Don't need true idempotency

### Use gNMI Method When:
- Production deployments
- Need true idempotency
- Performance is critical
- Multi-vendor environment
- Using OpenConfig models

### Use REST Method When:
- Web application integration
- Building custom dashboards
- Simple HTTP-based automation
- No gRPC support available

## File Locations

### Main Files
- `ansible/site.yml` - Main playbook (imports CLI by default)
- `ansible/inventory.yml` - Device inventory
- `ansible/ansible.cfg` - Ansible configuration

### CLI Method
- `ansible/methods/cli/site.yml` - CLI method main playbook
- `ansible/methods/cli/playbooks/` - Component playbooks
- `ansible/methods/cli/roles/` - CLI-specific roles

### Documentation
- `ansible/README.md` - Main documentation
- `ansible/METHODS.md` - Method overview
- `ansible/COMPARISON.md` - Method comparison
- `ansible/methods/cli/README.md` - CLI method details

## Examples

### Example 1: Deploy to Lab
```bash
# From Mac
orb -m clab

# In VM
cd /vagrant/containerlab
./deploy-datacenter.sh
```

### Example 2: Update BGP Configuration
```bash
# Edit inventory
vim ansible/inventory.yml
# Change ASN or add neighbors

# Apply changes
cd ansible
ansible-playbook methods/cli/playbooks/configure-bgp.yml

# Verify
ansible-playbook playbooks/verify.yml --tags bgp
```

### Example 3: Deploy to Spines Only
```bash
cd ansible
ansible-playbook methods/cli/site.yml --limit spines
ansible-playbook playbooks/verify.yml --limit spines
```

### Example 4: Incremental Deployment
```bash
cd ansible

# Deploy to one spine first
ansible-playbook methods/cli/site.yml --limit spine1

# Verify
ansible-playbook playbooks/verify.yml --limit spine1

# If good, deploy to all spines
ansible-playbook methods/cli/site.yml --limit spines

# Then deploy to leafs
ansible-playbook methods/cli/site.yml --limit leafs
```

## Next Steps

1. **Read the docs**
   - `ansible/METHODS.md` - Understand available methods
   - `ansible/COMPARISON.md` - Compare methods
   - `ansible/methods/cli/README.md` - CLI method details

2. **Test CLI method**
   ```bash
   ./deploy-datacenter.sh
   ```

3. **Explore other methods**
   - Review gNMI method documentation
   - Consider REST method for web integration

4. **Customize for your needs**
   - Edit inventory for your topology
   - Add new roles for additional features
   - Create custom playbooks

## Help

### Documentation
- Main docs: `ansible/README.md`
- Method overview: `ansible/METHODS.md`
- Comparison: `ansible/COMPARISON.md`
- Architecture: `ansible/ARCHITECTURE.md`

### Common Issues

**Issue:** Roles not found
```bash
# Check roles_path in ansible.cfg
cat ansible/ansible.cfg | grep roles_path
```

**Issue:** Connection failed
```bash
# Check containers are running
docker ps | grep clab-gnmi-clos

# Test connectivity
ansible all -m ping
```

**Issue:** Configuration not applied
```bash
# Check with verbose output
ansible-playbook methods/cli/site.yml -vvv

# Check device manually
docker exec clab-gnmi-clos-spine1 sr_cli "info from running"
```

## Summary

The multi-method structure allows you to:
- ✅ Use CLI method (ready now)
- 🚧 Use gNMI method (when implemented)
- 💡 Use REST method (future)
- 🔄 Switch between methods easily
- 📊 Compare method performance
- 🎯 Choose best method for your use case

Default command remains simple:
```bash
ansible-playbook site.yml
```
