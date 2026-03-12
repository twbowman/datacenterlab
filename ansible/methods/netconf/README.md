# NETCONF Configuration Method

This method would use NETCONF protocol to configure devices.

## Status

❌ **Not Applicable** - SR Linux does not support NETCONF protocol.

## Overview

NETCONF (Network Configuration Protocol) is an IETF standard for network device configuration. However, SR Linux uses gNMI instead of NETCONF.

## Why Not Available

Nokia SR Linux chose to implement gNMI (gRPC Network Management Interface) instead of NETCONF because:

1. **Modern protocol** - gNMI uses gRPC, which is more efficient than NETCONF's XML/SSH
2. **Streaming support** - gNMI supports streaming telemetry natively
3. **Better performance** - Binary protocol (protobuf) vs XML
4. **Industry direction** - Many vendors moving to gNMI

## Alternative

Use the **gNMI method** instead (`methods/gnmi/`).

## Supported Protocols in SR Linux

| Protocol | Status | Use Case |
|----------|--------|----------|
| CLI | ✅ Supported | Manual configuration, scripting |
| gNMI | ✅ Supported | Automation, telemetry |
| NETCONF | ❌ Not supported | N/A |
| JSON-RPC | ✅ Supported | Management API |

## Resources

- [SR Linux Management Interfaces](https://documentation.nokia.com/srlinux/)
- [gNMI vs NETCONF Comparison](https://github.com/openconfig/reference/blob/master/rpc/gnmi/gnmi-specification.md)
