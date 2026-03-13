---
title: OpenConfig Vendor-Specific Requirements
description: Critical configuration requirements for enabling OpenConfig support on different network vendors
inclusion: auto
fileMatchPattern: ".*openconfig.*|.*gnmi.*|.*telemetry.*"
---

# OpenConfig Vendor-Specific Requirements

## Overview

OpenConfig support is NOT automatically enabled on most network devices. Each vendor requires specific configuration to enable OpenConfig YANG models for gNMI telemetry.

**CRITICAL**: Always verify OpenConfig is enabled before attempting to collect OpenConfig metrics.

## Path Strategy for SR Linux

**IMPORTANT**: SR Linux supports BOTH OpenConfig and native paths simultaneously via gNMI origin specification:

### Using gNMI Origin for Dual-Model Access

SR Linux provides a translation layer between OpenConfig and native YANG models. When OpenConfig is enabled, you can access BOTH models by specifying the origin:

- **OpenConfig paths** (no origin prefix or `openconfig:` prefix):
  - Interfaces: `/interfaces/interface[name=...]`
  - System: `/system/...`
  - LLDP: `/lldp/...`
  - Network instances: `/network-instances/network-instance[name=...]`
  - BGP neighbors: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state`

- **SR Linux native paths** (use `srl_nokia:` origin prefix):
  - Interfaces: `srl_nokia:/interface[name=...]`
  - Network instances: `srl_nokia:/network-instance[name=...]`
  - OSPF: `srl_nokia:/network-instance[name=default]/protocols/ospf/...`
  - BGP: `srl_nokia:/network-instance[name=default]/protocols/bgp/...`
  - EVPN: `srl_nokia:/network-instance[name=...]/protocols/bgp-evpn/...`
  - Routing Policy: `srl_nokia:/routing-policy/...`

### Recommended Approach

**Configuration (gNMI SET)**: Use SR Linux native paths with `srl_nokia:` origin
- Provides full access to SR Linux's rich native protocol features
- Example: `srl_nokia:/network-instance[name=default]/protocols/bgp/autonomous-system`
- Used for: OSPF, BGP, EVPN, VXLAN configuration
- **Why not OpenConfig for config?**
  - EVPN (L2VPN_EVPN) address family is NOT supported via OpenConfig on SR Linux
  - OpenConfig BGP requires peer-groups and more verbose configuration
  - SR Linux native paths provide simpler, more complete protocol access
  - OpenConfig BGP config IS technically possible but limited (tested: basic BGP works, EVPN fails)

**Telemetry (gNMI SUBSCRIBE)**: Use OpenConfig paths without origin prefix
- Enables multi-vendor dashboards and metric normalization
- Example: `/interfaces/interface[name=ethernet-1/1]/state/counters`
- Example: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state`
- Used for: Interface stats, BGP neighbor state, LLDP neighbors
- **Why OpenConfig for telemetry?**
  - Multi-vendor compatibility: same Grafana dashboards work across Arista, Juniper, Nokia, etc.
  - Standardized metric names and structures
  - Industry best practice for network observability

### gnmic Command Examples

```bash
# Configuration using SR Linux native paths
gnmic -a 172.20.20.21:57400 -u admin -p password --skip-verify set \
  --update-path 'srl_nokia:/network-instance[name=default]/protocols/bgp/autonomous-system' \
  --update-value 65000 \
  --encoding json_ietf

# Telemetry using OpenConfig paths
gnmic -a 172.20.20.21:57400 -u admin -p password --skip-verify subscribe \
  --path '/interfaces/interface[name=ethernet-1/1]/state/counters' \
  --encoding json_ietf

# Telemetry for BGP using OpenConfig paths
gnmic -a 172.20.20.21:57400 -u admin -p password --skip-verify subscribe \
  --path '/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state' \
  --encoding json_ietf
```

### gnmic Configuration File Example

```yaml
subscriptions:
  # OpenConfig interface stats - multi-vendor compatible
  oc_interface_stats:
    paths:
      - /interfaces/interface/state/counters
      - /interfaces/interface/state/oper-status
      - /interfaces/interface/state/admin-status
    mode: stream
    stream-mode: sample
    sample-interval: 10s
  
  # OpenConfig BGP state - multi-vendor compatible
  oc_bgp_neighbors:
    paths:
      - /network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state
    mode: stream
    stream-mode: sample
    sample-interval: 30s
  
  # OpenConfig LLDP - multi-vendor compatible
  oc_lldp:
    paths:
      - /lldp/interfaces/interface/neighbors/neighbor/state
    mode: stream
    stream-mode: sample
    sample-interval: 60s
```

### Key Benefits

1. **Best of Both Worlds**: Use SR Linux native features for configuration while maintaining OpenConfig compatibility for telemetry
2. **Multi-Vendor Dashboards**: OpenConfig telemetry enables universal Grafana dashboards that work across vendors
3. **Production Ready**: Works in both containerlab and production environments
4. **No Compromise**: Full access to SR Linux protocol features without sacrificing OpenConfig telemetry

### OpenConfig BGP Configuration Testing Results

Testing confirmed that OpenConfig BGP configuration is PARTIALLY supported on SR Linux:

**What Works:**
```bash
# Basic BGP configuration via OpenConfig
gnmic set \
  --update-path '/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/config/identifier' \
  --update-value 'BGP' \
  --update-path '/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/bgp/global/config/as' \
  --update-value 65000 \
  --update-path '/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/bgp/global/config/router-id' \
  --update-value '10.0.1.1' \
  --update-path '/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/bgp/global/afi-safis/afi-safi[afi-safi-name=openconfig-bgp-types:IPV4_UNICAST]/config/enabled' \
  --update-value true
```

**What Doesn't Work:**
- EVPN address family: `openconfig-bgp-types:L2VPN_EVPN` returns error "unable to map L2VPN_EVPN"
- Neighbors require peer-groups (mandatory field), making configuration more complex
- Route reflector configuration not tested but likely requires additional OpenConfig structures

**Conclusion:** While OpenConfig BGP configuration is technically possible for basic IPv4/IPv6 unicast, the lack of EVPN support and increased complexity make SR Linux native paths the better choice for configuration.

### Important Notes

- **Always use OpenConfig paths for telemetry collection** - This ensures dashboards work across multiple vendors
- **Use SR Linux native paths with `srl_nokia:` origin for configuration** - This provides access to full protocol features including EVPN
- **OSPF telemetry EXCEPTION**: SR Linux does NOT expose OSPF via OpenConfig paths (confirmed via testing and Nokia documentation)
  - While SR Linux has a translation layer that maps OpenConfig to native models, it only supports "base protocol functionalities"
  - OSPF configuration and state information are primarily exposed through native SR Linux YANG models
  - OSPF telemetry MUST use SR Linux native paths: `srl_nokia:/network-instance[name=default]/protocols/ospf/...`
  - This requires vendor-specific dashboards for OSPF monitoring
  - BGP, interfaces, LLDP, and system metrics ARE available via OpenConfig for multi-vendor dashboards
  - Reference: Nokia Documentation confirms "OSPF configuration and state information are primarily exposed through the native SR Linux YANG models"
- **EVPN/VXLAN**: Not available in OpenConfig configuration; use SR Linux native paths for both configuration and telemetry if needed

## Nokia SR Linux

### Requirements

OpenConfig must be explicitly enabled in SR Linux configuration:

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

### Prerequisites

1. **LLDP must be enabled first**:
```json
{
  "system": {
    "lldp": {
      "admin-state": "enable"
    }
  }
}
```

2. **gNMI server must be enabled**:
```json
{
  "system": {
    "gnmi-server": {
      "admin-state": "enable",
      "network-instance": [
        {
          "name": "mgmt"
        }
      ]
    }
  }
}
```

### Verification Commands

```bash
# Check OpenConfig status
sr_cli "info from state /system management openconfig"
# Expected: admin-state enable, oper-state up

# Check YANG models
sr_cli "info from state /system grpc-server mgmt yang-models"
# Expected: yang-models openconfig

# Test native path access with origin
gnmic -a <device>:57400 -u admin -p password --skip-verify get \
  --path 'srl_nokia:/network-instance[name=default]' \
  --encoding json_ietf

# Test OpenConfig path access for telemetry
gnmic -a <device>:57400 -u admin -p password --skip-verify get \
  --path '/interfaces/interface[name=ethernet-1/1]/state' \
  --encoding json_ietf

# Test OpenConfig BGP telemetry
gnmic -a <device>:57400 -u admin -p password --skip-verify get \
  --path '/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state' \
  --encoding json_ietf
```

### Configuration Methods

**Method 1: Startup Config** (Recommended)
- Add to `config.json` before device boot
- Persistent across reboots
