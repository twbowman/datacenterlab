# srlinux_gnmi Configuration Method

This method uses the `gnmic` CLI tool to configure devices via gNMI protocol.

## Overview

The srlinux_gnmi method uses `gnmic` (gNMI CLI tool) to send configuration commands to SR Linux devices over gRPC. This provides true idempotency through the gNMI protocol while maintaining the simplicity of CLI commands.

### Important: Native SR Linux Paths Required

⚠️ **This method uses native SR Linux YANG paths, not OpenConfig models.**

SR Linux has limited OpenConfig support:
- ✅ OpenConfig works for **read operations** (GET) - monitoring and telemetry
- ❌ OpenConfig fails for **write operations** (SET) - configuration changes
- Error: "OpenConfig management interface is not operational"

Therefore, all configuration must use native SR Linux paths:
- `/interface[name=X]` (not OpenConfig `/interfaces/interface[name=X]`)
- `/network-instance[name=default]/protocols/bgp` (not OpenConfig BGP paths)
- `/system/lldp` (not OpenConfig `/lldp`)

This is a platform limitation, not a method limitation. Other vendors may have full OpenConfig support for configuration.

## Pros
- True idempotency (gNMI protocol handles it)
- Fast and efficient (gRPC/binary protocol)
- Simple CLI tool (easy to test manually)
- No Ansible collection dependencies
- Works with native SR Linux paths
- Easy to debug

## Cons
- Requires gnmic installation
- Certificate management (using --skip-verify for lab)
- Limited to SR Linux native paths (not OpenConfig for config)

## Prerequisites

### Install gnmic
```bash
# Install gnmic CLI tool
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"

# Verify installation
gnmic version
```

## Usage

### Full Deployment
```bash
cd ansible
ansible-playbook methods/srlinux_gnmi/site.yml
```

### Verification
```bash
# Basic verification
ansible-playbook methods/srlinux_gnmi/playbooks/verify.yml

# Detailed verification with neighbor status
ansible-playbook methods/srlinux_gnmi/playbooks/verify-detailed.yml
```

### Component Deployment
```bash
# Interfaces only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-interfaces.yml

# LLDP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-lldp.yml

# BGP only
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml
```

### With Tags
```bash
# Deploy only BGP
ansible-playbook methods/srlinux_gnmi/site.yml --tags bgp

# Deploy interfaces and LLDP
ansible-playbook methods/srlinux_gnmi/site.yml --tags interfaces,lldp

# Skip LLDP
ansible-playbook methods/srlinux_gnmi/site.yml --skip-tags lldp
```

### Limit to Specific Hosts
```bash
# Deploy to spines only
ansible-playbook methods/srlinux_gnmi/site.yml --limit spines

# Deploy to one leaf
ansible-playbook methods/srlinux_gnmi/site.yml --limit leaf1
```

## Roles

### srlinux_interfaces
Configures network interfaces and IP addresses.

**Tasks:**
1. Check if interface is configured
2. Configure interface if needed
3. Configure system0 loopback (leafs only)

**Variables:**
- `interfaces`: List of interfaces with name, ip
- `loopback_ip`: Loopback IP address (optional)

### srlinux_lldp
Enables LLDP for neighbor discovery.

**Tasks:**
1. Check if LLDP is globally enabled
2. Enable LLDP globally if needed
3. Check LLDP on each interface
4. Enable LLDP per interface if needed

**Variables:**
- `interfaces`: List of interfaces

### srlinux_bgp
Configures BGP routing protocol.

**Tasks:**
1. Check if BGP is configured
2. Configure BGP global settings (AS, router-id)
3. Check BGP neighbors
4. Configure BGP neighbors if needed

**Variables:**
- `asn`: BGP AS number
- `router_id`: BGP router ID
- `interfaces`: List with neighbor_ip, neighbor_asn

## How It Works

Each role uses `gnmic` to send gNMI Set operations:

1. **Connect via gNMI** - Uses gRPC to connect to device
2. **Send configuration** - Uses gNMI Set with update operations
3. **Protocol handles idempotency** - gNMI ensures idempotent operations
4. **Report changes** - Based on gnmic output

Example:
```yaml
- name: Configure interface via gnmic
  shell: |
    gnmic -a {{ ansible_host }}:57400 \
      -u admin -p NokiaSrl1! \
      --skip-verify \
      set \
      --update-path /interface[name=ethernet-1/1]/admin-state \
      --update-value enable
  register: result
  changed_when: "'success' in result.stdout or 'ok' in result.stdout"
```

## Idempotency

This method provides true idempotency:
- gNMI protocol handles idempotency natively
- Same configuration applied multiple times = no changes
- Accurate change detection
- No string parsing needed

Benefits:
- ✅ True idempotency via gNMI protocol
- ✅ Detects actual configuration drift
- ✅ Atomic operations
- ✅ Accurate change reporting

## Debugging

### Enable Verbose Output
```bash
ansible-playbook methods/srlinux_gnmi/site.yml -vvv
```

### Test Single Command
```bash
# Test on one device
ansible-playbook methods/srlinux_gnmi/site.yml --limit spine1 -vvv

# Test one role
ansible-playbook methods/srlinux_gnmi/site.yml --tags interfaces -vvv
```

### Manual Testing
```bash
# Test gnmic connection
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities

# Test get operation
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify \
  get --path /interface[name=ethernet-1/1]

# Test set operation
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify \
  set --update-path /interface[name=ethernet-1/1]/admin-state \
      --update-value enable
```

## Troubleshooting

### gnmic Not Found
```bash
# Install gnmic
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"

# Verify
gnmic version
```

### Connection Refused
- Check device is running: `docker ps | grep clab-gnmi-clos`
- Check gNMI port (57400) is accessible
- Verify management IP in inventory

### Certificate Errors
- Using `--skip-verify` for lab environment
- For production, use proper certificates

### Configuration Not Applied
- Check gnmic output for errors
- Verify SR Linux path syntax
- Test gnmic command manually
- Check device logs

## Best Practices

1. **Test in lab first** - Always test changes in lab environment
2. **Use check mode** - Run with `--check` to see what would change
3. **Deploy incrementally** - Use `--limit` to deploy to one device first
4. **Verify after deployment** - Run verification playbook
5. **Keep roles simple** - One role per feature
6. **Document commands** - Add comments explaining CLI commands

## Examples

### Fresh Deployment
```bash
# Deploy everything
ansible-playbook methods/srlinux_gnmi/site.yml

# Verify
ansible-playbook methods/srlinux_gnmi/playbooks/verify.yml

# Detailed verification
ansible-playbook methods/srlinux_gnmi/playbooks/verify-detailed.yml
```

### Update BGP Configuration
```bash
# Update inventory with new BGP neighbors
vim inventory.yml

# Deploy only BGP changes
ansible-playbook methods/srlinux_gnmi/playbooks/configure-bgp.yml

# Verify BGP
ansible-playbook playbooks/verify.yml --tags bgp
```

### Rollback Strategy
```bash
# Save current config
for node in spine1 spine2 leaf1 leaf2 leaf3 leaf4; do
  docker exec clab-gnmi-clos-$node sr_cli "info from running" > backup-$node.txt
done

# Deploy changes
ansible-playbook methods/cli/site.yml

# If issues, restore manually from backup files
```

## Comparison with Other Methods

| Feature | CLI | gNMI | NETCONF |
|---------|-----|------|---------|
| Idempotency | Pseudo | True | True |
| Speed | Slow | Fast | Medium |
| Complexity | Low | Medium | High |
| Dependencies | Docker | gRPC libs | NETCONF libs |
| Debugging | Easy | Medium | Hard |
| Multi-vendor | No | Yes | Yes |

## When to Use

Use CLI method when:
- Learning SR Linux
- Debugging configuration issues
- Need maximum compatibility
- Working in development/lab environment
- Don't need true idempotency
- Want simple, easy-to-understand automation

Use gNMI method when:
- Need true idempotency
- Production deployments
- Multi-vendor environments
- Performance is critical
- Using OpenConfig models
