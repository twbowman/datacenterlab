# Monitoring Configuration Files

## Directory Structure

```
monitoring/
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       │   ├── dashboards.yml          # Dashboard provider config
│       │   └── network-overview.json   # Network dashboard definition
│       └── datasources/
│           └── prometheus.yml          # Prometheus datasource (auto-configured)
├── prometheus/
│   ├── prometheus.yml                  # Prometheus scrape configuration
│   └── alerts.yml                      # Alert rules
└── telegraf/
    └── telegraf.conf                   # Telegraf gNMI collector config

```

## File Purposes

### Grafana Files

- **prometheus.yml** - Auto-configures Prometheus datasource pointing to 172.20.20.3:9090
- **dashboards.yml** - Tells Grafana where to find dashboard JSON files
- **network-overview.json** - Pre-built dashboard for network monitoring

### Prometheus Files

- **prometheus.yml** - Defines what metrics to scrape (Telegraf, Prometheus itself, network devices)
- **alerts.yml** - Alert rules for network monitoring

### Telegraf Files

- **telegraf.conf** - Configuration for collecting gNMI telemetry from network devices

## What Was Removed

- ❌ `grafana.ini` - Not needed, using environment variables instead
- ❌ `ldap.toml` - Not needed for this setup
- ❌ `datasources.yml` - Old config with wrong URLs, replaced with prometheus.yml
- ❌ Sample YAML files - Just examples, not needed
- ❌ Debug scripts - Temporary troubleshooting scripts
- ❌ Empty directories - Cleaned up

## Container Configuration

All monitoring now uses official containers configured in `topology.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  mgmt-ipv4: 172.20.20.2
  ports: [3000:3000]
  env:
    GF_SECURITY_ADMIN_PASSWORD: admin

prometheus:
  image: prom/prometheus:latest
  mgmt-ipv4: 172.20.20.3
  ports: [9090:9090]

telegraf:
  image: telegraf:latest
  mgmt-ipv4: 172.20.20.4
  ports: [8888:8888]
```

## Next Steps

Deploy the lab with the new monitoring setup:

```bash
./redeploy-monitoring.sh
```
