# Migrate from Telegraf to gNMIc

## Why gNMIc?

- **Native gNMI**: Built specifically for gNMI telemetry
- **OpenConfig**: Better support for OpenConfig models
- **Lightweight**: Smaller footprint than Telegraf
- **Prometheus Export**: Direct Prometheus metrics export
- **Modern**: Active development, gNMI-focused

## Current Stack vs New Stack

### Current (Telegraf + gNMIc)
```
Network Devices (gNMI)
    ↓
Telegraf (collector) → InfluxDB → Grafana
    ↓
gNMIc (collector) → Prometheus → Grafana
```

### New (gNMIc Only)
```
Network Devices (gNMI)
    ↓
gNMIc (collector) → Prometheus → Grafana
```

## Migration Steps

### Step 1: Remove Telegraf from Topology

Edit `topology.yml` and remove the telegraf node:

```yaml
# REMOVE THIS:
telegraf:
  kind: linux
  image: telegraf:latest
  mgmt-ipv4: 172.20.20.4
  ports:
    - 8888:8888
  binds:
    - ./monitoring/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf
```

### Step 2: Update Prometheus Configuration

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # gNMIc metrics endpoint
  - job_name: 'gnmic'
    static_configs:
      - targets: ['172.20.20.5:9273']
        labels:
          source: 'gnmic'
  
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### Step 3: Configure gNMIc

Create/update `monitoring/gnmic/gnmic-config.yml`:

```yaml
# gNMIc configuration for SR Linux devices
username: admin
password: NokiaSrl1!
skip-verify: true
encoding: json_ietf

targets:
  spine1:172.20.20.10:57400:
  spine2:172.20.20.11:57400:
  leaf1:172.20.20.21:57400:
  leaf2:172.20.20.22:57400:
  leaf3:172.20.20.23:57400:
  leaf4:172.20.20.24:57400:

subscriptions:
  # Interface statistics
  interfaces:
    paths:
      - /interface[name=*]/statistics
      - /interface[name=*]/subinterface[index=*]/statistics
    mode: sample
    sample-interval: 10s
  
  # BGP statistics
  bgp:
    paths:
      - /network-instance[name=*]/protocols/bgp/neighbor[neighbor-address=*]/statistics
    mode: sample
    sample-interval: 30s
  
  # LLDP neighbors
  lldp:
    paths:
      - /system/lldp/interface[name=*]/neighbor[id=*]
    mode: sample
    sample-interval: 60s
  
  # System info
  system:
    paths:
      - /system/memory
      - /system/cpu
    mode: sample
    sample-interval: 30s

outputs:
  # Export to Prometheus
  prometheus:
    type: prometheus
    listen: :9273
    path: /metrics
    metric-prefix: gnmic
    append-subscription-name: true
    export-timestamps: true
    strings-as-labels: true
```

### Step 4: Update Grafana Data Sources

In Grafana, remove InfluxDB data source and keep only Prometheus:

1. Go to Configuration → Data Sources
2. Delete InfluxDB data source (if exists)
3. Keep Prometheus data source pointing to `http://172.20.20.3:9090`

### Step 5: Redeploy

```bash
# Destroy current lab
./destroy.sh

# Deploy with new configuration
./deploy.sh
```

### Step 6: Verify

```bash
# Check gNMIc is collecting metrics
curl http://172.20.20.5:9273/metrics

# Check Prometheus is scraping gNMIc
curl http://172.20.20.3:9090/api/v1/targets

# Check metrics in Prometheus
curl http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_statistics_in_octets
```

## Updated Topology (Clean)

```yaml
nodes:
  # === Monitoring Stack ===
  grafana:
    kind: linux
    image: grafana/grafana:latest
    mgmt-ipv4: 172.20.20.2
    ports:
      - 3000:3000
    binds:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/data:/var/lib/grafana              # Persistent
    env:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_SECURITY_ADMIN_USER: admin
  
  prometheus:
    kind: linux
    image: prom/prometheus:latest
    mgmt-ipv4: 172.20.20.3
    ports:
      - 9090:9090
    binds:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/prometheus/alerts.yml:/etc/prometheus/alerts.yml
      - ./monitoring/prometheus/data:/prometheus                # Persistent
    cmd: >
      --config.file=/etc/prometheus/prometheus.yml 
      --storage.tsdb.path=/prometheus
      --storage.tsdb.retention.time=30d
  
  gnmic:
    kind: linux
    image: ghcr.io/openconfig/gnmic:latest
    mgmt-ipv4: 172.20.20.5
    ports:
      - 9273:9273
    binds:
      - ./monitoring/gnmic/gnmic-config.yml:/gnmic-config.yml:ro
    cmd: --config /gnmic-config.yml subscribe
```

## Benefits of gNMIc-Only Stack

1. **Simpler**: One collector instead of two
2. **Native gNMI**: Built for gNMI from the ground up
3. **Better Performance**: Optimized for network telemetry
4. **OpenConfig**: First-class OpenConfig support
5. **Prometheus Native**: Direct Prometheus export
6. **Less Resources**: Fewer containers to run

## Metric Mapping

### Telegraf → gNMIc

| Telegraf Metric | gNMIc Metric |
|----------------|--------------|
| `interface_in_octets` | `gnmic_interface_statistics_in_octets` |
| `interface_out_octets` | `gnmic_interface_statistics_out_octets` |
| `bgp_peer_state` | `gnmic_bgp_neighbor_session_state` |
| `lldp_neighbor_count` | `gnmic_lldp_neighbor_count` |

Update your Grafana dashboards to use the new metric names.

## Grafana Dashboard Updates

### Old Query (Telegraf)
```promql
rate(interface_in_octets{interface="ethernet-1/1"}[5m])
```

### New Query (gNMIc)
```promql
rate(gnmic_interface_statistics_in_octets{interface="ethernet-1/1"}[5m])
```

## Troubleshooting

### gNMIc Not Collecting Metrics

```bash
# Check gNMIc logs
docker logs clab-gnmi-clos-gnmic

# Test gNMI connection manually
docker exec clab-gnmi-clos-gnmic gnmic -a 172.20.20.10:57400 \
  -u admin -p NokiaSrl1! --insecure capabilities
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
curl http://172.20.20.3:9090/api/v1/targets | jq

# Check Prometheus logs
docker logs clab-gnmi-clos-prometheus
```

### No Metrics in Grafana

```bash
# Check if metrics exist in Prometheus
curl http://172.20.20.3:9090/api/v1/label/__name__/values | jq | grep gnmic

# Test query
curl 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_statistics_in_octets'
```

## Cleanup

After migration, you can remove Telegraf files:

```bash
# Archive old Telegraf config
mkdir -p archive/telegraf
mv monitoring/telegraf archive/

# Or just remove
rm -rf monitoring/telegraf
```

## Summary

**Quick Migration:**

1. Remove Telegraf from `topology.yml`
2. Update `monitoring/prometheus/prometheus.yml` to scrape gNMIc only
3. Configure `monitoring/gnmic/gnmic-config.yml` with all subscriptions
4. Redeploy: `./destroy.sh && ./deploy.sh`
5. Update Grafana dashboards with new metric names

**Result:** Simpler, more efficient monitoring stack using gNMIc as the single telemetry collector.
