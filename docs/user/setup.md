# Setup Guide

This guide provides step-by-step instructions for setting up the Production Network Testing Lab environment.

## Prerequisites

### Required Software

**macOS with ARM Processor (Apple Silicon):**
- **ORB** (Orbstack) - Required for running containerlab on ARM Macs
- **Docker** - Included with ORB
- **Python 3.8+** - For validation and analysis tools

**Linux x86_64:**
- **Docker** >= 20.10
- **Containerlab** >= 0.40.0
- **Ansible** >= 2.9
- **Python 3.8+**

### Network Device Images

The lab supports multiple vendor network operating systems:

- **SR Linux** (Nokia): `ghcr.io/nokia/srlinux:latest`
- **Arista cEOS**: `ceos:4.28.0F` (requires manual download from Arista)
- **SONiC**: `docker-sonic-vs:latest` (requires build or download)
- **Juniper cRPD**: `crpd:23.2R1` (requires license from Juniper)

**Note**: SR Linux is freely available and works out of the box. Other vendors require registration, licenses, or manual builds.

## Installation

### macOS with ARM (Apple Silicon)

#### 1. Install ORB

```bash
# Install ORB (if not already installed)
brew install orbstack

# Start ORB
orb start

# Create containerlab machine (if not exists)
orb create ubuntu clab
```

#### 2. Enter ORB VM

All subsequent commands run inside the ORB VM:

```bash
orb -m clab
```

#### 3. Install Containerlab

```bash
# Inside ORB VM
bash -c "$(curl -sL https://get.containerlab.dev)"
```

#### 4. Install Ansible

```bash
# Inside ORB VM
sudo apt update
sudo apt install -y ansible python3-pip

# Install Ansible collections
ansible-galaxy collection install ansible.netcommon
ansible-galaxy collection install ansible.utils
```

#### 5. Install gNMIc

```bash
# Inside ORB VM
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"
```

#### 6. Install Python Dependencies

```bash
# Inside ORB VM
cd /path/to/containerlab
pip3 install -r requirements.txt
```

### Linux x86_64

#### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

Log out and back in for group changes to take effect.

#### 2. Install Containerlab

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

#### 3. Install Ansible

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ansible python3-pip

# Install Ansible collections
ansible-galaxy collection install ansible.netcommon
ansible-galaxy collection install ansible.utils
```

#### 4. Install gNMIc

```bash
bash -c "$(curl -sL https://get-gnmic.openconfig.net)"
```

#### 5. Install Python Dependencies

```bash
cd /path/to/containerlab
pip3 install -r requirements.txt
```

## Verification

### Verify Installation

```bash
# Check Docker
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Containerlab
containerlab version
# Expected: containerlab version 0.40.0 or higher

# Check Ansible
ansible --version
# Expected: ansible 2.9.0 or higher

# Check gNMIc
gnmic version
# Expected: version info

# Check Python
python3 --version
# Expected: Python 3.8.0 or higher
```

### Test Docker Access

```bash
# Should list running containers (may be empty)
docker ps

# Should show Docker info
docker info
```

### Pull SR Linux Image

```bash
# Pull the SR Linux container image
docker pull ghcr.io/nokia/srlinux:latest
```

This may take several minutes depending on your internet connection.

## Quick Start Test

Deploy a minimal test topology to verify everything works:

```bash
# Clone or navigate to the lab directory
cd /path/to/containerlab

# Deploy the lab (macOS ARM: use orb -m clab prefix)
# macOS ARM:
orb -m clab sudo containerlab deploy -t topology.yml

# Linux:
sudo containerlab deploy -t topology.yml

# Wait for devices to boot (2-3 minutes)
sleep 180

# Check devices are running
docker ps --filter "name=clab-gnmi-clos"

# Destroy the lab
# macOS ARM:
orb -m clab sudo containerlab destroy -t topology.yml

# Linux:
sudo containerlab destroy -t topology.yml
```

If this works, your environment is ready!

## Platform-Specific Notes

### macOS ARM (Apple Silicon)

**Critical**: All containerlab, docker, and ansible commands must be prefixed with `orb -m clab` to run in the ORB VM context.

**Command Examples:**
```bash
# Deploy topology
orb -m clab sudo containerlab deploy -t topology.yml

# Run Ansible
orb -m clab ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Access device CLI
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli "show version"

# Check containers
orb -m clab docker ps
```

**File Access:**
- Files in your workspace are automatically synced to the ORB VM
- Edit files locally with your preferred editor
- Run commands in the ORB VM context

**Why ORB?**
- Containerlab and SR Linux require x86_64 architecture
- ARM Macs need emulation via ORB's Linux VM
- ORB provides transparent file sync and networking

### Linux x86_64

No special prefixes needed. Run commands directly:

```bash
# Deploy topology
sudo containerlab deploy -t topology.yml

# Run Ansible
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Access device CLI
docker exec clab-gnmi-clos-spine1 sr_cli "show version"
```

## Troubleshooting

### Issue: "containerlab: command not found"

**Solution**: Containerlab is not in PATH.

```bash
# Find containerlab
which containerlab

# If not found, reinstall
bash -c "$(curl -sL https://get.containerlab.dev)"

# Or add to PATH
export PATH=$PATH:/usr/local/bin
```

### Issue: "permission denied" when running docker

**Solution**: User not in docker group.

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Issue: "Cannot connect to the Docker daemon"

**Solution**: Docker is not running.

```bash
# macOS with ORB
orb start

# Linux
sudo systemctl start docker
sudo systemctl enable docker
```

### Issue: SR Linux image pull fails

**Solution**: Network or registry issue.

```bash
# Try with explicit registry
docker pull ghcr.io/nokia/srlinux:latest

# Check Docker Hub login if needed
docker login ghcr.io
```

### Issue: Devices fail to boot

**Symptoms**: Containers start but devices don't respond to gNMI.

**Solution**: Wait longer. SR Linux can take 2-3 minutes to fully boot.

```bash
# Check container logs
docker logs clab-gnmi-clos-spine1

# Look for "All applications started successfully"
```

### Issue: ORB VM runs out of disk space

**Solution**: Increase ORB VM disk size.

```bash
# Check disk usage
orb -m clab df -h

# Increase VM disk (in ORB settings)
# Or clean up old containers/images
orb -m clab docker system prune -a
```

### Issue: Ansible connection failures

**Symptoms**: "Failed to connect to device" errors.

**Solution**: Verify gNMI is enabled and reachable.

```bash
# Check device is running
docker ps --filter "name=clab-gnmi-clos-spine1"

# Test gNMI connection
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities

# Check device logs
docker logs clab-gnmi-clos-spine1
```

## Next Steps

Once your environment is set up:

1. **Read the Configuration Guide**: `docs/user/configuration.md`
2. **Deploy Your First Lab**: Follow the examples in `topologies/examples/`
3. **Configure Devices**: Use Ansible playbooks in `ansible/`
4. **Set Up Monitoring**: Deploy the monitoring stack
5. **Explore Dashboards**: Access Grafana at http://localhost:3000

## Getting Help

If you encounter issues not covered here:

1. Check the **Troubleshooting Guide**: `docs/user/troubleshooting.md`
2. Review **Containerlab Documentation**: https://containerlab.dev
3. Check **SR Linux Documentation**: https://learn.srlinux.dev
4. Review project issues on GitHub

## Hardware Requirements

### Minimum Requirements

- **CPU**: 4 cores (8 recommended)
- **RAM**: 8 GB (16 GB recommended)
- **Disk**: 20 GB free space (50 GB recommended)
- **Network**: Internet connection for image downloads

### Recommended for Multi-Vendor Labs

- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disk**: 50+ GB free space
- **Network**: Fast internet for large image downloads

### Resource Usage by Topology Size

**Small Lab** (2 spines, 4 leafs):
- ~4 GB RAM
- ~10 GB disk
- 6 containers

**Medium Lab** (4 spines, 8 leafs):
- ~8 GB RAM
- ~20 GB disk
- 12 containers

**Large Lab** (8 spines, 16 leafs):
- ~16 GB RAM
- ~40 GB disk
- 24 containers

**Note**: Add monitoring stack (Grafana, Prometheus, gNMIc) requires additional ~2 GB RAM.

## Security Considerations

### Default Credentials

The lab uses default credentials for convenience:

- **SR Linux**: admin / NokiaSrl1!
- **Grafana**: admin / admin
- **Prometheus**: No authentication

**Warning**: These are insecure defaults suitable only for isolated lab environments. Never use these credentials in production.

### Network Isolation

Lab containers run on isolated Docker networks:

- Management network: 172.20.20.0/24
- Data plane networks: 10.x.x.x/31 point-to-point links

Containers are not directly accessible from outside the Docker host unless ports are explicitly published.

### Production Deployment

When adapting lab configurations for production:

1. Change all default credentials
2. Enable authentication on all services
3. Use TLS/SSL for all connections
4. Implement proper access controls
5. Follow your organization's security policies

See the **Production Datacenter Compatibility** section in the design document for migration guidance.
