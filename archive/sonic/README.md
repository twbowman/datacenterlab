# SONiC Configuration Files

SONiC configuration for CLOS topology with BGP underlay.

## Configuration Structure

Each switch has a `config_db.json` file that defines:
- Device metadata (hostname, ASN, type)
- Loopback interfaces
- Physical interfaces and IP addresses
- BGP neighbors
- VLANs (for leaf switches)

## Topology

### Spines
- **spine1**: AS 65001, Loopback 10.0.0.1
- **spine2**: AS 65002, Loopback 10.0.0.2

### Leafs
- **leaf1**: AS 65011, Loopback 10.0.0.11, VLAN 10 (10.10.1.0/24)
- **leaf2**: AS 65012, Loopback 10.0.0.12, VLAN 20 (10.10.2.0/24)
- **leaf3**: AS 65013, Loopback 10.0.0.13, VLAN 30 (10.10.3.0/24)
- **leaf4**: AS 65014, Loopback 10.0.0.14, VLAN 40 (10.10.4.0/24)

## Interface Mapping

### Spine1 to Leafs
- Ethernet0 (10.1.1.0/31) → leaf1
- Ethernet4 (10.1.2.0/31) → leaf2
- Ethernet8 (10.1.3.0/31) → leaf3
- Ethernet12 (10.1.4.0/31) → leaf4

### Spine2 to Leafs
- Ethernet0 (10.2.1.0/31) → leaf1
- Ethernet4 (10.2.2.0/31) → leaf2
- Ethernet8 (10.2.3.0/31) → leaf3
- Ethernet12 (10.2.4.0/31) → leaf4

### Leaf to Clients
- Ethernet8 on each leaf connects to client subnet

## Using SONiC Configs

### Switch a node to SONiC

Edit `topology.yml` and change the kind:

```yaml
spine1:
  kind: sonic    # Changed from 'frr'
  mgmt-ipv4: 172.20.20.10
  binds:
    - ./sonic/spine1:/etc/sonic  # Changed from ./frr/spine1:/etc/frr
```

### Switch all nodes to SONiC

Change the image in the kinds section:

```yaml
kinds:
  frr:
    image: docker-sonic-vs:latest  # Changed from frrouting/frr:latest
```

And update all binds from `/etc/frr` to `/etc/sonic`.

## SONiC Commands

```bash
# Access SONiC CLI
docker exec -it clab-gnmi-clos-spine1 bash

# Show config
show runningconfiguration all

# Show BGP summary
show ip bgp summary

# Show interfaces
show interfaces status

# Show VLAN (leafs only)
show vlan brief

# Configure via CLI
config interface ip add Ethernet0 10.1.1.0/31

# Or edit config_db.json and reload
config reload -y
```

## gNMI Access

SONiC has native gNMI support on port 8080:

```bash
# From host
gnmic -a 172.20.20.10:8080 -u admin -p admin --insecure capabilities

# Get interface state
gnmic -a 172.20.20.10:8080 -u admin -p admin --insecure \
  get --path /interfaces/interface[name=Ethernet0]/state
```

## Notes

- SONiC requires x86_64 architecture (won't work on ARM64/Apple Silicon)
- Default credentials: admin/admin
- Config changes require `config reload` or restart
- gNMI port 8080 is enabled by default
