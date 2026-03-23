# gnmi_system Role

## Description

Configures system-level settings on SR Linux devices including:
- gNMI server enablement
- OpenConfig support enablement
- gRPC server YANG model configuration

## Requirements

- SR Linux device with gNMI support
- gnmic CLI tool installed on control node
- Network connectivity to device management interface

## Role Variables

```yaml
gnmi_port: 57400              # gNMI server port
gnmi_username: admin          # gNMI authentication username
gnmi_password: NokiaSrl1!     # gNMI authentication password
```

## Dependencies

None. This role should be run FIRST before other configuration roles.

## Example Playbook

```yaml
- hosts: all
  roles:
    - role: gnmi_system
      tags: [system]
```

## What This Role Configures

### 1. gNMI Server

Enables the gNMI server on the management network instance:

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

### 2. OpenConfig Support

Enables OpenConfig YANG models for telemetry:

```json
{
  "system": {
    "management": {
      "openconfig": {
        "admin-state": "enable"
      }
    }
  }
}
```

### 3. gRPC Server YANG Models

Configures the gRPC server to use OpenConfig models:

```json
{
  "system": {
    "grpc-server": {
      "mgmt": {
        "yang-models": "openconfig"
      }
    }
  }
}
```

## Why This Matters

### OpenConfig Enablement

SR Linux does NOT enable OpenConfig by default. Without this configuration:
- ❌ OpenConfig telemetry paths will fail
- ❌ gNMIc cannot collect OpenConfig metrics
- ❌ Multi-vendor monitoring won't work

With this configuration:
- ✅ OpenConfig telemetry paths work
- ✅ gNMIc collects OpenConfig metrics
- ✅ Multi-vendor monitoring ready

### gNMI Server

The gNMI server must be explicitly enabled for:
- Configuration via gNMI (this playbook)
- Telemetry collection via gNMI (monitoring)

## Tags

- `system` - All system configuration tasks
- `gnmi` - gNMI server configuration only
- `openconfig` - OpenConfig enablement only

## Example Usage

```bash
# Run all system configuration
ansible-playbook site.yml --tags system

# Only enable OpenConfig
ansible-playbook site.yml --tags openconfig

# Only enable gNMI server
ansible-playbook site.yml --tags gnmi
```

## Verification

After running this role, verify configuration:

```bash
# Check gNMI server status
sr_cli "info from state /system gnmi-server"

# Check OpenConfig status
sr_cli "info from state /system management openconfig"

# Check YANG models
sr_cli "info from state /system grpc-server mgmt yang-models"
```

Expected output:
```
gnmi-server:
  admin-state: enable
  
openconfig:
  admin-state: enable
  oper-state: up
  
yang-models: openconfig
```

## Notes

- This role must run BEFORE other configuration roles
- OpenConfig enablement is persistent across reboots
- Changes take effect immediately (no reboot required)
- This is SR Linux specific - other vendors may have different requirements

## Related Documentation

- `.kiro/steering/openconfig-vendor-requirements.md` - Vendor-specific OpenConfig requirements
- `OPENCONFIG-IMPLEMENTATION-COMPLETE.md` - OpenConfig implementation guide
- `monitoring/gnmic/gnmic-config.yml` - Telemetry configuration using OpenConfig
