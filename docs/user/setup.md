# Setup Guide

This guide provides step-by-step instructions for setting up the Production Network Testing Lab environment.

## Architecture

- **Development machine** (macOS ARM or any OS): Edit code, run git, use the `./lab` wrapper
- **Remote lab server** (x86_64 Linux): Runs containerlab, Docker, Ansible, monitoring stack
- The `./lab` wrapper handles rsync and SSH execution transparently

## Prerequisites

### Local Machine (macOS / Linux / Windows)

- **SSH key** for connecting to the remote server
- **rsync** (pre-installed on macOS and most Linux)
- **Python 3.8+** (optional, for local validation scripts)

### Remote Server (x86_64 Linux)

Recommended: Hetzner Cloud CPX31 or CPX41 (Ubuntu 22.04+)

The `./lab setup` command installs everything automatically:
- Docker
- Containerlab
- gNMIc
- Ansible + Python dependencies

### Network Device Images

- **SR Linux** (Nokia): `ghcr.io/nokia/srlinux:latest` — freely available
- **SONiC**: `docker-sonic-vs:latest` — x86_64 only
- **Arista cEOS**: requires manual download from Arista
- **Juniper cRPD**: requires license from Juniper

## Quick Start

### 1. Configure Remote Server Connection

```bash
cp .env.example .env
# Edit .env with your server IP, SSH key, etc.
```

### 2. Provision the Remote Server

```bash
./lab setup
```

This runs `scripts/remote-setup.sh` on the server, installing Docker, containerlab, gnmic, Ansible, and Python deps.

### 3. Deploy the Lab

```bash
./lab deploy              # default vendor (from .env)
./lab deploy srlinux      # SR Linux topology
./lab deploy sonic        # SONiC topology
```

### 4. Check Status

```bash
./lab status
```

### 5. Configure the Fabric

```bash
./lab configure
```

### 6. Access Monitoring

```bash
./lab tunnel
# Then open http://localhost:3000 (Grafana)
```

## Verification

After `./lab setup`, verify the remote server:

```bash
./lab exec "docker --version"
./lab exec "containerlab version"
./lab exec "gnmic version"
./lab exec "ansible --version"
```

## Platform-Specific Notes

### macOS ARM (Apple Silicon)

SONiC VS images and some NOS containers are x86_64 only. The remote execution model solves this — you develop locally and the lab runs on a remote x86_64 server.

All lab commands go through `./lab`:
```bash
./lab deploy          # deploy topology
./lab configure       # run Ansible
./lab validate        # run validation
./lab ssh             # SSH to server
./lab exec "cmd"      # run arbitrary command
```

### Linux x86_64

Same workflow via `./lab`, or you can run commands directly on the server.

## Troubleshooting

### Issue: "./lab" fails with "Missing .env file"

```bash
cp .env.example .env
# Edit .env with your server details
```

### Issue: SSH connection refused

- Verify `LAB_HOST` IP in `.env`
- Verify `LAB_SSH_KEY` path points to your private key
- Ensure the server is running and SSH is enabled

### Issue: "containerlab: command not found" on remote

```bash
./lab setup   # re-run provisioning
```

### Issue: SR Linux image pull fails

```bash
./lab exec "docker pull ghcr.io/nokia/srlinux:latest"
```

### Issue: Devices fail to boot

SR Linux can take 2-3 minutes to fully boot.

```bash
./lab exec "docker logs clab-gnmi-clos-spine1"
# Look for "All applications started successfully"
```

### Issue: Disk space on remote server

```bash
./lab exec "df -h"
./lab exec "docker system prune -a"
```

## Hardware Requirements

### Remote Server (Recommended)

- **CPU**: 4+ cores (8 recommended for multi-vendor)
- **RAM**: 8 GB (16 GB recommended)
- **Disk**: 40 GB+ SSD
- Hetzner CPX31 (4 vCPU, 8 GB) or CPX41 (8 vCPU, 16 GB)

### Resource Usage

| Topology | RAM | Disk | Containers |
|----------|-----|------|------------|
| Small (2 spines, 4 leafs) | ~4 GB | ~10 GB | 6 |
| + Monitoring stack | +2 GB | +5 GB | +3 |
| + Client nodes | +1 GB | +1 GB | +4 |

## Security Considerations

### Default Credentials

Lab uses default credentials (for isolated lab environments only):

- **SR Linux**: admin / NokiaSrl1!
- **Grafana**: admin / admin
- **Prometheus**: No authentication

### Network Isolation

Lab containers run on isolated Docker networks on the remote server. Access monitoring via SSH tunnels (`./lab tunnel`).

## Next Steps

1. **Configure devices**: `./lab configure`
2. **Set up monitoring**: Included in topology, access via `./lab tunnel`
3. **Run validation**: `./lab validate`
4. **Explore dashboards**: http://localhost:3000 (after `./lab tunnel`)
