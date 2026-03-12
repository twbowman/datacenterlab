# Configuration Validation Role

## Overview

This role provides pre-deployment configuration syntax validation for multi-vendor network devices. It validates configuration parameters before they are applied to devices, preventing deployment failures due to syntax errors.

**Validates: Requirements 2.5, 11.2**

## Features

- **Pre-deployment Validation**: Checks configuration syntax before applying to devices
- **Multi-Vendor Support**: Validates SR Linux, Arista EOS, SONiC, and Juniper configurations
- **Descriptive Error Messages**: Provides clear error messages with expected formats
- **Early Failure Detection**: Catches errors before device communication
- **Vendor-Specific Rules**: Applies vendor-appropriate validation rules

## Architecture

### Dispatcher Pattern

The role uses a dispatcher pattern to route validation to vendor-specific implementations:

```
config_validation/
├── tasks/
│   ├── main.yml              # Dispatcher
│   ├── validate_srlinux.yml  # SR Linux validation rules
│   ├── validate_arista.yml   # Arista EOS validation rules
│   ├── validate_sonic.yml    # SONiC validation rules
│   └── validate_junos.yml    # Juniper validation rules
└── README.md
```

## Usage

### Automatic Integration

The role is automatically included in `ansible/site.yml` before configuration deployment:

```yaml
- name: Validate configuration syntax before deployment
  include_role:
    name: config_validation
  tags: [validation, always]
```

### Manual Validation

To validate configuration without deploying:

```bash
# Validate all devices
ansible-playbook -i inventory.yml site.yml --tags validation

# Validate specific device
ansible-playbook -i inventory.yml site.yml --tags validation --limit spine1

# Validate specific vendor
ansible-playbook -i inventory.yml site.yml --tags validation --limit srlinux_devices
```

## Validation Rules

### Common Validations (All Vendors)

1. **Connection Variables**: Ensures required connection parameters are defined
2. **IPv4 Address Format**: Validates CIDR notation (X.X.X.X/Y)
3. **BGP ASN Range**: Validates ASN is between 1 and 4294967295
4. **BGP Router ID**: Validates IPv4 format for router ID
5. **BGP Neighbor Syntax**: Validates neighbor IP and peer AS

### SR Linux Specific

**Interface Names**:
- Valid formats: `ethernet-X/Y`, `mgmt0`, `system0`, `loX`
- Regex: `^ethernet-[0-9]+/[0-9]+$|^mgmt0$|^system0$|^lo[0-9]+$`

**Examples**:
- ✓ Valid: `ethernet-1/1`, `ethernet-1/49`, `mgmt0`, `lo0`
- ✗ Invalid: `Ethernet1/1`, `eth1/1`, `e1-1`

### Arista EOS Specific

**Interface Names**:
- Valid formats: `Ethernet1/1`, `ethernet-1/1` (translated), `Management1`
- Regex: `^ethernet-[0-9]+/[0-9]+$|^Ethernet[0-9]+(/[0-9]+)?$|^Management[0-9]+$`

**Examples**:
- ✓ Valid: `Ethernet1/1`, `Ethernet1`, `ethernet-1/1`, `Management1`
- ✗ Invalid: `eth1/1`, `e1-1`, `mgmt0`

### SONiC Specific

**Interface Names**:
- Valid formats: `Ethernet0`, `ethernet-1/1` (translated), `PortChannel1`
- Regex: `^ethernet-[0-9]+/[0-9]+$|^Ethernet[0-9]+$|^PortChannel[0-9]+$`

**Examples**:
- ✓ Valid: `Ethernet0`, `Ethernet48`, `ethernet-1/1`, `PortChannel1`
- ✗ Invalid: `Ethernet1/1`, `eth0`, `Po1`

### Juniper Specific

**Interface Names**:
- Valid formats: `ge-0/0/0`, `xe-0/0/0`, `ethernet-1/1` (translated), `lo0`
- Regex: `^ethernet-[0-9]+/[0-9]+$|^[gx]e-[0-9]+/[0-9]+/[0-9]+$|^lo[0-9]+$`

**Examples**:
- ✓ Valid: `ge-0/0/0`, `xe-0/0/1`, `ethernet-1/1`, `lo0`
- ✗ Invalid: `Ethernet1/1`, `eth0`, `GigabitEthernet0/0/0`

## Error Messages

### Example: Invalid Interface Name

```
FAILED! => {
    "assertion": "item.name is match('^ethernet-[0-9]+/[0-9]+$|^mgmt0$|^system0$|^lo[0-9]+$')",
    "msg": "Invalid SR Linux interface name: Ethernet1/1\nExpected format: ethernet-X/Y, mgmt0, system0, or loX"
}
```

### Example: Invalid BGP Configuration

```
FAILED! => {
    "assertion": "asn is number and asn >= 1 and asn <= 4294967295",
    "msg": "Invalid BGP configuration for spine1:\n- ASN must be a number between 1 and 4294967295\n- Router ID must be in IPv4 format (X.X.X.X)\nCurrent values: asn=undefined, router_id=10.0.0.1"
}
```

### Example: Missing Required Variables

```
FAILED! => {
    "assertion": "ansible_host is defined and gnmi_port is defined",
    "msg": "Missing required SR Linux connection variables for spine1.\nRequired: ansible_host, gnmi_port, gnmi_username, gnmi_password"
}
```

## Validated Configuration Elements

### Interfaces
- Interface name format (vendor-specific)
- IPv4 address format (CIDR notation)
- Required fields: `name`
- Optional fields: `description`, `ip`

### BGP
- ASN range (1 to 4294967295)
- Router ID format (IPv4 address)
- Neighbor IP format (IPv4 address)
- Neighbor peer AS range
- Required fields: `asn`, `router_id`

### BGP Neighbors
- Neighbor IP format (IPv4 address)
- Peer AS range (1 to 4294967295)
- Required fields: `ip`, `peer_as`

## Variables

### Required Variables (per vendor)

**SR Linux**:
- `ansible_host`: Device management IP
- `gnmi_port`: gNMI port
- `gnmi_username`: gNMI username
- `gnmi_password`: gNMI password

**Arista EOS**:
- `ansible_host`: Device management IP
- `ansible_user`: API username
- `ansible_password`: API password

**SONiC**:
- `ansible_host`: Device management IP
- `ansible_user`: API username
- `ansible_password`: API password

**Juniper**:
- `ansible_host`: Device management IP
- `ansible_user`: NETCONF username
- `ansible_password`: NETCONF password

### Configuration Variables

- `interfaces`: List of interface configurations
- `asn`: BGP autonomous system number
- `router_id`: BGP router ID
- `bgp_neighbors`: List of BGP neighbor configurations

## Testing

### Test Valid Configuration

```bash
# Should pass validation
ansible-playbook -i inventory.yml site.yml --tags validation
```

### Test Invalid Configuration

1. Introduce an error in inventory (e.g., invalid interface name)
2. Run validation:
```bash
ansible-playbook -i inventory.yml site.yml --tags validation
```
3. Should fail with descriptive error message

### Test Missing Variables

1. Remove required variable from inventory
2. Run validation:
```bash
ansible-playbook -i inventory.yml site.yml --tags validation
```
3. Should fail indicating missing variable

## Limitations

1. **Syntax Only**: Validates syntax, not semantic correctness
2. **No Device Communication**: Does not verify device capabilities
3. **Limited Scope**: Only validates common configuration elements
4. **No Template Validation**: Does not validate Jinja2 templates
5. **No Cross-Device Validation**: Does not check consistency across devices

## Future Enhancements

- Semantic validation (e.g., BGP neighbor reachability)
- Template syntax validation
- Cross-device consistency checks (e.g., matching BGP peer ASNs)
- YAML schema validation
- Custom validation rules per deployment
- Integration with vendor-specific linters

## Related Documentation

- **Requirements**: See `.kiro/specs/production-network-testing-lab/requirements.md` (Requirements 2.5, 11.2)
- **Design**: See `.kiro/specs/production-network-testing-lab/design.md` (Property 7)
- **Main Playbook**: See `ansible/site.yml`
- **Rollback Role**: See `ansible/roles/config_rollback/`

