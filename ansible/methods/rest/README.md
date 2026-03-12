# REST API Configuration Method

This method would use SR Linux JSON-RPC API to configure devices.

## Status

💡 **Possible Future Implementation** - SR Linux supports JSON-RPC API.

## Overview

SR Linux provides a JSON-RPC API that can be used for configuration and management. This could be wrapped in Ansible modules for automation.

## SR Linux JSON-RPC API

SR Linux supports JSON-RPC 2.0 over HTTP/HTTPS for management operations.

### Features
- RESTful-style API
- JSON data format
- HTTPS support
- Authentication via tokens
- CRUD operations on configuration

### Endpoints
- Configuration: `/jsonrpc`
- CLI commands: `/jsonrpc`
- State queries: `/jsonrpc`

## Potential Implementation

### Using uri Module
```yaml
- name: Configure interface via JSON-RPC
  uri:
    url: "https://{{ ansible_host }}:443/jsonrpc"
    method: POST
    user: admin
    password: NokiaSrl1!
    force_basic_auth: yes
    validate_certs: no
    body_format: json
    body:
      jsonrpc: "2.0"
      id: 1
      method: "set"
      params:
        commands:
          - "set / interface ethernet-1/1 admin-state enable"
```

### Custom Module
```python
# library/srlinux_jsonrpc.py
def configure_interface(module):
    url = f"https://{module.params['host']}:443/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "set",
        "params": {
            "commands": module.params['commands']
        }
    }
    # Make request, handle response
```

## Pros

- Native HTTP/HTTPS (no special protocols)
- JSON data format (easy to work with)
- RESTful patterns (familiar to developers)
- Good for web-based integrations
- No special client libraries needed

## Cons

- Less efficient than gRPC/gNMI
- May not support all features
- Documentation may be limited
- Not as widely used as gNMI

## When to Use

Consider REST/JSON-RPC method when:
- Integrating with web applications
- Working in environments without gRPC support
- Need simple HTTP-based automation
- Prefer JSON over protobuf
- Building custom dashboards/UIs

## Resources

- [SR Linux JSON-RPC Documentation](https://documentation.nokia.com/srlinux/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

## Implementation Status

This method is not currently implemented but could be added if needed. The CLI and gNMI methods cover most use cases.

## Contributing

If you want to implement this method:

1. Research SR Linux JSON-RPC API capabilities
2. Test API endpoints and authentication
3. Create Ansible modules or use uri module
4. Follow the pattern from CLI method
5. Document API endpoints and payloads
6. Test thoroughly
7. Update this README
