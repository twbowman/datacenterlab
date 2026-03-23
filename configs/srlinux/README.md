# Nokia SR Linux Configuration

SR Linux configs for CLOS topology with BGP underlay.

## Features

- ✅ Native gNMI support (enabled by default)
- ✅ JSON-based configuration
- ✅ Full BGP support
- ✅ Works on ARM64 and x86_64

## Using SR Linux

### Switch a node to SR Linux

Edit `topologies/topology-srlinux.yml`:

```yaml
spine1:
  group: srlinux-router    # Change from frr-router
  mgmt-ipv4: 172.20.20.10
  binds:
    - ./configs/spine1:/config
    - ./configs/spine1/srlinux/config.json:/etc/opt/srlinux/config.json
```

### Access SR Linux CLI

```bash
# Enter SR Linux CLI
docker exec -it clab-gnmi-clos-spine1 sr_cli

# Show interfaces
show interface brief

# Show BGP summary
show network-instance default protocols bgp summary

# Show running config
info
```

## gNMI Access

SR Linux has native gNMI on port 57400:

```bash
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --insecure capabilities
```

## Configuration Structure

Each switch has a `config.json` with:
- System settings (hostname, gNMI server)
- Interfaces and IP addresses
- Network instances
- BGP configuration

## Topology

Same as FRR/SONiC:
- Spines: AS 65001-65002
- Leafs: AS 65011-65014
- Loopbacks: 10.0.0.x
- P2P links: 10.1.x.0/31, 10.2.x.0/31

## Default Credentials

- Username: `admin`
- Password: `NokiaSrl1!`
