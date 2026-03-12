# Archive Directory

This directory contains files that are no longer actively used but kept for reference.

## Structure

### docs/
Documentation from previous iterations of the lab:
- `MIGRATE-TO-GNMIC.md` - Migration guide from Telegraf to gNMIc
- `MIGRATION-COMPLETE.md` - Completion summary of gNMIc migration
- `MONITORING-FILES.md` - Old monitoring files documentation
- `MONITORING-PERSISTENCE.md` - Persistence strategy (now integrated into main docs)
- `SWITCHING-NOS.md` - Guide for switching network operating systems
- `TELEMETRY-SETUP.md` - Old telemetry setup guide

### scripts/
Scripts from previous workflows:
- `configure-lldp-cli.sh` - CLI-based LLDP configuration (replaced by Ansible)
- `lldp-config.txt` - Manual LLDP config commands
- `setup-monitoring-persistence.sh` - Manual persistence setup (now in topology.yml)
- `deploy-gnmic-collector.sh` - Standalone gNMIc deployment (now in topology.yml)
- `test-connectivity.sh` - Old connectivity tests (replaced by Ansible verify)
- `verify-lab.sh` - Old verification script (replaced by Ansible verify)
- `verify-routing-gnmi.sh` - gNMI routing verification
- `verify-telemetry.sh` - Telemetry verification

### monitoring/
- `telegraf/` - Old Telegraf configuration (replaced by gNMIc-only stack)

### topology-simple.yml
Old topology file using FRR routers (replaced by SR Linux topology)

### frr/
FRR router configurations from old topology:
- Configuration files for spine and leaf routers using FRRouting
- Replaced by: SR Linux configurations in `configs/*/srlinux/`
- Reason: Lab now uses Nokia SR Linux instead of FRR

### sonic/
SONiC router configurations from experimental topology:
- Configuration files for spine and leaf routers using SONiC
- Replaced by: SR Linux configurations in `configs/*/srlinux/`
- Reason: Lab now uses Nokia SR Linux instead of SONiC

## Why Archived?

These files were replaced by:
1. **Ansible automation** - Configuration is now done via Ansible playbooks
2. **Integrated deployment** - Everything is in topology.yml and deployment scripts
3. **Simplified workflow** - Single `deploy-datacenter.sh` script handles everything
4. **Better documentation** - Consolidated into main README and deployment guides

## Current Active Files

See the root directory for current files:
- `deploy-datacenter.sh` - Main deployment script
- `redeploy-datacenter.sh` - Full redeploy script
- `LAB-RESTART-GUIDE.md` - Current deployment guide
- `DATACENTER-DEPLOYMENT.md` - Overview of datacenter simulation
- `ansible/` - All configuration via Ansible
- `topology.yml` - Current topology with SR Linux

## Restoration

If you need to restore any of these files, they're available here. However, they may need updates to work with the current lab setup.
