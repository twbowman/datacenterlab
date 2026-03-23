# gNMI/gRPC Setup for Ansible

## Overview

The Ansible playbooks now use the `nokia.grpc` collection to communicate with SR Linux devices via gNMI (gRPC Network Management Interface) using OpenConfig models.

## Prerequisites

### Install Ansible Collection

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
```

This installs the `nokia.grpc` collection which provides the `gnmi_set` and `gnmi_get` modules.

### Install Python Dependencies

The nokia.grpc collection requires:

```bash
pip3 install grpcio protobuf
```

Or in the remote server:

```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install grpcio protobuf
```

## How It Works

### gNMI vs JSON-RPC

**Before (JSON-RPC):**
- Used HTTP/HTTPS with JSON-RPC protocol
- Less standard, vendor-specific
- Required manual HTTP requests

**Now (gNMI/gRPC):**
- Uses gRPC protocol (HTTP/2 based)
- Industry standard (OpenConfig)
- Native Ansible modules
- Better error handling
- Streaming telemetry support

### Module Usage

The `nokia.grpc.gnmi_set` module is used for configuration:

```yaml
- name: Configure interface
  nokia.grpc.gnmi_set:
    hostname: "{{ ansible_host }}"
    port: "{{ gnmi_port }}"
    username: "{{ gnmi_username }}"
    password: "{{ gnmi_password }}"
    insecure: true
    encoding: "json_ietf"
    update:
      - path: "/interfaces/interface[name=ethernet-1/1]"
        val:
          name: "ethernet-1/1"
          config:
            enabled: true
    origin: "openconfig"
```

### Key Parameters

- `hostname`: Device IP address
- `port`: gNMI port (57400 for SR Linux)
- `username/password`: Authentication credentials
- `insecure: true`: Skip TLS certificate verification
- `encoding: "json_ietf"`: Use JSON encoding (IETF standard)
- `origin: "openconfig"`: Use OpenConfig YANG models
- `update`: List of paths and values to configure

## OpenConfig Paths

### Interfaces

```
/interfaces/interface[name=<name>]
  /config
    /name
    /type (ethernetCsmacd, softwareLoopback)
    /enabled
    /description
  /subinterfaces/subinterface[index=0]
    /ipv4/addresses/address[ip=<ip>]
      /config
        /ip
        /prefix-length
```

### BGP

```
/network-instances/network-instance[name=default]
  /protocols/protocol[identifier=BGP][name=BGP]
    /bgp
      /global/config
        /as
        /router-id
      /neighbors/neighbor[neighbor-address=<ip>]
        /config
          /neighbor-address
          /peer-as
          /enabled
        /afi-safis/afi-safi[afi-safi-name=IPV4_UNICAST]
          /config
            /afi-safi-name
            /enabled
```

### LLDP

```
/lldp
  /config
    /enabled
  /interfaces/interface[name=<name>]
    /config
      /name
      /enabled
```

## Troubleshooting

### Collection Not Found

```bash
# Install the collection
ansible-galaxy collection install nokia.grpc

# Or from requirements
ansible-galaxy collection install -r requirements.yml
```

### gRPC Connection Errors

```bash
# Check if gNMI port is accessible
nc -zv 172.20.20.10 57400

# Test with gnmic CLI
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --insecure capabilities
```

### Python Module Errors

```bash
# Install required Python packages
pip3 install grpcio protobuf

# Check Python version (needs 3.6+)
python3 --version
```

### Authentication Errors

Default credentials for SR Linux:
- Username: `admin`
- Password: `NokiaSrl1!`
- Port: `57400`

### Verify gNMI is Enabled

```bash
docker exec clab-gnmi-clos-spine1 sr_cli "show system gnmi-server"
```

Should show:
```
admin-state: enable
network-instance: mgmt
```

## Testing

### Test gNMI Connection

```bash
cd ansible

# Test with a simple get operation
ansible spine1 -m nokia.grpc.gnmi_get \
  -a "hostname=172.20.20.10 port=57400 username=admin password=NokiaSrl1! insecure=true path=/system/information/version"
```

### Run Playbooks

```bash
cd ansible

# Configure interfaces
ansible-playbook playbooks/configure-interfaces.yml -v

# Configure LLDP
ansible-playbook playbooks/configure-lldp.yml -v

# Configure BGP
ansible-playbook playbooks/configure-bgp.yml -v

# Run all
ansible-playbook site.yml -v
```

## Benefits of gNMI/gRPC

1. **Standard Protocol**: OpenConfig industry standard
2. **Better Performance**: HTTP/2 based, binary protocol
3. **Streaming**: Real-time telemetry streaming
4. **Vendor Neutral**: Works across vendors supporting OpenConfig
5. **Type Safety**: Protobuf schema validation
6. **Better Errors**: Structured error responses

## References

- [OpenConfig Models](https://github.com/openconfig/public)
- [gNMI Specification](https://github.com/openconfig/reference/blob/master/rpc/gnmi/gnmi-specification.md)
- [Nokia SR Linux gNMI Guide](https://documentation.nokia.com/srlinux/)
- [nokia.grpc Collection](https://galaxy.ansible.com/nokia/grpc)
