# Telemetry Setup Guide

## Current Status

### ✅ Working
- SR Linux switches fully configured (interfaces, BGP)
- All BGP sessions established
- gNMI accessible on all switches (port 57400 with TLS)
- Ansible playbooks for configuration and verification
- Monitoring stack deployed (Grafana, Prometheus, Telegraf)

### ⚠️ Issue
- Telegraf's gNMI plugin cannot handle SR Linux's self-signed TLS certificates
- Port 57401 (insecure gRPC) is configured but not listening

## Recommended Solution: Use gnmic Collector

`gnmic` is a dedicated gNMI client that properly handles TLS and exports to Prometheus.

### Deploy gnmic Collector

gnmic is now part of the ContainerLab topology. To deploy:

```bash
# From OrbStack - redeploy the lab
orb exec bash deploy-gnmic-collector.sh

# Or manually
orb exec sudo containerlab deploy -t topology.yml --reconfigure
```

This will:
1. Start gnmic as container `clab-gnmi-clos-gnmic` (IP: 172.20.20.5)
2. Subscribe to all 6 switches via gNMI
3. Collect interface stats, oper-state, and BGP state
4. Export metrics to Prometheus format on port 9273

### Verify Telemetry

```bash
# Check gnmic is collecting data
orb exec docker logs -f clab-gnmi-clos-gnmic

# Check Prometheus metrics
orb exec curl -s http://172.20.20.5:9273/metrics | grep gnmi

# Or from Mac
curl -s http://localhost:9273/metrics | grep gnmi

# Restart Prometheus to pick up new scrape target
orb exec docker restart clab-gnmi-clos-prometheus
```

### Access Grafana

```
URL: http://localhost:3000
Username: admin
Password: admin
```

Create dashboards using metrics with prefix `gnmi_*`

## Alternative: Keep Current Setup

If you want to keep Telegraf:
- It will collect system metrics (CPU, memory, disk)
- But won't get gNMI telemetry from switches
- Prometheus is already configured to scrape Telegraf on port 8888

## Architecture

```
SR Linux Switches (port 57400 gNMI/TLS)
    ↓ (gNMI Subscribe)
gnmic Collector (port 9273 Prometheus)
    ↓ (HTTP Scrape)
Prometheus (port 9090)
    ↓ (Query)
Grafana (port 3000)
```

## Files

- `monitoring/gnmic/gnmic-config.yml` - gnmic configuration
- `deploy-gnmic-collector.sh` - Deployment script
- `monitoring/prometheus/prometheus.yml` - Updated to scrape gnmic
- `ansible/configure-gnmi.yml` - Ansible playbook for switch config
- `ansible/verify-simple.yml` - Verification playbook

## Next Steps

1. Deploy gnmic collector
2. Verify metrics in Prometheus
3. Create Grafana dashboards
4. Optional: Add more subscriptions to gnmic-config.yml for additional telemetry paths
