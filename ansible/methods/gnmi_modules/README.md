# gNMI Modules Configuration Method

This method uses Ansible gNMI modules (nokia.grpc collection or similar) to configure devices via gNMI protocol.

## Status

🚧 **Awaiting Stable Modules** - Uses Ansible gNMI modules when available and stable.

## Overview

The gNMI modules method will use native Ansible modules for gNMI operations. This provides a more "Ansible-native" experience compared to the srlinux_gnmi method which uses shell commands.

## Planned Features

- True idempotency via gNMI Set operations
- Support for OpenConfig YANG models (read-only)
- Support for native SR Linux paths (configuration)
- Certificate-based authentication
- Structured data validation
- Atomic transactions

## Implementation Approach

This method will use Ansible gNMI modules instead of CLI tools.

### Why Ansible Modules?

1. **Native Ansible experience** - Uses standard Ansible module syntax
2. **Better integration** - Works with Ansible features (check mode, diff, etc.)
3. **Type safety** - Module parameters are validated
4. **Cleaner playbooks** - No shell commands needed

### Current Status

The nokia.grpc collection has bugs that prevent its use:
- Error: `AttributeError: 'Connection' object has no attribute 'nonetype'`
- Affects Ansible 2.16.3 with Python 3.10 and 3.11

### When Available

Once stable gNMI modules are available, this method will provide:

```yaml
- name: Configure interface via gNMI module
  nokia.grpc.gnmi_set:
    paths:
      - path: /interface[name=ethernet-1/1]/admin-state
        value: enable
      - path: /interface[name=ethernet-1/1]/subinterface[index=0]/ipv4/address[ip-prefix=10.1.1.0/31]
        value: {}
```

### Alternative: Use srlinux_gnmi Method

Until gNMI modules are stable, use the `srlinux_gnmi` method which provides the same functionality via the gnmic CLI tool.

## Directory Structure

```
methods/gnmi/
├── site.yml                         # Main playbook
├── playbooks/                       # Component playbooks
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml
│   └── configure-lldp.yml
└── roles/                           # gNMI-specific roles
    ├── gnmi_interfaces/
    ├── gnmi_bgp/
    └── gnmi_lldp/
```

## Pros (When Implemented)

- True idempotency
- Vendor-neutral (with OpenConfig)
- Fast and efficient
- Structured data validation
- Atomic transactions
- Better error handling

## Cons

- More complex setup
- Certificate management required
- Requires gNMI support
- SR Linux needs native paths for config
- Collection bugs need fixing

## Resources

- [gNMI Specification](https://github.com/openconfig/gnmi)
- [OpenConfig Models](https://github.com/openconfig/public)
- [SR Linux gNMI Guide](https://documentation.nokia.com/srlinux/)
- [gnmic Tool](https://gnmic.openconfig.net/)
- [nokia.grpc Collection](https://galaxy.ansible.com/nokia/grpc)

## Contributing

If you want to implement this method:

1. Test gnmic CLI tool approach first
2. Create roles following CLI method pattern
3. Document native SR Linux paths needed
4. Add certificate management
5. Test idempotency thoroughly
6. Update this README

## Testing gnmic

The gnmic tool works with SR Linux:

```bash
# Test connection
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities

# Get configuration
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify get --path /interface[name=ethernet-1/1]

# Set configuration (use native paths)
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify set \
  --update-path /interface[name=ethernet-1/1]/admin-state \
  --update-value enable
```

## Next Steps

1. Fix or work around nokia.grpc collection bugs
2. Document native SR Linux paths for all features
3. Create gnmic-based roles
4. Implement certificate management
5. Test thoroughly
6. Document migration from CLI method
