# Example Topologies

This directory contains pre-built topology examples demonstrating different network designs and vendor configurations.

## Available Examples

### 1. Simple 2-Spine, 4-Leaf (SR Linux Only)

**File**: `2-spine-4-leaf.yml`

**Description**: Basic Clos fabric with SR Linux devices. Good starting point for learning the lab.

**Topology**:
- 2 Spine switches
- 4 Leaf switches
- 4 Client nodes
- Full mesh between spines and leafs

**Use Cases**:
- Learning SR Linux configuration
- Testing basic BGP/OSPF
- Understanding Clos fabric design
- Developing Ansible playbooks

**Expected Outcomes**:
- All BGP sessions established (spine-leaf iBGP)
- All OSPF neighbors up
- Full reachability between clients
- LLDP topology matches physical connections

### 2. Multi-Vendor Topology

**File**: `multi-vendor.yml`

**Description**: Mixed vendor environment demonstrating vendor-agnostic automation.

**Topology**:
- 1 SR Linux spine
- 1 Arista cEOS spine
- 1 SR Linux leaf
- 1 Arista cEOS leaf
- 1 SONiC leaf
- 1 Juniper cRPD leaf
- 4 Client nodes

**Use Cases**:
- Testing multi-vendor interoperability
- Validating metric normalization
- Testing universal Grafana dashboards
- Demonstrating vendor-agnostic automation

**Expected Outcomes**:
- BGP sessions between different vendors
- Universal metrics from all vendors
- Single dashboard showing all devices
- Consistent interface naming across vendors

### 3. EVPN/VXLAN Fabric

**File**: `evpn-vxlan.yml`

**Description**: Layer 2 overlay network using EVPN/VXLAN.

**Topology**:
- 2 Spine switches (route reflectors)
- 4 Leaf switches (VTEP)
- 4 Client nodes in different VLANs
- EVPN address family in BGP
- VXLAN tunnels between leafs

**Use Cases**:
- Testing EVPN/VXLAN configuration
- Multi-tenancy scenarios
- Layer 2 extension across fabric
- VXLAN tunnel monitoring

**Expected Outcomes**:
- EVPN routes advertised and received
- VXLAN tunnels established
- Layer 2 connectivity within VLANs
- Layer 3 connectivity between VLANs (with IRB)

## Deployment Instructions

### Deploy an Example

```bash
# macOS ARM
orb -m clab sudo containerlab deploy -t topologies/examples/2-spine-4-leaf.yml

# Linux
sudo containerlab deploy -t topologies/examples/2-spine-4-leaf.yml
```

### Configure Devices

Each example includes a corresponding inventory file:

```bash
# macOS ARM
orb -m clab ansible-playbook -i topologies/examples/inventory-2-spine-4-leaf.yml ansible/site.yml

# Linux
ansible-playbook -i topologies/examples/inventory-2-spine-4-leaf.yml ansible/site.yml
```

### Verify Deployment

```bash
# Check all containers are running
docker ps --filter "name=clab-"

# Run verification playbook
ansible-playbook -i topologies/examples/inventory-2-spine-4-leaf.yml ansible/playbooks/verify.yml
```

### Destroy Example

```bash
# macOS ARM
orb -m clab sudo containerlab destroy -t topologies/examples/2-spine-4-leaf.yml

# Linux
sudo containerlab destroy -t topologies/examples/2-spine-4-leaf.yml
```

## Customizing Examples

### Modify Topology

1. Copy example to new file
2. Edit node definitions
3. Update links
4. Adjust management IPs

### Modify Configuration

1. Copy inventory file
2. Update device variables
3. Adjust IP addressing
4. Modify BGP/OSPF parameters

### Add Monitoring

All examples work with the monitoring stack:

```bash
# Deploy monitoring (once)
sudo containerlab deploy -t topology-monitoring.yml

# Monitoring will automatically collect from all devices
```

## Resource Requirements

### 2-Spine-4-Leaf

- **Containers**: 10 (6 switches + 4 clients)
- **RAM**: ~6 GB
- **Disk**: ~15 GB
- **Boot Time**: ~3 minutes

### Multi-Vendor

- **Containers**: 10 (6 switches + 4 clients)
- **RAM**: ~8 GB (varies by vendor)
- **Disk**: ~25 GB (larger images)
- **Boot Time**: ~5 minutes (SONiC is slowest)

### EVPN/VXLAN

- **Containers**: 10 (6 switches + 4 clients)
- **RAM**: ~6 GB
- **Disk**: ~15 GB
- **Boot Time**: ~3 minutes

## Troubleshooting

### Example Won't Deploy

**Check Prerequisites**:
```bash
# Verify images are available
docker images | grep srlinux
docker images | grep ceos
docker images | grep sonic
docker images | grep crpd
```

**Pull Missing Images**:
```bash
# SR Linux (always available)
docker pull ghcr.io/nokia/srlinux:latest

# Other vendors require manual download/build
```

### Configuration Fails

**Check Inventory Path**:
```bash
# Ensure using correct inventory file
ls -l topologies/examples/inventory-*.yml
```

**Verify Device IPs**:
```bash
# Check devices have expected IPs
docker inspect clab-example-spine1 | grep IPAddress
```

### Monitoring Not Working

**Update gNMIc Config**:
```yaml
# Add example devices to monitoring/gnmic/gnmic-config.yml
targets:
  example-spine1:
    address: clab-example-spine1:57400
```

**Restart gNMIc**:
```bash
docker restart clab-monitoring-gnmic
```

## Next Steps

After deploying an example:

1. **Explore the Topology**: Use `docker exec` to access device CLIs
2. **Review Configuration**: Check what Ansible configured
3. **Monitor Metrics**: Open Grafana and view dashboards
4. **Experiment**: Modify configurations and observe results
5. **Create Your Own**: Use examples as templates for custom topologies

## Additional Resources

- **Configuration Guide**: `docs/user/configuration.md`
- **Monitoring Guide**: `docs/user/monitoring.md`
- **Troubleshooting Guide**: `docs/user/troubleshooting.md`
- **Ansible Documentation**: `ansible/README.md`
