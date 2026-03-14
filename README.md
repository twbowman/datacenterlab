# Production Network Testing Lab

A production-grade multi-vendor network testing lab for developing and validating datacenter automation, telemetry, and monitoring tools.

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

## Documentation

Complete documentation is organized in the `docs/` directory:

- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[Getting Started](docs/user/setup.md)** - Initial setup and deployment
- **[Lab Operations](docs/user/LAB-RESTART-GUIDE.md)** - Day-to-day lab management
- **[Configuration Guide](docs/user/configuration.md)** - Network configuration
- **[Monitoring Guide](docs/user/monitoring.md)** - Telemetry and dashboards
- **[Troubleshooting](docs/user/troubleshooting.md)** - Common issues and solutions
- **[Developer Guide](docs/developer/contributing.md)** - Contributing and testing
- **[Architecture](docs/developer/architecture.md)** - System design and components

## Overview

This lab provides a production-grade datacenter network with:
- **OSPF underlay** for fast convergence and next-hop reachability
- **iBGP overlay** with route reflectors for application routing and EVPN
- **Separate monitoring stack** that persists across network lab rebuilds
- **Ansible automation** using native SR Linux YANG paths via gNMI
- **All tools designed for production datacenter use** - only difference is containerized vs physical hardware

## Architecture

### Network Topology

```
           ┌─────────┐      ┌─────────┐
           │ spine1  │      │ spine2  │
           │  (RR)   │      │  (RR)   │
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
     │AS65000│ │AS65000│ │AS65000 │ │AS65000 │
     └───┬───┘ └───┬───┘ └───┬────┘ └───┬────┘
         │         │         │           │
     ┌───┴───┐ ┌───┴───┐ ┌───┴───┐  ┌───┴───┐
     │client1│ │client2│ │client3│  │client4│
     └───────┘ └───────┘ └───────┘  └───────┘
```

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
- Network Congestion Analysis
- EVPN/VXLAN Stability

Access Grafana at http://localhost:3000 (admin/admin)

## Traffic Testing

Separate Ansible-based fabric load testing using iperf3 across all client nodes via EVPN/VXLAN.

All 4 clients share the same L2 subnet (10.10.100.0/24) bridged across the fabric via mac-vrf-100 (VNI 10100). Traffic between clients on different leafs traverses the full leaf-spine-leaf VXLAN path.

```bash
# Quick 30-second validation
orb -m clab ansible-playbook -i traffic-testing/inventory.yml traffic-testing/playbooks/quick-test.yml

# Full 5-minute mesh test
orb -m clab ansible-playbook -i traffic-testing/inventory.yml traffic-testing/playbooks/full-mesh-traffic.yml

# Stress test
orb -m clab ansible-playbook -i traffic-testing/inventory.yml traffic-testing/playbooks/stress-test.yml
```

See [Traffic Testing README](traffic-testing/README.md) for details.

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

# Client connectivity (via EVPN/VXLAN)
docker exec clab-gnmi-clos-client1 ping -c 3 10.10.100.12
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

## Prerequisites

- OrbStack with containerlab VM (or Linux host)
- Docker (in lab VM)
- Containerlab >= 0.40.0 (in lab VM)
- Ansible >= 2.9 (in lab VM)
- gnmic CLI tool (in lab VM)

All commands in this README assume you're running inside the lab VM (e.g., `orb -m clab` to enter the VM).

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

See [Troubleshooting Guide](docs/user/troubleshooting.md) for more details.

## Contributing

See [Developer Guide](docs/developer/contributing.md) for information on:
- Development setup
- Running tests
- CI/CD pipeline
- Code standards
- Submitting changes

### Code Quality

This project uses comprehensive linting and security scanning:
- **Python**: Ruff (linter/formatter) + Mypy (type checking)
- **YAML**: yamllint
- **Ansible**: ansible-lint
- **Shell**: ShellCheck
- **Security**: Bandit, Trivy, Gitleaks

Run all checks locally:
```bash
./scripts/run-linters.sh
```

See [Linting & Security Guide](docs/LINTING-SECURITY.md) for details.

## License

This project is provided as-is for educational and testing purposes.
