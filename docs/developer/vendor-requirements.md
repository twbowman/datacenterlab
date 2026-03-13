# Vendor-Specific Requirements

## Overview

This document details vendor-specific requirements, limitations, and configuration needs for the Production Network Testing Lab. Understanding these requirements is critical for successful multi-vendor deployments.

**Validates: Requirements 10.2, 13.2, 13.4**

## Nokia SR Linux

### Container Requirements

**Image**: `ghcr.io/nokia/srlinux:latest`
- **Size**: ~1.2GB
- **Boot Time**: 90-120 seconds
- **Resource Requirements**:
  - CPU: 2 cores minimum
  - Memory: 2GB minimum
  - Disk: 5GB minimum

**Supported Types**:
- `ixrd1`: 1 linecard, 6 ports
- `ixrd2`: 2 linecards, 12 ports
- `ixrd3`: 3 linecards, 18 ports
- `ixrh2`: High-scale, 32 ports
- `ixrh3`: High-scale, 48 ports

### Management Access

**Protocols**:
- SSH: Port 22 (default)
- gNMI: Port 57400 (default)
- JSON-RPC: Port 80 (HTTP), 443 (HTTPS)

**Default Credentials**:
- Username: `admin`
- Password: `NokiaSrl1!`

### OpenConfig Support

**Status**: ✅ Full support (requires explicit enablement)

**CRITICAL**: OpenConfig must be explicitly enabled in SR Linux configuration:

```json
{
  "system": {
    "management": {
      "openconfig": {
        "admin-state": "enable"
      }
    },
    "grpc-server": {
      "mgmt": {
        "yang-models": "openconfig"
      }
    }
  }
}
```

**Prerequisites**:
1. LLDP must be enabled first
2. gNMI server must be enabled
3. Management network instance must be configured

**Verification**:
```bash
# Check OpenConfig status
sr_cli "info from state /system management openconfig"
# Expected: admin-state enable, oper-state up

# Check YANG models
sr_cli "info from state /system grpc-server mgmt yang-models"
# Expected: yang-models openconfig
```

**Supported OpenConfig Models**:
- ✅ `/interfaces` - Full support
- ✅ `/network-instances` - Full support
- ✅ `/lldp` - Full support (requires LLDP enabled)
- ✅ `/system` - Partial support
- ⚠️ `/bgp` - Use native SR Linux paths for full features
- ⚠️ `/ospf` - Use native SR Linux paths

### Configuration Methods

**gNMI** (Recommended):
- Protocol: gRPC
- Port: 57400
- Encoding: JSON_IETF
- Operations: Get, Set, Subscribe

**JSON-RPC**:
- Protocol: HTTP/HTTPS
- Port: 80/443
- Format: JSON
- Operations: Get, Set

**CLI**:
- Protocol: SSH
- Port: 22
- Format: Text commands
- Operations: Show, Configure

### Known Limitations

1. **EVPN/VXLAN**: Requires SR Linux 23.3.1+
2. **OpenConfig BGP**: Limited compared to native paths
3. **Interface Names**: Use `ethernet-1/1` format (not `e1-1`)
4. **Management Network**: Must use `mgmt` network instance for gNMI

### Example Topology

```yaml
name: srlinux-lab
topology:
  kinds:
    nokia_srlinux:
      image: ghcr.io/nokia/srlinux:latest
  
  nodes:
    spine1:
      kind: nokia_srlinux
      type: ixrd3
      startup-config: configs/srlinux/spine1.json
      mgmt_ipv4: 172.20.20.10
```

## Arista cEOS

### Container Requirements

**Image**: `ceos:latest` (must be imported manually)
- **Size**: ~1.5GB
- **Boot Time**: 60-90 seconds
- **Resource Requirements**:
  - CPU: 2 cores minimum
  - Memory: 2GB minimum
  - Disk: 5GB minimum

**Image Import**:
```bash
# Download from Arista website (requires account)
# Import to Docker
docker import cEOS64-lab-4.28.0F.tar.xz ceos:4.28.0F
```

### Management Access

**Protocols**:
- SSH: Port 22 (default)
- eAPI: Port 443 (HTTPS)
- gNMI: Port 6030 (requires enablement)

**Default Credentials**:
- Username: `admin`
- Password: (empty by default)

### OpenConfig Support

**Status**: ⚠️ Partial support

**Supported OpenConfig Models**:
- ✅ `/interfaces` - Full support
- ✅ `/network-instances` - Full support
- ⚠️ `/lldp` - Limited support
- ⚠️ `/system` - Limited support
- ❌ `/bgp` - Not supported (use native EOS paths)
- ❌ `/ospf` - Not supported (use native EOS paths)

**gNMI Enablement**:
```
management api gnmi
   transport grpc default
      vrf MGMT
```

### Configuration Methods

**eAPI** (Recommended):
- Protocol: HTTPS
- Port: 443
- Format: JSON-RPC
- Operations: Show, Configure

**gNMI**:
- Protocol: gRPC
- Port: 6030
- Encoding: JSON_IETF
- Operations: Get, Set, Subscribe

**CLI**:
- Protocol: SSH
- Port: 22
- Format: EOS commands
- Operations: Show, Configure

### Known Limitations

1. **OpenConfig BGP**: Not supported, use native EOS paths
2. **gNMI**: Must be explicitly enabled
3. **Container Licensing**: Requires valid license for full features
4. **Interface Names**: Use `Ethernet1/1` format (capital E)
5. **EVPN**: Requires EOS 4.25.0+

### Example Topology

```yaml
name: arista-lab
topology:
  kinds:
    arista_ceos:
      image: ceos:4.28.0F
  
  nodes:
    arista-spine1:
      kind: arista_ceos
      startup-config: configs/arista/spine1.cfg
      mgmt_ipv4: 172.20.20.20
```

## Dell SONiC

### Container Requirements

**Image**: `docker-sonic-vs:latest`
- **Size**: ~800MB
- **Boot Time**: 120-180 seconds
- **Resource Requirements**:
  - CPU: 2 cores minimum
  - Memory: 4GB minimum (higher than others)
  - Disk: 10GB minimum

**Image Build**:
```bash
# Clone SONiC repository
git clone https://github.com/sonic-net/sonic-buildimage.git
cd sonic-buildimage

# Build virtual switch image
make configure PLATFORM=vs
make target/docker-sonic-vs.gz
```

### Management Access

**Protocols**:
- SSH: Port 22 (default)
- REST API: Port 443 (HTTPS)
- gNMI: Port 8080 (requires enablement)

**Default Credentials**:
- Username: `admin`
- Password: `YourPaSsWoRd`

### OpenConfig Support

**Status**: ⚠️ Limited support

**Supported OpenConfig Models**:
- ⚠️ `/interfaces` - Partial support
- ❌ `/network-instances` - Not supported
- ❌ `/lldp` - Not supported
- ❌ `/system` - Not supported
- ❌ `/bgp` - Not supported (use native SONiC paths)
- ❌ `/ospf` - Not supported (use native SONiC paths)

**Recommendation**: Use native SONiC REST API paths for most operations.

### Configuration Methods

**REST API** (Recommended):
- Protocol: HTTPS
- Port: 443
- Format: JSON
- Operations: GET, POST, PUT, DELETE

**gNMI**:
- Protocol: gRPC
- Port: 8080
- Encoding: JSON_IETF
- Operations: Get, Set, Subscribe (limited)

**CLI**:
- Protocol: SSH
- Port: 22
- Format: SONiC commands
- Operations: Show, Config

### Known Limitations

1. **OpenConfig Support**: Very limited, use native SONiC paths
2. **Boot Time**: Significantly longer than other vendors (2-3 minutes)
3. **Memory Usage**: Higher memory requirements
4. **gNMI**: Limited support, REST API preferred
5. **EVPN**: Requires SONiC 202012+
6. **Container Stability**: Less stable than SR Linux or Arista

### Example Topology

```yaml
name: sonic-lab
topology:
  kinds:
    sonic:
      image: docker-sonic-vs:latest
  
  nodes:
    sonic-leaf1:
      kind: sonic
      startup-config: configs/sonic/leaf1.json
      mgmt_ipv4: 172.20.20.30
      env:
        SONIC_CFGGEN_ARGS: "-j /etc/sonic/config_db.json"
```

## Juniper cRPD

### Container Requirements

**Image**: `crpd:latest` (must be obtained from Juniper)
- **Size**: ~600MB
- **Boot Time**: 60-90 seconds
- **Resource Requirements**:
  - CPU: 2 cores minimum
  - Memory: 2GB minimum
  - Disk: 5GB minimum

**Image Acquisition**:
- Download from Juniper support portal (requires account)
- Load into Docker: `docker load -i crpd-<version>.tar.gz`

### Management Access

**Protocols**:
- SSH: Port 22 (default)
- NETCONF: Port 830 (default)
- gNMI: Port 32767 (requires enablement)

**Default Credentials**:
- Username: `root`
- Password: (set during first boot)

### OpenConfig Support

**Status**: ⚠️ Partial support

**Supported OpenConfig Models**:
- ✅ `/interfaces` - Full support
- ✅ `/network-instances` - Full support
- ⚠️ `/lldp` - Limited support
- ⚠️ `/system` - Limited support
- ⚠️ `/bgp` - Partial support
- ⚠️ `/ospf` - Partial support

**gNMI Enablement**:
```
set system services extension-service request-response grpc clear-text port 32767
set system services extension-service request-response grpc skip-authentication
```

### Configuration Methods

**NETCONF** (Recommended):
- Protocol: SSH
- Port: 830
- Format: XML
- Operations: Get, Edit, Commit

**gNMI**:
- Protocol: gRPC
- Port: 32767
- Encoding: JSON_IETF
- Operations: Get, Set, Subscribe

**CLI**:
- Protocol: SSH
- Port: 22
- Format: Junos commands
- Operations: Show, Configure

### Known Limitations

1. **Licensing**: Requires valid license for full features
2. **gNMI**: Must be explicitly enabled
3. **OpenConfig**: Better support than SONiC, but not as complete as SR Linux
4. **NETCONF Preferred**: NETCONF is more mature than gNMI on Junos
5. **Container Mode**: Some features limited compared to physical Junos

### Example Topology

```yaml
name: juniper-lab
topology:
  kinds:
    juniper_crpd:
      image: crpd:23.2R1
  
  nodes:
    juniper-spine1:
      kind: juniper_crpd
      startup-config: configs/juniper/spine1.conf
      mgmt_ipv4: 172.20.20.40
```

## Multi-Vendor Comparison

### OpenConfig Support Matrix

| Feature | SR Linux | Arista cEOS | SONiC | Juniper cRPD |
|---------|----------|-------------|-------|--------------|
| Interfaces | ✅ Full | ✅ Full | ⚠️ Partial | ✅ Full |
| Network Instances | ✅ Full | ✅ Full | ❌ None | ✅ Full |
| LLDP | ✅ Full | ⚠️ Limited | ❌ None | ⚠️ Limited |
| System | ⚠️ Partial | ⚠️ Limited | ❌ None | ⚠️ Limited |
| BGP | ⚠️ Partial | ❌ None | ❌ None | ⚠️ Partial |
| OSPF | ⚠️ Partial | ❌ None | ❌ None | ⚠️ Partial |

**Legend**:
- ✅ Full: Complete OpenConfig support
- ⚠️ Partial/Limited: Some features supported
- ❌ None: No OpenConfig support

### Configuration Protocol Recommendations

| Vendor | Primary | Secondary | Avoid |
|--------|---------|-----------|-------|
| SR Linux | gNMI | JSON-RPC | CLI |
| Arista cEOS | eAPI | gNMI | CLI |
| SONiC | REST API | CLI | gNMI |
| Juniper cRPD | NETCONF | gNMI | CLI |

### Telemetry Protocol Recommendations

| Vendor | Primary | Secondary | Notes |
|--------|---------|-----------|-------|
| SR Linux | gNMI | - | Best gNMI support |
| Arista cEOS | gNMI | eAPI | Requires enablement |
| SONiC | REST API | gNMI | gNMI limited |
| Juniper cRPD | gNMI | NETCONF | NETCONF more mature |

### Resource Requirements Summary

| Vendor | CPU | Memory | Disk | Boot Time |
|--------|-----|--------|------|-----------|
| SR Linux | 2 cores | 2GB | 5GB | 90-120s |
| Arista cEOS | 2 cores | 2GB | 5GB | 60-90s |
| SONiC | 2 cores | 4GB | 10GB | 120-180s |
| Juniper cRPD | 2 cores | 2GB | 5GB | 60-90s |

## Configuration Enablement Checklist

### SR Linux

- [ ] Enable gNMI server
- [ ] Enable OpenConfig (if using OpenConfig paths)
- [ ] Enable LLDP (if using OpenConfig LLDP)
- [ ] Configure management network instance
- [ ] Set credentials

### Arista cEOS

- [ ] Enable eAPI
- [ ] Enable gNMI (if using gNMI)
- [ ] Configure management VRF
- [ ] Set credentials
- [ ] Apply license (for full features)

### SONiC

- [ ] Enable REST API
- [ ] Configure management interface
- [ ] Set credentials
- [ ] Initialize config_db.json

### Juniper cRPD

- [ ] Enable NETCONF
- [ ] Enable gNMI (if using gNMI)
- [ ] Configure management interface
- [ ] Set root password
- [ ] Apply license (for full features)

## Troubleshooting Common Issues

### SR Linux: OpenConfig Not Working

**Symptom**: gNMI subscription to OpenConfig paths fails

**Diagnosis**:
```bash
# Check OpenConfig status
sr_cli "info from state /system management openconfig"

# Check LLDP status (required for OpenConfig LLDP)
sr_cli "info from state /system lldp"
```

**Solution**:
1. Enable OpenConfig: `sr_cli "set /system management openconfig admin-state enable"`
2. Enable LLDP: `sr_cli "set /system lldp admin-state enable"`
3. Commit: `sr_cli "commit now"`

### Arista: gNMI Not Accessible

**Symptom**: Cannot connect to gNMI port 6030

**Diagnosis**:
```bash
# Check gNMI status
docker exec clab-lab-arista-spine1 Cli -c "show management api gnmi"
```

**Solution**:
```
# Enable gNMI
configure
management api gnmi
   transport grpc default
      vrf MGMT
   exit
exit
write memory
```

### SONiC: Slow Boot Time

**Symptom**: SONiC container takes 3+ minutes to boot

**Diagnosis**:
```bash
# Check container logs
docker logs clab-lab-sonic-leaf1
```

**Solution**:
- This is normal for SONiC
- Increase wait time in deployment scripts
- Consider pre-warming containers

### Juniper: NETCONF Connection Refused

**Symptom**: Cannot connect to NETCONF port 830

**Diagnosis**:
```bash
# Check NETCONF status
docker exec clab-lab-juniper-spine1 cli show system services
```

**Solution**:
```
# Enable NETCONF
configure
set system services netconf ssh
commit
```

## Production Considerations

### SR Linux
- **Production Ready**: ✅ Yes
- **Licensing**: Not required for containerlab
- **Support**: Commercial support available
- **Stability**: Excellent

### Arista cEOS
- **Production Ready**: ✅ Yes
- **Licensing**: Required for production use
- **Support**: Commercial support available
- **Stability**: Excellent

### SONiC
- **Production Ready**: ⚠️ Depends on vendor
- **Licensing**: Open source (Apache 2.0)
- **Support**: Community or vendor-specific
- **Stability**: Good (varies by vendor)

### Juniper cRPD
- **Production Ready**: ✅ Yes
- **Licensing**: Required for production use
- **Support**: Commercial support available
- **Stability**: Excellent

## Related Documentation

- **Architecture Guide**: `docs/developer/architecture.md`
- **Vendor Extension Guide**: `docs/developer/vendor-extension.md`
- **OpenConfig Telemetry**: `monitoring/OPENCONFIG-TELEMETRY-GUIDE.md`
- **Metric Normalization**: `docs/developer/metric-normalization.md`
- **Ansible Dispatcher**: `ansible/DISPATCHER-PATTERN.md`

## Summary

### Key Takeaways

1. **OpenConfig Support Varies**: SR Linux has best support, SONiC has least
2. **Explicit Enablement**: Most vendors require explicit OpenConfig/gNMI enablement
3. **Native Paths Recommended**: Use native paths when OpenConfig is incomplete
4. **Resource Requirements**: SONiC requires more resources than others
5. **Boot Times**: SONiC is slowest (2-3 min), Arista is fastest (1-1.5 min)
6. **Production Licensing**: Arista and Juniper require licenses for production

### Vendor Selection Guide

**Choose SR Linux if**:
- You want best OpenConfig support
- You prefer gNMI for everything
- You need modern, cloud-native NOS

**Choose Arista cEOS if**:
- You have existing Arista infrastructure
- You prefer eAPI for configuration
- You need mature, stable platform

**Choose SONiC if**:
- You want open source solution
- You can tolerate longer boot times
- You're comfortable with REST API

**Choose Juniper cRPD if**:
- You have existing Juniper infrastructure
- You prefer NETCONF for configuration
- You need Junos feature set

### Multi-Vendor Strategy

For multi-vendor deployments:
1. Use OpenConfig where fully supported (interfaces)
2. Fall back to native paths for incomplete features (BGP, OSPF)
3. Normalize all metrics to universal paths
4. Test each vendor's specific requirements
5. Document vendor-specific limitations
