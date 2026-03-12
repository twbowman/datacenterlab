# Multi-Vendor Network Lab Deployment

This guide explains how to deploy and manage multi-vendor network topologies using the enhanced deployment scripts.

## Overview

The multi-vendor deployment system supports:
- **SR Linux** (Nokia)
- **Arista cEOS** (Arista)
- **SONiC** (Dell/Microsoft)
- **Juniper cRPD** (Juniper)

## Quick Start

### Deploy Multi-Vendor Lab

```bash
./deploy-multi-vendor.sh topology-multi-vendor.yml
```

### Destroy Multi-Vendor Lab

```bash
./destroy-multi-vendor.sh topology-multi-vendor.yml
```

## Features

### 1. Topology Validation

Before deployment, the topology is automatically validated:
- Required fields (kind, image)
- Supported device types
- Circular dependencies in links
- Specific error messages for failures

Manual validation:
```bash
python3 scripts/validate-topology.py topology-multi-vendor.yml
```

### 2. Vendor-Specific Boot Times

The deployment script automatically calculates boot time based on vendors:
- SR Linux: 60 seconds
- Arista cEOS: 90 seconds
- SONiC: 120 seconds
- Juniper cRPD: 90 seconds

### 3. Health Checks

After deployment, all devices are checked for gNMI reachability.

### 4. Cleanup Verification

The destroy script verifies all resources are removed:
- Containers
- Networks
- Volumes

## Topology Structure


### Example Multi-Vendor Topology

```yaml
name: multi-vendor-lab

topology:
  groups:
    srlinux-router:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
    
    arista-router:
      kind: arista_ceos
      image: ceos:4.28.0F
    
    sonic-router:
      kind: sonic-vs
      image: docker-sonic-vs:latest
    
    juniper-router:
      kind: juniper_crpd
      image: crpd:23.2R1

  nodes:
    srl-spine1:
      group: srlinux-router
      labels:
        vendor: nokia
        role: spine
    
    arista-leaf1:
      group: arista-router
      labels:
        vendor: arista
        role: leaf
```

## Supported Vendors

### SR Linux (Nokia)
- **Kind**: `nokia_srlinux`
- **Image**: `ghcr.io/nokia/srlinux:latest`
- **Interface naming**: `ethernet-1/1`
- **gNMI port**: 57400

### Arista cEOS
- **Kind**: `arista_ceos`
- **Image**: `ceos:4.28.0F`
- **Interface naming**: `Ethernet1`
- **gNMI port**: 57400

### SONiC
- **Kind**: `sonic-vs`
- **Image**: `docker-sonic-vs:latest`
- **Interface naming**: `Ethernet0`
- **gNMI port**: 57400

### Juniper cRPD
- **Kind**: `juniper_crpd`
- **Image**: `crpd:23.2R1`
- **Interface naming**: `eth1`
- **gNMI port**: 57400

## Troubleshooting

### Validation Errors

If validation fails, check:
1. All nodes have required `kind` field
2. Device kinds are supported
3. All link endpoints reference existing nodes
4. No self-loops in links

### Health Check Failures

If devices fail health checks:
1. Wait longer - devices may still be booting
2. Check container logs: `docker logs clab-<lab-name>-<device-name>`
3. Verify gNMI port is accessible: `nc -zv <ip> 57400`

### Cleanup Issues

If cleanup verification fails:
```bash
# Force remove containers
docker rm -f $(docker ps -aq --filter name=clab-<lab-name>)

# Force remove networks
docker network rm $(docker network ls --filter name=clab-<lab-name> -q)

# Force remove volumes
docker volume rm $(docker volume ls --filter name=clab-<lab-name> -q)
```

## Next Steps

After deployment:
1. Configure devices with Ansible (see ansible/README.md)
2. Deploy monitoring stack (see monitoring/README.md)
3. Run validation checks (see validation/README.md)
