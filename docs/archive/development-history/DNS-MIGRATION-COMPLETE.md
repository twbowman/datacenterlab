# DNS Migration Complete

## Summary

Replaced all hardcoded IP addresses in monitoring stack configuration with DNS names for better maintainability and production-readiness.

## Changes Made

### 1. Grafana Datasource Configuration
**File**: `monitoring/grafana/provisioning/datasources/prometheus.yml`

**Before**:
```yaml
url: http://172.20.20.3:9090
```

**After**:
```yaml
url: http://clab-monitoring-prometheus:9090
```

### 2. Prometheus Scrape Configuration
**File**: `monitoring/prometheus/prometheus.yml`

**Before**:
```yaml
- targets: ['172.20.20.5:9273']
```

**After**:
```yaml
- targets: ['clab-monitoring-gnmic:9273']
```

### 3. Python Analysis Script
**File**: `analyze-link-utilization.py`

**Before**:
```python
PROMETHEUS_URL = "http://172.20.20.3:9090"  # Prometheus container IP
```

**After**:
```python
PROMETHEUS_URL = "http://clab-monitoring-prometheus:9090"  # Prometheus container DNS name
```

## DNS Names Used

All monitoring containers use containerlab's automatic DNS naming:

| Service | DNS Name | IP Address | Port |
|---------|----------|------------|------|
| Grafana | `clab-monitoring-grafana` | 172.20.20.2 | 3000 |
| Prometheus | `clab-monitoring-prometheus` | 172.20.20.3 | 9090 |
| gNMIc | `clab-monitoring-gnmic` | 172.20.20.5 | 9273 |

Network devices also use DNS:

| Device | DNS Name | IP Address | gNMI Port |
|--------|----------|------------|-----------|
| spine1 | `clab-gnmi-clos-spine1` | 172.20.20.10 | 57400 |
| spine2 | `clab-gnmi-clos-spine2` | 172.20.20.11 | 57400 |
| leaf1 | `clab-gnmi-clos-leaf1` | 172.20.20.21 | 57400 |
| leaf2 | `clab-gnmi-clos-leaf2` | 172.20.20.22 | 57400 |
| leaf3 | `clab-gnmi-clos-leaf3` | 172.20.20.23 | 57400 |
| leaf4 | `clab-gnmi-clos-leaf4` | 172.20.20.24 | 57400 |

## Benefits of DNS

### 1. Production-Ready
- Matches real-world deployments
- No hardcoded IPs in configuration
- Easier to understand and maintain

### 2. Flexibility
- IP addresses can change without config updates
- Easier to move containers or services
- Better for multi-environment deployments

### 3. Readability
- `clab-monitoring-prometheus` is clearer than `172.20.20.3`
- Self-documenting configuration
- Easier troubleshooting

### 4. Consistency
- All components use DNS
- Matches containerlab's naming convention
- Aligns with Kubernetes/Docker best practices

## Verification

### Test DNS Resolution
```bash
# From Grafana container
orb -m clab docker exec clab-monitoring-grafana nslookup clab-monitoring-prometheus

# From Prometheus container
orb -m clab docker exec clab-monitoring-prometheus nslookup clab-monitoring-gnmic

# From any container
orb -m clab docker exec clab-monitoring-grafana nslookup clab-gnmi-clos-spine1
```

### Test Connectivity
```bash
# Grafana can reach Prometheus
orb -m clab docker exec clab-monitoring-grafana wget -qO- http://clab-monitoring-prometheus:9090/api/v1/targets

# Prometheus can reach gNMIc
orb -m clab docker exec clab-monitoring-prometheus wget -qO- http://clab-monitoring-gnmic:9273/metrics | head -10

# Python script can reach Prometheus
orb -m clab ./lab analyze-links
```

### Check Grafana Datasource
1. Open Grafana: http://172.20.20.2:3000 (or http://clab-monitoring-grafana:3000 from within containers)
2. Go to Configuration → Data Sources → Prometheus
3. Verify URL shows: `http://clab-monitoring-prometheus:9090`
4. Click "Save & Test" - should show green checkmark

### Check Prometheus Targets
1. Open Prometheus: http://172.20.20.3:9090 (or http://clab-monitoring-prometheus:9090 from within containers)
2. Go to Status → Targets
3. Verify gnmic target shows: `clab-monitoring-gnmic:9273`
4. Status should be "UP"

## Documentation Notes

Some documentation files still reference IP addresses in examples and troubleshooting commands. This is intentional:

- **IP-ADDRESS-REFERENCE.md** - Documents the IP addressing scheme (reference)
- **GRAFANA-TROUBLESHOOTING.md** - Shows both IP and DNS options for troubleshooting
- **DNS-NAMING-FIX-SUMMARY.md** - Historical documentation of the DNS implementation

These files serve as reference and don't need to be updated since they're showing examples that work from outside the container network.

## Configuration Files Updated

✅ `monitoring/grafana/provisioning/datasources/prometheus.yml` - Grafana datasource
✅ `monitoring/prometheus/prometheus.yml` - Prometheus scrape targets
✅ `monitoring/gnmic/gnmic-config.yml` - gNMIc device targets (already using DNS)
✅ `analyze-link-utilization.py` - Python script Prometheus URL

## No Changes Needed

These files already use DNS or don't need changes:
- `monitoring/gnmic/gnmic-config.yml` - Already uses DNS (clab-gnmi-clos-spine1, etc.)
- Dashboard JSON files - Use Prometheus datasource (no direct IPs)
- Ansible playbooks - Use inventory variables (no hardcoded IPs)

## Rollback (if needed)

If DNS resolution fails for any reason, you can rollback by:

1. Restore IP addresses in the three files above
2. Restart services: `docker restart clab-monitoring-prometheus clab-monitoring-grafana`

However, DNS should always work within the containerlab network as it's managed by Docker's embedded DNS server.

## Related Documentation

- `DNS-NAMING-FIX-SUMMARY.md` - Initial DNS implementation for gNMIc targets
- `GRAFANA-DASHBOARD-FIX.md` - Dashboard device name fix
- `IP-ADDRESS-REFERENCE.md` - IP addressing scheme reference
- `TELEMETRY-STRATEGY.md` - Overall telemetry strategy
