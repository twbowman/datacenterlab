# Enabling OpenConfig on SR Linux - Summary

## Discovery

OpenConfig support exists in SR Linux but must be explicitly enabled via configuration:

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

## What Was Done

### 1. Updated All Device Configs

✅ Updated startup configs for all 6 devices:
- `configs/spine1/srlinux/config.json`
- `configs/spine2/srlinux/config.json`
- `configs/leaf1/srlinux/config.json`
- `configs/leaf2/srlinux/config.json`
- `configs/leaf3/srlinux/config.json`
- `configs/leaf4/srlinux/config.json`

Each now includes:
```json
{
  "system": {
    "name": {
      "host-name": "device-name"
    },
    "gnmi-server": {
      "admin-state": "enable",
      "network-instance": [
        {
          "name": "mgmt"
        }
      ]
    },
    "management": {
      "openconfig": {
        "admin-state": "enable"
      }
    }
  }
}
```

### 2. Created Enable Script

✅ Created `enable-openconfig.sh` for easy updates

## What Needs to Be Done

### Apply the Configuration

The configs are updated but not yet applied to running devices. You have two options:

#### Option 1: Restart Entire Lab (Recommended)

```bash
# Destroy and redeploy
orb -m clab sudo containerlab destroy -t topology.yml
orb -m clab sudo containerlab deploy -t topology.yml

# Wait for devices to boot (2 minutes)
sleep 120

# Reconfigure network (interfaces, BGP, etc.)
cd ansible
orb -m clab ansible-playbook site.yml
```

**Time**: ~5 minutes
**Impact**: Full lab restart, need to reconfigure

#### Option 2: Restart Devices One by One

```bash
# Restart each device
for device in spine1 spine2 leaf1 leaf2 leaf3 leaf4; do
  echo "Restarting $device..."
  orb -m clab docker restart clab-gnmi-clos-$device
  sleep 60
done

# Reconfigure network
cd ansible
orb -m clab ansible-playbook site.yml
```

**Time**: ~8 minutes
**Impact**: Rolling restart, less disruptive

## After Enabling OpenConfig

### 1. Verify OpenConfig is Enabled

```bash
# Check on spine1
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli "info from state /system management openconfig"

# Should show:
# admin-state enable
```

### 2. Test OpenConfig Paths

```bash
# Test interface path
orb -m clab docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status"

# Should return data (not connection error)
```

### 3. Restart gNMIc

```bash
# Restart to pick up OpenConfig subscriptions
orb -m clab docker restart clab-monitoring-gnmic
sleep 10
```

### 4. Verify OpenConfig Metrics

```bash
# Check for OpenConfig metrics
curl http://172.20.20.5:9273/metrics | grep "oc_interface_stats"

# Should see metrics like:
# gnmic_oc_interface_stats_interfaces_interface_state_counters_in_octets
```

## Expected Results

### Before OpenConfig Enabled
```bash
# OpenConfig paths fail
orb -m clab docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status"

# Error: connection error: desc = "error reading server preface: EOF"
```

### After OpenConfig Enabled
```bash
# OpenConfig paths work
orb -m clab docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status"

# Returns: oper-status: "UP" or "DOWN"
```

## Impact on Previous Work

### Multi-Vendor Framework
✅ No changes needed - already designed for this

### Telemetry Collection
✅ OpenConfig subscriptions in gNMIc config will now work

### Grafana Dashboards
✅ Can now use OpenConfig metrics (after restart)

### Metric Normalization
✅ Can normalize both SR Linux native AND OpenConfig metrics

## Why This Matters

### Before (Native Only)
- ❌ Vendor-specific metrics only
- ❌ Can't test OpenConfig
- ❌ Multi-vendor requires different queries

### After (Native + OpenConfig)
- ✅ Can use native SR Linux metrics (current dashboards)
- ✅ Can use OpenConfig metrics (multi-vendor dashboards)
- ✅ Can test OpenConfig support
- ✅ Can compare native vs OpenConfig
- ✅ Ready for true multi-vendor with OpenConfig

## Next Steps

1. **Restart Lab** (choose option above)
2. **Verify OpenConfig** is enabled
3. **Test OpenConfig paths** work
4. **Restart gNMIc** to collect OpenConfig metrics
5. **Verify metrics** appear in Prometheus
6. **Update test results** document

## Files Modified

- ✅ `configs/spine1/srlinux/config.json`
- ✅ `configs/spine2/srlinux/config.json`
- ✅ `configs/leaf1/srlinux/config.json`
- ✅ `configs/leaf2/srlinux/config.json`
- ✅ `configs/leaf3/srlinux/config.json`
- ✅ `configs/leaf4/srlinux/config.json`
- ✅ `enable-openconfig.sh` (new)
- ✅ `ENABLE-OPENCONFIG-SUMMARY.md` (this file)

## Quick Command Reference

```bash
# Restart lab
orb -m clab sudo containerlab destroy -t topology.yml
orb -m clab sudo containerlab deploy -t topology.yml
sleep 120

# Reconfigure
cd ansible && orb -m clab ansible-playbook site.yml

# Verify OpenConfig
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli \
  "info from state /system management openconfig"

# Test OpenConfig path
orb -m clab docker exec clab-monitoring-gnmic /app/gnmic \
  -a clab-gnmi-clos-spine1:57400 -u admin -p 'NokiaSrl1!' --insecure \
  get --path "/interfaces/interface[name=ethernet-1/1]/state/oper-status"

# Restart gNMIc
orb -m clab docker restart clab-monitoring-gnmic

# Check metrics
curl http://172.20.20.5:9273/metrics | grep "oc_interface"
```

## Status

- ✅ OpenConfig configuration added to all device configs
- ⏳ Waiting for lab restart to apply
- ⏳ Waiting for OpenConfig verification
- ⏳ Waiting for OpenConfig metrics collection

**Ready to restart lab and test OpenConfig!**
