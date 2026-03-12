# Ansible OpenConfig Integration - Complete

## Summary

OpenConfig enablement has been integrated into the Ansible automation framework. The system configuration (including OpenConfig) is now part of the standard deployment process.

## What Was Added

### New Role: gnmi_system

Created `ansible/methods/srlinux_gnmi/roles/gnmi_system/` with:

**Purpose**: Configure system-level settings including OpenConfig enablement

**Tasks** (`tasks/main.yml`):
1. Enable gNMI server
2. Enable OpenConfig support
3. Set gRPC server YANG models to OpenConfig

**Configuration Applied**:
```json
{
  "system": {
    "gnmi-server": {
      "admin-state": "enable",
      "network-instance": [{"name": "mgmt"}]
    },
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

### Updated Playbook

Modified `ansible/methods/srlinux_gnmi/site.yml`:

**Before**:
```yaml
roles:
  - role: gnmi_interfaces
  - role: gnmi_lldp
  - role: gnmi_ospf
  - role: gnmi_bgp
```

**After**:
```yaml
roles:
  - role: gnmi_system      # NEW - runs first
  - role: gnmi_interfaces
  - role: gnmi_lldp
  - role: gnmi_ospf
  - role: gnmi_bgp
```

### Documentation

Created comprehensive documentation:
- `ansible/methods/srlinux_gnmi/roles/gnmi_system/README.md` - Role documentation
- `.kiro/steering/openconfig-vendor-requirements.md` - Vendor requirements reference

## How It Works

### Deployment Flow

```
1. ansible-playbook site.yml
   ↓
2. gnmi_system role runs FIRST
   ├─ Enable gNMI server
   ├─ Enable OpenConfig
   └─ Set YANG models to OpenConfig
   ↓
3. Other roles run (interfaces, LLDP, OSPF, BGP)
   ↓
4. Device is fully configured with OpenConfig enabled
```

### Why This Order Matters

The `gnmi_system` role MUST run first because:
1. gNMI server must be enabled for subsequent gNMI operations
2. OpenConfig must be enabled before collecting OpenConfig metrics
3. YANG models must be set before telemetry collection starts

## Usage

### Deploy Everything (Including OpenConfig)

```bash
cd ansible
ansible-playbook site.yml
```

This will:
- ✅ Enable gNMI server
- ✅ Enable OpenConfig
- ✅ Configure interfaces
- ✅ Configure LLDP
- ✅ Configure OSPF
- ✅ Configure BGP

### Deploy Only System Configuration

```bash
cd ansible
ansible-playbook site.yml --tags system
```

This will:
- ✅ Enable gNMI server
- ✅ Enable OpenConfig
- ❌ Skip other configuration

### Deploy Only OpenConfig

```bash
cd ansible
ansible-playbook site.yml --tags openconfig
```

This will:
- ✅ Enable OpenConfig
- ❌ Skip everything else

## Verification

After deployment, verify OpenConfig is enabled:

```bash
# Check on spine1
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli \
  "info from state /system management openconfig"

# Expected output:
# admin-state enable
# oper-state up
```

Or run the test script:

```bash
./test-openconfig-metrics.sh
```

## Benefits

### 1. Automated OpenConfig Enablement

**Before**: Manual configuration required
- Edit config files manually
- Restart devices
- Verify configuration

**After**: Fully automated
- Run `ansible-playbook site.yml`
- OpenConfig enabled automatically
- Ready for telemetry collection

### 2. Consistent Configuration

Every deployment includes:
- ✅ gNMI server enabled
- ✅ OpenConfig enabled
- ✅ Correct YANG models
- ✅ Ready for monitoring

### 3. Idempotent Operations

Running the playbook multiple times:
- ✅ Safe (won't break existing config)
- ✅ Fast (only applies changes if needed)
- ✅ Reliable (consistent results)

### 4. Tagged Execution

Granular control over what gets configured:
- `--tags system` - System configuration only
- `--tags openconfig` - OpenConfig only
- `--tags interfaces` - Interfaces only
- `--tags config` - All configuration

## Integration with Telemetry

### Before Ansible Runs

```
Device: Default configuration
  ├─ gNMI server: disabled
  ├─ OpenConfig: disabled
  └─ YANG models: native only

gNMIc: Cannot collect OpenConfig metrics ❌
```

### After Ansible Runs

```
Device: Fully configured
  ├─ gNMI server: enabled ✅
  ├─ OpenConfig: enabled ✅
  └─ YANG models: openconfig ✅

gNMIc: Collecting OpenConfig metrics ✅
```

## Multi-Vendor Considerations

### Current Implementation (SR Linux)

The `gnmi_system` role is SR Linux specific:
- Uses SR Linux native paths
- SR Linux specific configuration structure

### Future Multi-Vendor Support

When adding other vendors, create vendor-specific system roles:

```
ansible/roles/
├─ multi_vendor_system/
│  ├─ tasks/
│  │  ├─ main.yml          # Dispatcher
│  │  ├─ srlinux.yml       # SR Linux (current gnmi_system)
│  │  ├─ arista_eos.yml    # Arista OpenConfig enablement
│  │  └─ sonic.yml         # SONiC OpenConfig enablement
```

Each vendor has different requirements (see `.kiro/steering/openconfig-vendor-requirements.md`).

## Files Created/Modified

### New Files
- ✅ `ansible/methods/srlinux_gnmi/roles/gnmi_system/tasks/main.yml`
- ✅ `ansible/methods/srlinux_gnmi/roles/gnmi_system/defaults/main.yml`
- ✅ `ansible/methods/srlinux_gnmi/roles/gnmi_system/README.md`
- ✅ `.kiro/steering/openconfig-vendor-requirements.md`
- ✅ `ANSIBLE-OPENCONFIG-INTEGRATION.md` (this file)

### Modified Files
- ✅ `ansible/methods/srlinux_gnmi/site.yml` (added gnmi_system role)

## Testing

### Test the New Role

```bash
# Deploy to lab
cd ansible
orb -m clab ansible-playbook site.yml

# Verify OpenConfig enabled
./test-openconfig-metrics.sh

# Check metrics collecting
curl http://172.20.20.5:9273/metrics | grep "oc_interface"
```

### Expected Results

All tests should pass:
- ✅ OpenConfig enabled on all devices
- ✅ OpenConfig operational state: up
- ✅ YANG models: openconfig
- ✅ Metrics collecting

## Troubleshooting

### OpenConfig Not Enabled

```bash
# Check if role ran
ansible-playbook site.yml --tags system -v

# Manually verify
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli \
  "info from state /system management openconfig"
```

### gNMI Connection Errors

```bash
# Check gNMI server status
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli \
  "info from state /system gnmi-server"

# Should show: admin-state enable
```

### Metrics Not Collecting

```bash
# Restart gNMIc after Ansible deployment
orb -m clab docker restart clab-monitoring-gnmic

# Wait 30 seconds
sleep 30

# Check metrics
curl http://172.20.20.5:9273/metrics | grep "oc_interface"
```

## Best Practices

### 1. Always Run System Role First

The `gnmi_system` role is positioned first in `site.yml` for a reason. Don't change this order.

### 2. Verify After Deployment

Always verify OpenConfig is enabled after running Ansible:
```bash
./test-openconfig-metrics.sh
```

### 3. Use Tags for Selective Deployment

Don't re-run everything if you only need to update one component:
```bash
# Only update BGP
ansible-playbook site.yml --tags bgp

# Only update system settings
ansible-playbook site.yml --tags system
```

### 4. Document Vendor Requirements

When adding new vendors, update `.kiro/steering/openconfig-vendor-requirements.md` with their specific requirements.

## Related Documentation

- `ansible/methods/srlinux_gnmi/roles/gnmi_system/README.md` - Role documentation
- `.kiro/steering/openconfig-vendor-requirements.md` - Vendor requirements
- `OPENCONFIG-IMPLEMENTATION-COMPLETE.md` - OpenConfig implementation
- `ansible/MULTI-VENDOR-ARCHITECTURE.md` - Multi-vendor framework

## Conclusion

OpenConfig enablement is now fully integrated into the Ansible automation framework. Every deployment automatically:

1. Enables gNMI server
2. Enables OpenConfig support
3. Configures YANG models
4. Prepares devices for telemetry collection

This ensures consistent, repeatable deployments with OpenConfig ready for multi-vendor monitoring.

---

**Status**: ✅ Complete and integrated
**Date**: March 12, 2026
**Impact**: All future Ansible deployments include OpenConfig enablement
**Next**: Deploy to lab and verify with `ansible-playbook site.yml`
