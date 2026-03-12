# Migration to gNMIc-Only Stack - COMPLETE ✅

## What Was Done

Successfully migrated from Telegraf+gNMIc to gNMIc-only monitoring stack with persistent storage.

## Changes Made

### 1. ✅ Persistence Directories Created
```
monitoring/
├── grafana/data/          # Grafana persistent storage
└── prometheus/data/       # Prometheus persistent storage
```

Permissions set:
- Grafana: user 472
- Prometheus: user 65534

### 2. ✅ gNMIc Configuration Created
File: `monitoring/gnmic/gnmic-config.yml`

**Targets:**
- spine1: 172.20.20.10:57400
- spine2: 172.20.20.11:57400
- leaf1: 172.20.20.21:57400
- leaf2: 172.20.20.22:57400
- leaf3: 172.20.20.23:57400
- leaf4: 172.20.20.24:57400

**Subscriptions:**
- Interface statistics (10s interval)
- Interface state (30s interval)
- BGP statistics (30s interval)
- LLDP neighbors (60s interval)
- System resources (30s interval)

**Output:**
- Prometheus metrics on port 9273

### 3. ✅ Prometheus Configuration Updated
File: `monitoring/prometheus/prometheus.yml`

**Scrape Targets:**
- gNMIc: 172.20.20.5:9273 (10s interval)
- Prometheus self-monitoring: localhost:9090

**Retention:**
- 30 days of metrics history

### 4. ✅ Topology Updated
File: `topology.yml`

**Removed:**
- Telegraf container (no longer needed)

**Added:**
- Persistent volume binds for Grafana and Prometheus
- 30-day retention for Prometheus

**Current Stack:**
```
Network Devices (SR Linux)
    ↓ gNMI
gNMIc (collector)
    ↓ Prometheus metrics
Prometheus (storage)
    ↓ PromQL
Grafana (visualization)
```

### 5. ✅ Telegraf Archived
Old Telegraf configuration moved to: `archive/monitoring/telegraf/`

## New Monitoring Stack

### Components

| Component | IP | Port | Purpose |
|-----------|-----|------|---------|
| Grafana | 172.20.20.2 | 3000 | Visualization |
| Prometheus | 172.20.20.3 | 9090 | Metrics storage |
| gNMIc | 172.20.20.5 | 9273 | Telemetry collector |

### Data Flow

```
SR Linux Devices
    ↓ gNMI subscriptions
gNMIc (collects & transforms)
    ↓ Prometheus format
Prometheus (stores & queries)
    ↓ PromQL queries
Grafana (displays)
```

## Next Steps

### 1. Redeploy the Lab

```bash
# From your Mac
orb -m clab

# In the VM
cd /path/to/containerlab
./destroy.sh
./deploy.sh
```

### 2. Verify gNMIc is Collecting

```bash
# Check gNMIc metrics endpoint
curl http://172.20.20.5:9273/metrics

# Should see metrics like:
# gnmic_interface_stats_in_octets{...}
# gnmic_bgp_stats_session_state{...}
```

### 3. Verify Prometheus is Scraping

```bash
# Check Prometheus targets
curl http://172.20.20.3:9090/api/v1/targets

# Check metrics in Prometheus
curl 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_stats_in_octets'
```

### 4. Access Grafana

```bash
# Open in browser
open http://localhost:3000

# Login: admin / admin
```

### 5. Update Grafana Dashboards

If you have existing dashboards, update metric names:

**Old (Telegraf):**
```promql
rate(interface_in_octets[5m])
```

**New (gNMIc):**
```promql
rate(gnmic_interface_stats_in_octets[5m])
```

## Benefits Achieved

✅ **Simpler Stack**: One collector instead of two
✅ **Native gNMI**: Built specifically for gNMI telemetry
✅ **Persistent Data**: Survives lab restarts
✅ **30-Day Retention**: Historical data for troubleshooting
✅ **Better Performance**: Optimized for network telemetry
✅ **OpenConfig Native**: First-class OpenConfig support

## Verification Checklist

After redeploying, verify:

- [ ] gNMIc container is running
- [ ] gNMIc is exposing metrics on port 9273
- [ ] Prometheus is scraping gNMIc
- [ ] Grafana can query Prometheus
- [ ] Data persists after lab restart
- [ ] All 6 devices are being monitored

## Troubleshooting

### gNMIc Not Starting

```bash
# Check logs
docker logs clab-gnmi-clos-gnmic

# Common issues:
# - Config file syntax error
# - Can't reach devices (check IPs)
# - Authentication failure (check credentials)
```

### No Metrics in Prometheus

```bash
# Check Prometheus targets
curl http://172.20.20.3:9090/api/v1/targets | jq

# Check if gNMIc is reachable
curl http://172.20.20.5:9273/metrics

# Check Prometheus logs
docker logs clab-gnmi-clos-prometheus
```

### Permission Issues

```bash
# Fix Grafana permissions
sudo chown -R 472:472 monitoring/grafana/data

# Fix Prometheus permissions
sudo chown -R 65534:65534 monitoring/prometheus/data
```

## Rollback Plan

If you need to go back to Telegraf:

```bash
# 1. Restore Telegraf config
cp -r archive/monitoring/telegraf monitoring/

# 2. Restore old topology
git checkout topology.yml

# 3. Redeploy
./destroy.sh && ./deploy.sh
```

## Files Modified

- ✏️ `topology.yml` - Removed Telegraf, added persistence
- ✏️ `monitoring/prometheus/prometheus.yml` - Updated scrape config
- ✨ `monitoring/gnmic/gnmic-config.yml` - Created new config
- 📦 `archive/monitoring/telegraf/` - Archived old config

## Documentation

- [MONITORING-PERSISTENCE.md](MONITORING-PERSISTENCE.md) - Persistence strategy
- [MIGRATE-TO-GNMIC.md](MIGRATE-TO-GNMIC.md) - Migration guide
- [MIGRATION-COMPLETE.md](MIGRATION-COMPLETE.md) - This file

## Success Criteria

Migration is successful when:

1. ✅ Lab deploys without errors
2. ✅ gNMIc collects metrics from all 6 devices
3. ✅ Prometheus stores metrics
4. ✅ Grafana displays metrics
5. ✅ Data persists after `./destroy.sh && ./deploy.sh`

---

**Status: Ready to Deploy** 🚀

Run `./destroy.sh && ./deploy.sh` to activate the new monitoring stack!
