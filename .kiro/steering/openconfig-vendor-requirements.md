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
```

### Configuration Methods

**Method 1: Startup Config** (Recommended)
- Add to `config.json` before device boot
- Persistent across reboots
