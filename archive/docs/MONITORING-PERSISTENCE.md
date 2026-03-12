# Monitoring Data Persistence Strategy

## Problem

By default, ContainerLab containers lose all data when destroyed. This means:
- Grafana dashboards and settings are lost
- Prometheus metrics history is lost
- Historical data for troubleshooting is unavailable

## Solution: Docker Volumes

Use Docker volumes to persist data on the host filesystem.

## Implementation

### Option 1: Local Directory Binds (Recommended for Labs)

Mount local directories to store persistent data.

#### Updated Topology

```yaml
nodes:
  grafana:
    kind: linux
    image: grafana/grafana:latest
    mgmt-ipv4: 172.20.20.2
    ports:
      - 3000:3000
    binds:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/data:/var/lib/grafana              # Persistent data
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
      - ./monitoring/prometheus/data:/prometheus              # Persistent data
    cmd: --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus
  
  telegraf:
    kind: linux
    image: telegraf:latest
    mgmt-ipv4: 172.20.20.4
    ports:
      - 8888:8888
    binds:
      - ./monitoring/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf
  
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

#### Setup Script

```bash
#!/bin/bash
# setup-monitoring-persistence.sh

# Create directories for persistent data
mkdir -p monitoring/grafana/data
mkdir -p monitoring/prometheus/data

# Set proper permissions (Grafana runs as user 472)
sudo chown -R 472:472 monitoring/grafana/data

# Prometheus runs as user 65534 (nobody)
sudo chown -R 65534:65534 monitoring/prometheus/data

echo "Monitoring persistence directories created"
```

### Option 2: Named Docker Volumes (Recommended for Production)

Use Docker named volumes for better isolation and management.

#### Create Volumes

```bash
# Create named volumes
docker volume create grafana-data
docker volume create prometheus-data

# List volumes
docker volume ls

# Inspect volume
docker volume inspect grafana-data
```

#### Updated Topology (Named Volumes)

```yaml
nodes:
  grafana:
    kind: linux
    image: grafana/grafana:latest
    mgmt-ipv4: 172.20.20.2
    ports:
      - 3000:3000
    binds:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana                         # Named volume
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
      - prometheus-data:/prometheus                           # Named volume
    cmd: --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus
```

## What Gets Persisted

### Grafana
- **Dashboards**: Custom dashboards you create
- **Data sources**: Configured data sources
- **Users**: User accounts and permissions
- **Plugins**: Installed plugins
- **Settings**: All Grafana settings

### Prometheus
- **Metrics**: Time-series data collected from gNMIc
- **Retention**: Configurable (default 15 days)
- **Rules**: Recording and alerting rules
- **Targets**: Scrape target status

### gNMIc
- **No persistence needed**: gNMIc is stateless (collector only)
- Configuration is already persisted via bind mount
- Metrics are forwarded to Prometheus for storage
- gNMIc collects from network devices and exports to Prometheus

## Data Retention Configuration

### Prometheus Retention

```yaml
prometheus:
  cmd: >
    --config.file=/etc/prometheus/prometheus.yml 
    --storage.tsdb.path=/prometheus
    --storage.tsdb.retention.time=30d              # Keep 30 days
    --storage.tsdb.retention.size=10GB             # Max 10GB
```

### Grafana Data Source Settings

In Grafana, configure Prometheus data source:
- **Time range**: Set default time range
- **Query timeout**: Adjust for large queries
- **Cache**: Enable query caching

## Backup Strategy

### Manual Backup

```bash
#!/bin/bash
# backup-monitoring.sh

BACKUP_DIR="./monitoring-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup Grafana data
cp -r monitoring/grafana/data "$BACKUP_DIR/grafana"

# Backup Prometheus data
cp -r monitoring/prometheus/data "$BACKUP_DIR/prometheus"

echo "Backup created: $BACKUP_DIR"
```

### Automated Backup (Cron)

```bash
# Add to crontab
0 2 * * * /path/to/backup-monitoring.sh
```

### Docker Volume Backup

```bash
# Backup named volume
docker run --rm \
  -v grafana-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore named volume
docker run --rm \
  -v grafana-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/grafana-backup-20240310.tar.gz -C /data
```

## Testing Persistence

```bash
# 1. Deploy lab
./deploy.sh

# 2. Create some data
# - Add custom Grafana dashboard
# - Let Prometheus collect metrics for a while

# 3. Destroy lab
./destroy.sh

# 4. Redeploy lab
./deploy.sh

# 5. Verify data persists
# - Check Grafana dashboards still exist
# - Check Prometheus has historical data
```

## Disk Space Management

### Check Disk Usage

```bash
# Check directory sizes
du -sh monitoring/grafana/data
du -sh monitoring/prometheus/data

# Check Docker volume sizes
docker system df -v
```

### Clean Old Data

```bash
# Prometheus automatically manages retention
# But you can manually clean if needed

# Stop Prometheus
docker stop clab-gnmi-clos-prometheus

# Clean old data (keeps last 7 days)
find monitoring/prometheus/data -type f -mtime +7 -delete

# Restart Prometheus
docker start clab-gnmi-clos-prometheus
```

## Recommended Configuration

### For Lab/Development

```yaml
# Use local directories
binds:
  - ./monitoring/grafana/data:/var/lib/grafana
  - ./monitoring/prometheus/data:/prometheus

# Short retention (save disk space)
prometheus:
  cmd: >
    --config.file=/etc/prometheus/prometheus.yml 
    --storage.tsdb.path=/prometheus
    --storage.tsdb.retention.time=7d
```

### For Production/Long-term Testing

```yaml
# Use named volumes
binds:
  - grafana-data:/var/lib/grafana
  - prometheus-data:/prometheus

# Longer retention
prometheus:
  cmd: >
    --config.file=/etc/prometheus/prometheus.yml 
    --storage.tsdb.path=/prometheus
    --storage.tsdb.retention.time=90d
    --storage.tsdb.retention.size=50GB
```

## Migration Path

### Step 1: Create Directories

```bash
mkdir -p monitoring/grafana/data
mkdir -p monitoring/prometheus/data
sudo chown -R 472:472 monitoring/grafana/data
sudo chown -R 65534:65534 monitoring/prometheus/data
```

### Step 2: Update Topology

Add the binds to your `topology.yml` as shown above.

### Step 3: Redeploy

```bash
./destroy.sh
./deploy.sh
```

### Step 4: Verify

```bash
# Check mounts
docker inspect clab-gnmi-clos-grafana | grep -A 10 Mounts
docker inspect clab-gnmi-clos-prometheus | grep -A 10 Mounts

# Check data directories
ls -la monitoring/grafana/data
ls -la monitoring/prometheus/data
```

## Troubleshooting

### Permission Issues

```bash
# Grafana permission denied
sudo chown -R 472:472 monitoring/grafana/data

# Prometheus permission denied
sudo chown -R 65534:65534 monitoring/prometheus/data
```

### Data Not Persisting

```bash
# Check if bind mount is working
docker inspect clab-gnmi-clos-grafana | grep -A 10 Mounts

# Check if data is being written
ls -la monitoring/grafana/data
```

### Disk Space Issues

```bash
# Check available space
df -h

# Clean old Prometheus data
docker exec clab-gnmi-clos-prometheus \
  find /prometheus -type f -mtime +7 -delete
```

## Best Practices

1. **Use local directories for labs**: Easier to backup and inspect
2. **Use named volumes for production**: Better isolation and management
3. **Set appropriate retention**: Balance between history and disk space
4. **Regular backups**: Automate backups for important data
5. **Monitor disk usage**: Set up alerts for disk space
6. **Document retention policies**: Know how long data is kept
7. **Test restore procedures**: Ensure backups actually work

## Summary

**Quick Setup (Recommended):**

```bash
# 1. Create directories
mkdir -p monitoring/{grafana,prometheus}/data
sudo chown -R 472:472 monitoring/grafana/data
sudo chown -R 65534:65534 monitoring/prometheus/data

# 2. Update topology.yml to add binds (see above)

# 3. Redeploy
./destroy.sh && ./deploy.sh

# 4. Data now persists across reboots!
```

Your monitoring data will survive lab restarts, container recreations, and system reboots.

**Note:** Consider migrating from Telegraf to gNMIc-only. See [MIGRATE-TO-GNMIC.md](MIGRATE-TO-GNMIC.md) for details.
