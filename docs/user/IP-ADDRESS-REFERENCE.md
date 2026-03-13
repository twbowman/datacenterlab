# IP Address Reference

This document clarifies the IP addresses used in the lab environment.

## Container IP Addresses

The monitoring stack containers have fixed IP addresses on the management network (172.20.20.0/24):

| Container | IP Address | Port | Service |
|-----------|------------|------|---------|
| Grafana | 172.20.20.2 | 3000 | Web UI |
| Prometheus | 172.20.20.3 | 9090 | Web UI & API |
| gNMIc | 172.20.20.5 | 9273 | Metrics endpoint |

## Network Devices

| Device | IP Address | gNMI Port |
|--------|------------|-----------|
| spine1 | 172.20.20.10 | 57400 |
| spine2 | 172.20.20.11 | 57400 |
| leaf1 | 172.20.20.21 | 57400 |
| leaf2 | 172.20.20.22 | 57400 |
| leaf3 | 172.20.20.23 | 57400 |
| leaf4 | 172.20.20.24 | 57400 |

## Access Methods

### From Host Machine (Outside orb VM)

When accessing from your host machine (before running `orb -m clab`), use localhost with port forwarding:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **gNMIc Metrics**: http://localhost:9273/metrics

### From Inside orb VM (For Scripts)

When running scripts inside the orb VM (after `orb -m clab`), use container IPs:

- **Grafana**: http://172.20.20.2:3000
- **Prometheus**: http://172.20.20.3:9090
- **gNMIc Metrics**: http://172.20.20.5:9273/metrics

## Why Two Different Addresses?

The orb VM uses Docker networking with port forwarding:

1. **Container IPs (172.20.20.x)**: Direct access to containers on the Docker bridge network
2. **Localhost**: Port forwarding from host machine to containers

Scripts that run inside the orb VM (like `analyze-link-utilization.py`) must use container IPs because they're running in the same Docker network context.

## Files Updated

The following files have been updated to use correct container IPs:

1. `analyze-link-utilization.py` - Uses 172.20.20.3 for Prometheus
2. `check-monitoring.sh` - Uses 172.20.20.2, 172.20.20.3, 172.20.20.5
3. `check-metrics.sh` - Uses 172.20.20.3 and 172.20.20.5
4. `lab` - Shows both localhost and container IPs in status
5. `QUICK-START-LINK-ANALYSIS.md` - Documents both access methods
6. `LINK-UTILIZATION-TESTING.md` - Uses container IPs in examples

## Troubleshooting

### Cannot connect to Prometheus

If you see "Cannot connect to Prometheus at http://172.20.20.3:9090":

1. Verify you're inside the orb VM: `orb -m clab`
2. Check Prometheus is running: `docker ps | grep prometheus`
3. Verify container IP: `docker inspect clab-monitoring-prometheus | grep IPAddress`
4. Test connectivity: `curl http://172.20.20.3:9090/api/v1/status/config`

### Wrong IP in topology

If container IPs don't match, check `topology-monitoring.yml`:

```yaml
prometheus:
  mgmt-ipv4: 172.20.20.3  # Should match
```

### Port forwarding not working

If localhost access doesn't work from host machine:

1. Check port mappings: `docker port clab-monitoring-prometheus`
2. Verify orb VM is forwarding ports
3. Try accessing from inside orb VM using container IPs instead
