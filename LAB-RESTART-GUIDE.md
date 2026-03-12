# Datacenter Network Deployment Guide

## Overview

This lab simulates deploying a fresh datacenter network. Each restart brings up switches with minimal configuration (hostname + gNMI), then Ansible configures everything else - just like a real datacenter deployment.

## TL;DR - Deploy Fresh Datacenter

```bash
# One-command deployment
./deploy-datacenter.sh

# Or full redeploy (destroy + deploy)
./redeploy-datacenter.sh
```

## What Comes Up on Boot

When devices boot, they have ONLY:
- ✅ Hostname (spine1, leaf1, etc.)
- ✅ gNMI server enabled on mgmt interface
- ✅ Management IP (assigned by containerlab)

Everything else is configured by Ansible:
- 🔧 Interface IP addresses
- 🔧 LLDP configuration
- 🔧 BGP configuration
- 🔧 Network instance setup

This simulates a real datacenter where switches boot with minimal config and automation handles the rest.

## Deployment Scripts

### deploy-datacenter.sh
Deploys and configures a fresh datacenter network:
1. Deploys containerlab topology
2. Waits for devices to boot (120 seconds)
3. Runs Ansible playbooks to configure:
   - Interfaces
   - LLDP
   - BGP
4. Verifies configuration

### redeploy-datacenter.sh
Full redeploy (destroy + deploy):
1. Destroys existing lab
2. Runs deploy-datacenter.sh

## Manual Deployment Steps

If you want to run steps manually:

### Step 1: Deploy Lab

```bash
./deploy.sh
```

This creates:
- 2 spine switches (minimal config)
- 4 leaf switches (minimal config)
- 4 client nodes
- 3 monitoring containers (Grafana, Prometheus, gNMIc)

### Step 2: Wait for Boot

```bash
# Wait 2 minutes for devices to fully boot
sleep 120
```

### Step 3: Configure via Ansible

```bash
cd ansible

# Configure interfaces (must be first)
ansible-playbook playbooks/configure-interfaces.yml

# Configure LLDP
ansible-playbook playbooks/configure-lldp.yml

# Configure BGP
ansible-playbook playbooks/configure-bgp.yml

# Or run all at once
ansible-playbook site.yml
```

### Step 4: Verify

```bash
# Run verification playbook
ansible-playbook playbooks/verify.yml

# Or manual verification
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"
```

## What Gets Configured by Ansible

### Interfaces (configure-interfaces.yml)
- Interface IP addresses on all uplinks
- System0 loopback interfaces
- Interface admin state (enable)
- Network instance bindings

### LLDP (configure-lldp.yml)
- LLDP global enable
- LLDP per-interface enable
- Neighbor discovery

### BGP (configure-bgp.yml)
- BGP autonomous system numbers
- BGP router IDs
- BGP peer groups
- BGP neighbors
- IPv4 unicast address family

## Monitoring Stack

The monitoring stack starts automatically and begins collecting data once devices are configured:

| Component | IP | Port | Purpose |
|-----------|-----|------|---------|
| Grafana | 172.20.20.2 | 3000 | Visualization |
| Prometheus | 172.20.20.3 | 9090 | Metrics storage |
| gNMIc | 172.20.20.5 | 9273 | Telemetry collector |

### Persistent Data

Monitoring data persists across restarts:
- Grafana dashboards and settings: `monitoring/grafana/data/`
- Prometheus metrics (30 days): `monitoring/prometheus/data/`

## Verification Commands

### Check All Containers Running

```bash
docker ps --filter "name=clab-gnmi-clos"

# Should see 13 containers:
# - 2 spines, 4 leafs, 4 clients, 3 monitoring
```

### Check BGP Neighbors

```bash
# Spine1 should have 4 BGP neighbors (all leafs)
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"

# Leaf1 should have 2 BGP neighbors (both spines)
docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor"
```

### Check LLDP Neighbors

```bash
# Spine1 should see 4 LLDP neighbors (all leafs)
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"

# Leaf1 should see 3 LLDP neighbors (2 spines + 1 client)
docker exec clab-gnmi-clos-leaf1 sr_cli "show system lldp neighbor"
```

### Check Client Connectivity

```bash
# Client1 should be able to ping Client2
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.2.10

# Client1 should be able to ping Client3
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.3.10
```

### Check Monitoring

```bash
# Check gNMIc is collecting
curl http://172.20.20.5:9273/metrics | grep gnmic_interface

# Check Prometheus has data
curl 'http://172.20.20.3:9090/api/v1/query?query=up'

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

## Ansible Playbook Reference

### Individual Playbooks

```bash
cd ansible

# Configure interfaces only
ansible-playbook playbooks/configure-interfaces.yml

# Configure LLDP only
ansible-playbook playbooks/configure-lldp.yml

# Configure BGP only
ansible-playbook playbooks/configure-bgp.yml

# Verify configuration
ansible-playbook playbooks/verify.yml
```

### Main Playbook (All Configuration)

```bash
cd ansible

# Run all configuration
ansible-playbook site.yml

# Run specific tags
ansible-playbook site.yml --tags interfaces
ansible-playbook site.yml --tags lldp
ansible-playbook site.yml --tags bgp
ansible-playbook site.yml --tags verify
```

## Troubleshooting

### Devices Not Responding

```bash
# Check containers are running
docker ps --filter "name=clab-gnmi-clos"

# Check device logs
docker logs clab-gnmi-clos-spine1

# Wait longer - devices can take 2-3 minutes to boot
sleep 60
```

### Ansible Connection Failures

```bash
# Verify gNMI is enabled
docker exec clab-gnmi-clos-spine1 sr_cli "show system gnmi-server"

# Check device is reachable
ping -c 3 172.20.20.10

# Verify credentials (default: admin/NokiaSrl1!)
docker exec clab-gnmi-clos-spine1 sr_cli
```

### BGP Neighbors Not Establishing

```bash
# Check interfaces are configured first
docker exec clab-gnmi-clos-spine1 sr_cli "show interface brief"

# Check BGP configuration
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp"

# Check BGP neighbor state
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"
```

### LLDP Not Working

```bash
# Check LLDP is enabled globally
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp"

# Check LLDP on interfaces
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp interface"

# Wait for neighbor discovery (can take 30-60 seconds)
sleep 30
```

### Monitoring Not Collecting

```bash
# Check gNMIc logs
docker logs clab-gnmi-clos-gnmic

# Check if devices are reachable from gNMIc
docker exec clab-gnmi-clos-gnmic ping -c 3 172.20.20.10

# Restart gNMIc
docker restart clab-gnmi-clos-gnmic
```

## Configuration Order Matters

Ansible playbooks must be run in this order:

1. **Interfaces** - Must be first (creates interfaces and IPs)
2. **LLDP** - Requires interfaces to exist
3. **BGP** - Requires interfaces and IPs to be configured

The `site.yml` playbook runs them in the correct order automatically.

## Simulating Different Scenarios

### Fresh Datacenter Deployment
```bash
./redeploy-datacenter.sh
# Simulates: New datacenter, zero-touch provisioning
```

### Configuration Changes Only
```bash
# Modify ansible/roles/*/defaults/main.yml
cd ansible
ansible-playbook site.yml
# Simulates: Day 2 operations, config updates
```

### Disaster Recovery
```bash
./destroy.sh
./deploy-datacenter.sh
# Simulates: Complete datacenter rebuild
# Monitoring data persists (30 days of metrics)
```

### Testing Automation
```bash
# Deploy without automation
./deploy.sh
sleep 120

# Manually configure via CLI
docker exec -it clab-gnmi-clos-spine1 sr_cli

# Then test Ansible can manage it
cd ansible
ansible-playbook site.yml
```

## Quick Reference

### One-Command Deployment
```bash
./deploy-datacenter.sh
```

### One-Command Redeploy
```bash
./redeploy-datacenter.sh
```

### Manual Step-by-Step
```bash
./deploy.sh
sleep 120
cd ansible
ansible-playbook site.yml
```

### Verify Everything
```bash
cd ansible
ansible-playbook playbooks/verify.yml
```

## What This Simulates

This lab setup simulates real-world datacenter network deployment:

1. **Hardware Installation**: Containerlab deploys switches
2. **Initial Boot**: Switches boot with minimal config (hostname + mgmt)
3. **Zero-Touch Provisioning**: Ansible configures everything
4. **Verification**: Automated checks confirm deployment
5. **Monitoring**: Telemetry collection starts automatically

This is how modern datacenters are deployed - infrastructure as code, automation-first, with minimal manual configuration.

## Benefits of This Approach

- ✅ **Realistic**: Matches real datacenter deployment workflows
- ✅ **Repeatable**: Same process every time
- ✅ **Testable**: Easy to test configuration changes
- ✅ **Documented**: Ansible playbooks are living documentation
- ✅ **Version Controlled**: All configs in git
- ✅ **Auditable**: Clear history of what was deployed when

## Next Steps

1. Deploy the datacenter: `./deploy-datacenter.sh`
2. Explore Grafana dashboards: http://localhost:3000
3. Modify Ansible variables in `ansible/roles/*/defaults/main.yml`
4. Redeploy to test changes: `./redeploy-datacenter.sh`
5. Create custom Grafana dashboards for your metrics

---

**Ready to deploy your datacenter network!** 🚀
