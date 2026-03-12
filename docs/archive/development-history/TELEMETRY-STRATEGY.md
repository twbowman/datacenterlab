# Telemetry and Configuration Strategy

## Overview

This lab currently uses **native SR Linux paths** for both configuration and telemetry:
- **Configuration**: Native SR Linux YANG models via srlinux_gnmi
- **Telemetry/Monitoring**: Native SR Linux paths via gNMIc

## Current Implementation: Native SR Linux Paths

### Why Native Paths?

1. **Complete Feature Access**: Full access to all SR Linux capabilities
2. **Proven Reliability**: Vendor-tested and production-ready
3. **Better Documentation**: Comprehensive SR Linux documentation
4. **Simpler Implementation**: Direct mapping to device data model

### Configuration (srlinux_gnmi method)

All Ansible playbooks in `ansible/methods/srlinux_gnmi/` use native SR Linux paths:

**Interfaces**: `/interface[name=X]/admin-state`
```bash
gnmic set \
  --update-path /interface[name=ethernet-1/1]/admin-state \
  --update-value enable
```

**BGP**: `/network-instance[name=default]/protocols/bgp`
```bash
gnmic set \
  --update-path /network-instance[name=default]/protocols/bgp/autonomous-system \
  --update-value 65001
```

**LLDP**: `/system/lldp`
```bash
gnmic set \
  --update-path /system/lldp/admin-state \
  --update-value enable
```

### Telemetry (gNMIc subscriptions)

gNMIc subscriptions use native SR Linux paths:

```yaml
subscriptions:
  interface_stats:
    paths:
      - /interface/statistics
    
  ospf_state:
    paths:
      - /network-instance[name=default]/protocols/ospf
  
  bgp_state:
    paths:
      - /network-instance[name=default]/protocols/bgp
```

### Metric Examples

**Interface Statistics**:
- `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets`
- `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_in_packets`

**BGP State**:
- `gnmic_bgp_state_srl_nokia_network_instance_network_instance_protocols_srl_nokia_bgp_bgp_neighbor_session_state`

**OSPF State**:
- `gnmic_ospf_state_srl_nokia_network_instance_network_instance_protocols_srl_nokia_ospf_ospf_instance_area_interface_neighbor_adjacency_state`

## Multi-Vendor Strategy

### Current Status
✅ **Optimized for SR Linux** - Using native paths throughout
📋 **Multi-vendor ready** - Strategy documented for future expansion

### When Adding New Device Types

You have two options:

#### Option 1: Vendor-Specific Paths (Current Approach)
**Pros**:
- Complete feature access
- Better performance
- Vendor-optimized
- More reliable

**Cons**:
- Separate playbooks per vendor
- Different metric names
- More maintenance

**Implementation**:
1. Create vendor-specific Ansible roles (e.g., `ansible/methods/srlinux_gnmi_arista/`)
2. Add vendor-specific gNMIc subscriptions
3. Update dashboards to support multiple metric formats
4. Use Prometheus relabeling to normalize where possible

#### Option 2: Migrate to OpenConfig (Future)
**Pros**:
- Vendor-neutral playbooks
- Standardized metrics
- Industry standard
- Easier multi-vendor support

**Cons**:
- May not support all features
- Vendor implementation varies
- Potential performance differences
- Less mature for some vendors

**Migration Path**:
1. Test OpenConfig support on target devices
2. Create OpenConfig-based roles in `ansible/methods/openconfig/`
3. Verify feature parity with native paths
4. Update gNMIc to use OpenConfig telemetry paths
5. Migrate dashboards to OpenConfig metrics

### Example: Adding Arista EOS

#### Option 1: Native Arista Paths
```yaml
# ansible/methods/srlinux_gnmi_arista/roles/interfaces/tasks/main.yml
- name: Configure interface
  ansible.builtin.shell: |
    gnmic set \
      --update-path /interfaces/interface[name={{ item.name }}]/config/enabled \
      --update-value true
```

#### Option 2: OpenConfig (if supported)
```yaml
# ansible/methods/openconfig/roles/interfaces/tasks/main.yml
- name: Configure interface (vendor-neutral)
  ansible.builtin.shell: |
    gnmic set \
      --encoding json_ietf \
      --update-path /interfaces/interface[name={{ item.name }}]/config/enabled \
      --update-value true
  # Works on SR Linux, Arista, Juniper, etc.
```

## OpenConfig Support in This Lab

### Limited OpenConfig Usage

Some verification playbooks use OpenConfig paths for read operations:
- `ansible/playbooks/verify.yml` - Uses OpenConfig for LLDP and BGP neighbor queries
- `ansible/archive/verify-lldp.yml` - OpenConfig LLDP verification

These demonstrate OpenConfig capability but aren't used for primary configuration.

### Testing OpenConfig

To test OpenConfig paths on SR Linux:

```bash
# Query LLDP neighbors (OpenConfig)
gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p 'NokiaSrl1!' \
  --skip-verify \
  --encoding json_ietf \
  get --path /lldp/interfaces/interface[name=*]/neighbors

# Query BGP neighbors (OpenConfig)  
gnmic -a clab-gnmi-clos-spine1:57400 \
  -u admin -p 'NokiaSrl1!' \
  --skip-verify \
  --encoding json_ietf \
  get --path /network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/bgp/neighbors
```

## Recommendation for Multi-Vendor

When you add other switch vendors, I recommend:

### Phase 1: Vendor-Specific (Fastest)
- Create vendor-specific roles for each platform
- Use native paths for complete feature access
- Maintain separate but similar playbook structures
- Use Prometheus relabeling for metric normalization

### Phase 2: Evaluate OpenConfig (Optional)
- Test OpenConfig support on all target platforms
- Compare feature completeness vs native paths
- Assess vendor implementation maturity
- Consider hybrid approach (OpenConfig where possible, native where needed)

### Phase 3: Standardize (Long-term)
- Migrate to OpenConfig if vendor support is mature
- Keep vendor-specific extensions for unique features
- Document platform differences
- Maintain fallback to native paths

## Files Reference

### Configuration (Native SR Linux)
- `ansible/methods/srlinux_gnmi/` - Primary configuration method
- `ansible/methods/srlinux_gnmi/roles/gnmi_bgp/` - BGP configuration
- `ansible/methods/srlinux_gnmi/roles/gnmi_interfaces/` - Interface configuration
- `ansible/methods/srlinux_gnmi/roles/gnmi_lldp/` - LLDP configuration

### Telemetry (Native SR Linux)
- `monitoring/gnmic/gnmic-config.yml` - Telemetry subscriptions
- `monitoring/grafana/provisioning/dashboards/*.json` - Dashboards
- `analyze-link-utilization.py` - Metric analysis script

### OpenConfig Examples
- `ansible/playbooks/verify.yml` - OpenConfig verification queries
- `ansible/archive/verify-lldp.yml` - OpenConfig LLDP verification

### Documentation
- `TELEMETRY-STRATEGY.md` - This document
- `ansible/OPENCONFIG-MIGRATION.md` - OpenConfig reference (aspirational)
- `DNS-NAMING-FIX-SUMMARY.md` - Device naming implementation

## Best Practices

1. **Start with native paths** - Ensures complete functionality
2. **Test OpenConfig early** - Understand vendor support before committing
3. **Document vendor differences** - Makes future decisions easier
4. **Use abstraction layers** - Prometheus relabeling, Ansible variables
5. **Keep it simple** - Don't over-engineer for hypothetical multi-vendor scenarios

## Decision Matrix

| Scenario | Recommendation |
|----------|---------------|
| Single vendor (SR Linux only) | ✅ Native paths (current) |
| 2-3 vendors, similar features | Consider OpenConfig |
| Multiple vendors, advanced features | Vendor-specific paths + abstraction |
| Standardization priority | OpenConfig with native fallbacks |
| Performance priority | Native paths |

## Future Considerations

The networking industry is moving toward OpenConfig, but adoption varies:
- **Mature**: Arista, Juniper (good OpenConfig support)
- **Growing**: Cisco IOS-XR, Nokia SR Linux
- **Limited**: Traditional enterprise switches

Monitor vendor OpenConfig maturity before committing to migration. Native paths remain the most reliable option for production deployments.

