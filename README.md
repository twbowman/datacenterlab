# Production Network Testing Lab

A production-grade multi-vendor network testing lab for developing and validating datacenter automation, telemetry, and monitoring tools.

## Quick Links

- **Spec**: See `.kiro/specs/production-network-testing-lab/README.md` for complete requirements, design, and implementation tasks
- **Getting Started**: See `LAB-RESTART-GUIDE.md` for lab operations
- **Business Case**: See `GNMI-BUSINESS-CASE.md` for gNMI vs SNMP comparison
- **IP Addressing**: See `IP-ADDRESS-REFERENCE.md` for network addressing
- **Changelog**: See `CHANGELOG.md` for version history and migration guides

## Documentation

- `docs/guides/` - Operational guides (troubleshooting, testing, dashboards)
- `docs/reference/` - Reference documentation (metrics, OpenConfig)
- `docs/archive/` - Historical development documents

## Current Status

See `.kiro/specs/production-network-testing-lab/README.md` for current implementation status and roadmap.

## Overview

This lab provides a production-grade datacenter network with:
- **OSPF underlay** for fast convergence and next-hop reachability
- **BGP overlay** for application routing
- **Separate monitoring stack** that persists across network lab rebuilds
- **Ansible automation** using native SR Linux YANG paths via gNMI
- **All tools designed for production datacenter use** - only difference is containerized vs physical hardware

## Quick Start

```bash
# Deploy network lab
./deploy.sh

# Configure network with Ansible
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Deploy monitoring (optional, separate)
./deploy-monitoring.sh

# Verify configuration
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify.yml

# Or use the lab management script
./lab start
./lab configure
./lab verify
```

## Architecture

### Network Topology

```
           ┌─────────┐      ┌─────────┐
           │ spine1  │      │ spine2  │
           │ AS65001 │      │ AS65002 │
           └────┬────┘      └────┬────┘
                │                │
        ┌───────┼────────────────┼───────┐
        │       │                │       │
        │   ┌───┼────────────────┼───┐   │
        │   │   │                │   │   │
        │   │   │   ┌────────────┼───┼───┼───┐
        │   │   │   │            │   │   │   │
     ┌──┴───┴┐ ┌┴───┴──┐ ┌───────┴┐ ┌┴───┴───┐
     │ leaf1 │ │ leaf2 │ │ leaf3  │ │ leaf4  │
     │AS65011│ │AS65012│ │AS65013 │ │AS65014 │
     └───┬───┘ └───┬───┘ └───┬────┘ └───┬────┘
         │         │         │           │
     ┌───┴───┐ ┌───┴───┐ ┌───┴───┐  ┌───┴───┐
     │client1│ │client2│ │client3│  │client4│
     └───────┘ └───────┘ └───────┘  └───────┘
```

### Routing Architecture

**OSPF Underlay:**
- All point-to-point interfaces in area 0.0.0.0
- Provides fast convergence (sub-second)
- Handles next-hop reachability for BGP

**BGP Overlay:**
- eBGP fabric with unique AS per device
- Advertises loopback addresses
- Uses OSPF-learned routes for next-hop resolution

This is a standard production datacenter design used in enterprise environments.

### Components

**Network Lab** (`topology.yml`):
- 2 Spine switches (SR Linux)
- 4 Leaf switches (SR Linux)
- 4 Client nodes (netshoot)

**Monitoring Stack** (`topology-monitoring.yml` - separate):
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- gNMIc: http://localhost:9273/metrics

**Management Network:**
- 172.20.20.0/24 (shared between network and monitoring)
- Spines: 172.20.20.10-11
- Leafs: 172.20.20.21-24
- Clients: 172.20.20.31-34
- Monitoring: 172.20.20.2-5

## Deployment

### Network Lab

```bash
# Deploy network devices
./deploy.sh

# Configure with Ansible (OSPF + BGP)
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Verify
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify.yml

# Destroy
./destroy.sh
```

### Monitoring Stack (Optional)

```bash
# Deploy monitoring (separate from network)
./deploy-monitoring.sh

# Check status
./check-monitoring.sh

# Destroy monitoring
./destroy-monitoring.sh
```

### Lab Management Script

```bash
# Network lab
./lab start          # Deploy network
./lab configure      # Configure with Ansible
./lab verify         # Verify configuration
./lab stop           # Destroy network

# Monitoring
./lab mon-start      # Deploy monitoring
./lab mon-stop       # Destroy monitoring

# Status and access
./lab status         # Show all containers
./lab sr_cli spine1  # Access SR Linux CLI
./lab logs leaf1     # View logs
```

## Ansible Automation

### Configuration Method

Uses **srlinux_gnmi method** with native SR Linux YANG paths:
- gNMI protocol via gnmic CLI tool
- Native SR Linux paths (not OpenConfig)
- True idempotency via gNMI

**Why native paths?** SR Linux only supports OpenConfig for read operations (monitoring). Configuration requires native SR Linux YANG paths.

### Playbooks

```bash
cd ansible

# Full configuration (interfaces → LLDP → OSPF → BGP)
ansible-playbook -i inventory.yml site.yml

# Individual components
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/configure-interfaces.yml
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/configure-lldp.yml

# Verification
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/verify.yml
ansible-playbook -i inventory.yml methods/srlinux_gnmi/playbooks/verify-detailed.yml

# Use tags
ansible-playbook -i inventory.yml site.yml --tags interfaces
ansible-playbook -i inventory.yml site.yml --tags ospf
ansible-playbook -i inventory.yml site.yml --tags bgp
```

### Roles

- `gnmi_interfaces` - Interface and IP configuration
- `gnmi_lldp` - LLDP neighbor discovery
- `gnmi_ospf` - OSPF underlay routing
- `gnmi_bgp` - BGP overlay routing

See `ansible/README.md` and `ansible/methods/srlinux_gnmi/README.md` for details.

## Monitoring

### Separate Monitoring Stack

The monitoring stack runs independently from the network lab:
- Deploy once, leave running
- Survives network lab rebuilds
- Collects historical data
- Can be stopped when not needed

### Telemetry Collection

gNMIc collects from all switches:
- Interface statistics (10s interval)
- Interface operational state (30s)
- BGP neighbor statistics (30s)
- OSPF neighbor state (30s)
- LLDP neighbors (60s)
- System resources (30s)

### Data Storage

Prometheus stores metrics:
- 30-day retention
- 10-second scrape interval
- PromQL queries available

### Visualization

Grafana dashboards:
- Interface bandwidth
- BGP peer status
- OSPF adjacencies
- LLDP topology
- System health

### Link Utilization Analysis

Automated analysis tool to identify network issues:

```bash
# Generate test traffic (optional)
./lab generate-traffic

# Analyze link utilization
./lab analyze-links
```

The analysis identifies:
- **Overutilized links** (>80%) - potential bottlenecks
- **Underutilized links** (<10%) - wasted capacity
- **ECMP imbalances** - parallel paths with >20% difference
- **Actionable recommendations** - next steps to resolve issues

See `QUICK-START-LINK-ANALYSIS.md` for quick start guide and `LINK-UTILIZATION-TESTING.md` for detailed testing procedures.

## Verification

### Check Network Lab

```bash
# All network containers
docker ps --filter "name=clab-gnmi-clos"

# OSPF neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf neighbor"

# BGP neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"

# Routing table
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default route-table"

# Client connectivity
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.2.10
```

### Check Monitoring

```bash
# Monitoring containers
docker ps --filter "name=clab-monitoring"

# gNMIc metrics
curl -s http://localhost:9273/metrics | head -20

# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq
```

## Directory Structure

```
containerlab/
├── deploy.sh                     # Deploy network lab
├── destroy.sh                    # Destroy network lab
├── deploy-monitoring.sh          # Deploy monitoring stack
├── destroy-monitoring.sh         # Destroy monitoring stack
├── lab                           # Lab management script
├── check-monitoring.sh           # Check monitoring status
├── verify-network.sh             # Network verification
├── topology.yml                  # Network lab topology
├── topology-monitoring.yml       # Monitoring stack topology
├── analyze-link-utilization.py   # Link utilization analysis tool
├── generate-traffic.sh           # Traffic generator for testing
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── LAB-RESTART-GUIDE.md         # Deployment guide
├── QUICK-START-LINK-ANALYSIS.md # Link analysis quick start
├── LINK-UTILIZATION-TESTING.md  # Detailed testing guide
├── ansible/                      # Ansible automation
│   ├── site.yml                 # Main playbook (imports srlinux_gnmi)
│   ├── inventory.yml            # Device inventory
│   ├── methods/srlinux_gnmi/         # gNMI CLI method
│   │   ├── site.yml            # Method playbook
│   │   ├── roles/              # Configuration roles
│   │   │   ├── gnmi_interfaces/
│   │   │   ├── gnmi_lldp/
│   │   │   ├── gnmi_ospf/
│   │   │   └── gnmi_bgp/
│   │   ├── playbooks/          # Component playbooks
│   │   │   ├── verify.yml
│   │   │   └── verify-detailed.yml
│   │   ├── README.md           # Method documentation
│   │   └── UNDERLAY-ROUTING.md # Architecture docs
│   └── roles/                   # OpenConfig roles (read-only)
│       ├── openconfig_interfaces/
│       ├── openconfig_lldp/
│       ├── openconfig_ospf/
│       └── openconfig_bgp/
├── configs/                      # Minimal startup configs
│   ├── spine1/srlinux/config.json
│   ├── spine2/srlinux/config.json
│   └── leaf*/srlinux/config.json
├── monitoring/                   # Monitoring configuration
│   ├── grafana/provisioning/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   └── gnmic/
│       └── gnmic-config.yml
└── archive/                      # Historical reference
```

## Key Features

### Production-Grade Architecture
- OSPF underlay for fast convergence
- BGP overlay for scalability
- Separate control and data planes
- Standard enterprise datacenter design

### Automation-First
- All configuration via Ansible
- Infrastructure as code
- Repeatable deployments
- Version controlled

### Separate Monitoring
- Independent lifecycle from network
- Persistent historical data
- Survives network rebuilds
- Optional deployment

### Native SR Linux Support
- Uses SR Linux YANG paths
- gNMI protocol for configuration
- True idempotency
- OpenConfig for monitoring only

## Important Notes

### SR Linux and OpenConfig

SR Linux has limited OpenConfig support:
- ✅ OpenConfig GET (read) - Works for monitoring
- ❌ OpenConfig SET (write) - Not supported for configuration
- ✅ Native SR Linux paths - Required for all configuration

This is why we use the srlinux_gnmi method with native paths instead of OpenConfig roles for configuration.

### Monitoring Independence

The monitoring stack is separate from the network lab:
- Different topology files
- Independent deployment
- Shared management network
- Can run independently

Benefits:
- Keep monitoring running during network changes
- Historical data persists
- Cleaner separation of concerns
- Resource management flexibility

## Prerequisites

- OrbStack with containerlab VM (or Linux host)
- Docker (in lab VM)
- Containerlab >= 0.40.0 (in lab VM)
- Ansible >= 2.9 (in lab VM)
- gnmic CLI tool (in lab VM)
- Python 3 with requests library (for link analysis tool)

All commands in this README assume you're running inside the lab VM (e.g., `orb -m clab` to enter the VM).

### Installing Python Dependencies

For the link utilization analysis tool, install the requests library:

```bash
# Inside orb VM
sudo apt update && sudo apt install -y python3-requests
```

Alternatively, use a virtual environment:
```bash
python3 -m venv ~/venv-lab
source ~/venv-lab/bin/activate
pip install -r requirements.txt
```

## Documentation

- `README.md` - This file (overview)
- `LAB-RESTART-GUIDE.md` - Deployment procedures
- `TELEMETRY-STRATEGY.md` - Native vs OpenConfig paths strategy for multi-vendor support
- `ansible/README.md` - Ansible automation guide
- `ansible/methods/srlinux_gnmi/README.md` - gNMI CLI method details (native SR Linux paths)
- `ansible/methods/srlinux_gnmi/UNDERLAY-ROUTING.md` - Routing architecture
- `ROUTING-PROTOCOL-DASHBOARDS.md` - OSPF and BGP monitoring dashboards
- `LINK-UTILIZATION-TESTING.md` - Link analysis and monitoring
- `archive/README.md` - Archived files

## Troubleshooting

### Network Lab Issues

```bash
# Check containers
docker ps --filter "name=clab-gnmi-clos"

# Check device logs
docker logs clab-gnmi-clos-spine1

# Verify gNMI connectivity
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities
```

### Ansible Issues

```bash
# Test connectivity
ansible -i ansible/inventory.yml all -m ping

# Run with verbose output
ansible-playbook -i ansible/inventory.yml ansible/site.yml -vvv

# Check diagnostics
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify-detailed.yml
```

### Monitoring Issues

```bash
# Check monitoring containers
docker ps --filter "name=clab-monitoring"

# Check gNMIc logs
docker logs clab-monitoring-gnmic

# Test metrics endpoint
curl http://localhost:9273/metrics
```

## License

This project is provided as-is for educational and testing purposes.

## Quick Start

```bash
# In the orb VM
orb -m clab
cd /path/to/containerlab

# Deploy fresh datacenter
./deploy-datacenter.sh

# Or full redeploy (destroy + deploy)
./redeploy-datacenter.sh

# Access Grafana
open http://localhost:3000  # admin/admin
```

## What Gets Deployed

### Network Topology

```
           ┌─────────┐      ┌─────────┐
           │ spine1  │      │ spine2  │
           └────┬────┘      └────┬────┘
                │                │
        ┌───────┼────────────────┼───────┐
        │       │                │       │
        │   ┌───┼────────────────┼───┐   │
        │   │   │                │   │   │
        │   │   │   ┌────────────┼───┼───┼───┐
        │   │   │   │            │   │   │   │
     ┌──┴───┴┐ ┌┴───┴──┐ ┌───────┴┐ ┌┴───┴───┐
     │ leaf1 │ │ leaf2 │ │ leaf3  │ │ leaf4  │
     └───┬───┘ └───┬───┘ └───┬────┘ └───┬────┘
         │         │         │           │
     ┌───┴───┐ ┌───┴───┐ ┌───┴───┐  ┌───┴───┐
     │client1│ │client2│ │client3│  │client4│
     └───────┘ └───────┘ └───────┘  └───────┘
```

**Connections:**
- Each leaf is dual-homed to both spines (full redundancy)
- spine1 → all 4 leafs (ethernet-1/1 through ethernet-1/4)
- spine2 → all 4 leafs (ethernet-1/1 through ethernet-1/4)
- Each client connects to one leaf

- 2 Spine switches (SR Linux)
- 4 Leaf switches (SR Linux)
- 4 Client nodes (netshoot)
- 3 Monitoring containers (Grafana, Prometheus, gNMIc)

### Components

**Spine Switches:**
- spine1: 172.20.20.10 (BGP AS 65001, Loopback 10.0.0.1)
- spine2: 172.20.20.11 (BGP AS 65002, Loopback 10.0.0.2)

**Leaf Switches:**
- leaf1: 172.20.20.21 (BGP AS 65011, Loopback 10.0.0.11)
- leaf2: 172.20.20.22 (BGP AS 65012, Loopback 10.0.0.12)
- leaf3: 172.20.20.23 (BGP AS 65013, Loopback 10.0.0.13)
- leaf4: 172.20.20.24 (BGP AS 65014, Loopback 10.0.0.14)

**Client Nodes:**
- client1: 10.10.1.10/24 (connected to leaf1)
- client2: 10.10.2.10/24 (connected to leaf2)
- client3: 10.10.3.10/24 (connected to leaf3)
- client4: 10.10.4.10/24 (connected to leaf4)

**Monitoring Stack:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- gNMIc: http://172.20.20.5:9273/metrics

## How It Works

### Zero-Touch Provisioning Simulation

1. **Minimal Boot Config**: Switches boot with only hostname + gNMI enabled
2. **Ansible Configuration**: All network config applied via Ansible
3. **Verification**: Automated checks confirm deployment
4. **Monitoring**: Telemetry collection starts automatically

This matches real datacenter deployments - infrastructure as code, automation-first.

### Configuration Flow

```
Containerlab Deploy
    ↓
Switches Boot (minimal config)
    ↓
Ansible Configures:
  - Interfaces
  - LLDP
  - BGP
    ↓
Verification
    ↓
Monitoring Active
```

## Deployment Scripts

### deploy-datacenter.sh
Deploys and configures a fresh datacenter:
1. Deploys containerlab topology
2. Waits for devices to boot (120 seconds)
3. Configures via Ansible (interfaces → LLDP → BGP)
4. Verifies configuration

### redeploy-datacenter.sh
Full redeploy (destroy + deploy):
1. Destroys existing lab
2. Runs deploy-datacenter.sh

## Manual Deployment

If you want to run steps manually:

```bash
# 1. Deploy topology
./deploy.sh

# 2. Wait for boot
sleep 120

# 3. Configure via Ansible
cd ansible
ansible-playbook site.yml

# 4. Verify
ansible-playbook playbooks/verify.yml
```

## Ansible Automation

All network configuration is done via Ansible using OpenConfig YANG models:

### Playbooks

```bash
cd ansible

# Run all configuration
ansible-playbook site.yml

# Individual playbooks
ansible-playbook playbooks/configure-interfaces.yml
ansible-playbook playbooks/configure-lldp.yml
ansible-playbook playbooks/configure-bgp.yml
ansible-playbook playbooks/verify.yml

# Use tags
ansible-playbook site.yml --tags interfaces
ansible-playbook site.yml --tags lldp
ansible-playbook site.yml --tags bgp
ansible-playbook site.yml --tags verify
```

### Roles

Configuration is organized into OpenConfig roles:
- `openconfig_interfaces` - Interface configuration
- `openconfig_lldp` - LLDP configuration
- `openconfig_bgp` - BGP configuration

See `ansible/README.md` for details.

## Monitoring

### gNMIc Telemetry Collection

gNMIc collects telemetry from all 6 switches:
- Interface statistics (10s interval)
- BGP statistics (30s interval)
- LLDP neighbors (60s interval)
- System resources (30s interval)

### Prometheus Storage

Prometheus stores metrics with 30-day retention:
- Scrapes gNMIc every 10 seconds
- Persistent storage survives lab restarts
- PromQL queries for analysis

### Grafana Visualization

Grafana provides dashboards:
- Interface bandwidth utilization
- BGP peer status
- LLDP topology
- System health

Access: http://localhost:3000 (admin/admin)

## Verification

### Check Deployment

```bash
# Check all containers running
docker ps --filter "name=clab-gnmi-clos"

# Should see 13 containers:
# - 2 spines, 4 leafs, 4 clients, 3 monitoring
```

### Check BGP

```bash
# Spine should have 4 BGP neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"

# Leaf should have 2 BGP neighbors
docker exec clab-gnmi-clos-leaf1 sr_cli "show network-instance default protocols bgp neighbor"
```

### Check LLDP

```bash
# Spine should see 4 LLDP neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"

# Leaf should see 3 LLDP neighbors (2 spines + 1 client)
docker exec clab-gnmi-clos-leaf1 sr_cli "show system lldp neighbor"
```

### Check Connectivity

```bash
# Client1 should ping Client2
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.2.10

# Client1 should ping Client3
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.3.10
```

### Check Monitoring

```bash
# Check gNMIc is collecting
curl http://172.20.20.5:9273/metrics | grep gnmic_interface

# Check Prometheus has data
curl 'http://172.20.20.3:9090/api/v1/query?query=up'
```

## Directory Structure

```
containerlab/
├── deploy-datacenter.sh          # Main deployment script
├── redeploy-datacenter.sh        # Full redeploy script
├── deploy.sh                     # Containerlab deploy
├── destroy.sh                    # Containerlab destroy
├── topology.yml                  # Lab topology
├── LAB-RESTART-GUIDE.md         # Deployment guide
├── DATACENTER-DEPLOYMENT.md     # Overview
├── README.md                     # This file
├── ansible/                      # Ansible automation
│   ├── site.yml                 # Main playbook
│   ├── inventory.yml            # Device inventory
│   ├── playbooks/               # Component playbooks
│   │   ├── configure-interfaces.yml
│   │   ├── configure-lldp.yml
│   │   ├── configure-bgp.yml
│   │   └── verify.yml
│   └── roles/                   # OpenConfig roles
│       ├── openconfig_interfaces/
│       ├── openconfig_lldp/
│       └── openconfig_bgp/
├── configs/                      # Minimal startup configs
│   ├── spine1/srlinux/config.json
│   ├── spine2/srlinux/config.json
│   ├── leaf1/srlinux/config.json
│   ├── leaf2/srlinux/config.json
│   ├── leaf3/srlinux/config.json
│   └── leaf4/srlinux/config.json
├── monitoring/                   # Monitoring stack
│   ├── grafana/
│   │   ├── provisioning/        # Datasources & dashboards
│   │   └── data/                # Persistent data
│   ├── prometheus/
│   │   ├── prometheus.yml       # Prometheus config
│   │   └── data/                # Persistent data (30 days)
│   └── gnmic/
│       └── gnmic-config.yml     # gNMIc telemetry config
└── archive/                      # Archived files
    ├── scripts/                 # Old scripts
    ├── docs/                    # Old documentation
    └── README.md                # Archive index
```

## Prerequisites

- OrbStack (for macOS) or Linux host
- Docker >= 20.10
- Containerlab >= 0.40.0
- Ansible >= 2.9

```bash
# Install Containerlab
bash -c "$(curl -sL https://get.containerlab.dev)"

# Install Ansible (in orb VM)
sudo apt update
sudo apt install -y ansible
```

## Documentation

- `LAB-RESTART-GUIDE.md` - Detailed deployment procedures
- `DATACENTER-DEPLOYMENT.md` - Overview of datacenter simulation
- `ansible/README.md` - Ansible automation guide
- `ansible/QUICK-START.md` - Quick start for Ansible
- `ansible/ROLES-README.md` - Role-based structure
- `archive/README.md` - Archived files index

## Use Cases

### Fresh Datacenter Deployment
```bash
./deploy-datacenter.sh
```
Simulates bringing up a new datacenter from scratch.

### Disaster Recovery
```bash
./redeploy-datacenter.sh
```
Simulates rebuilding after a disaster. Monitoring data persists.

### Configuration Testing
```bash
# Modify ansible/roles/*/defaults/main.yml
./redeploy-datacenter.sh
```
Test configuration changes in a fresh environment.

### Automation Development
```bash
./deploy.sh
sleep 120
# Develop and test Ansible playbooks
cd ansible
ansible-playbook site.yml
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

### BGP Not Establishing

```bash
# Check interfaces are configured first
docker exec clab-gnmi-clos-spine1 sr_cli "show interface brief"

# Check BGP configuration
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp"
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

See `LAB-RESTART-GUIDE.md` for detailed troubleshooting.

## What This Simulates

This lab simulates real-world datacenter network deployment:

1. **Hardware Installation**: Containerlab deploys switches
2. **Initial Boot**: Switches boot with minimal config (hostname + mgmt)
3. **Zero-Touch Provisioning**: Ansible configures everything
4. **Verification**: Automated checks confirm deployment
5. **Monitoring**: Telemetry collection starts automatically

This is how modern datacenters are deployed - infrastructure as code, automation-first, with minimal manual configuration.

## Benefits

- ✅ **Realistic**: Matches real datacenter deployment workflows
- ✅ **Repeatable**: Same process every time
- ✅ **Testable**: Easy to test configuration changes
- ✅ **Documented**: Ansible playbooks are living documentation
- ✅ **Version Controlled**: All configs in git
- ✅ **Auditable**: Clear history of what was deployed when

## License

This project is provided as-is for educational and testing purposes.
