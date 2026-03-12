# Directory Rename: gnmicli → srlinux_gnmi

## Summary

Renamed `ansible/methods/gnmicli/` to `ansible/methods/srlinux_gnmi/` to better reflect that this method uses:
- **SR Linux native YANG paths** (not OpenConfig)
- **gNMI protocol** via gnmic CLI tool

## What Changed

### Directory Structure
```
ansible/methods/
├── gnmicli/              → srlinux_gnmi/
│   ├── site.yml
│   ├── playbooks/
│   └── roles/
```

### Files Updated

All references to `gnmicli` were updated to `srlinux_gnmi` in:

1. **ansible/site.yml** - Main playbook import
2. **ansible/ansible.cfg** - roles_path configuration
3. **ansible/README.md** - Method documentation
4. **ansible/METHODS.md** - Method comparison
5. **ansible/methods/srlinux_gnmi/site.yml** - Method playbook
6. **ansible/methods/srlinux_gnmi/README.md** - Method documentation
7. **ansible/methods/srlinux_gnmi/playbooks/verify.yml** - Verification playbook
8. **ansible/methods/gnmi_modules/README.md** - Cross-references
9. **README.md** - Main project documentation
10. **TELEMETRY-STRATEGY.md** - Strategy documentation
11. **ROUTING-PROTOCOL-DASHBOARDS.md** - Dashboard documentation

## Why This Name?

### srlinux_gnmi Clearly Indicates:
- **srlinux** - Uses SR Linux native YANG paths (vendor-specific)
- **gnmi** - Uses gNMI protocol via gnmic CLI tool

### Better Than gnmicli Because:
- "gnmicli" only indicated the tool (gnmic CLI)
- Didn't indicate vendor-specific paths
- Could be confused with generic gNMI usage
- New name makes vendor-specificity explicit

## Usage (No Change)

Commands remain the same, just with the new directory name:

```bash
# Full deployment
ansible-playbook -i ansible/inventory.yml ansible/site.yml

# Explicit method
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/site.yml

# Individual playbooks
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/configure-interfaces.yml
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/playbooks/verify.yml

# Using tags
ansible-playbook -i ansible/inventory.yml ansible/methods/srlinux_gnmi/site.yml --tags bgp
```

## Future Vendor Support

When adding other vendors, the naming pattern is clear:

```
ansible/methods/
├── srlinux_gnmi/        # SR Linux native paths via gNMI
├── arista_gnmi/         # Arista native paths via gNMI (future)
├── junos_gnmi/          # Junos native paths via gNMI (future)
└── openconfig_gnmi/     # OpenConfig paths via gNMI (future, multi-vendor)
```

This makes it obvious which method to use for which vendor.

## Backward Compatibility

⚠️ **Breaking Change**: Old commands referencing `gnmicli` will need to be updated to `srlinux_gnmi`.

If you have scripts or documentation referencing the old path:
- Update `methods/gnmicli/` → `methods/srlinux_gnmi/`
- Update `gnmicli method` → `srlinux_gnmi method`

## Related Documentation

- `TELEMETRY-STRATEGY.md` - Native vs OpenConfig strategy
- `ansible/methods/srlinux_gnmi/README.md` - Method details
- `ansible/README.md` - Ansible overview
- `ansible/METHODS.md` - Method comparison
