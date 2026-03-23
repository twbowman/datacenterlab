# IP Address Reference

## Access Methods

### From Local Machine (via SSH tunnels)

Use `./lab tunnel` to open SSH tunnels, then access via localhost:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **gNMIc Metrics**: http://localhost:9273/metrics

### From Remote Server (direct container access)

When running commands on the remote server (via `./lab exec` or `./lab ssh`), use container IPs:

- **Grafana**: http://172.20.20.2:3000
- **Prometheus**: http://172.20.20.3:9090
- **gNMIc**: http://172.20.20.5:9273/metrics

## Network Device Management IPs

| Device | Management IP | gNMI Port |
|--------|--------------|-----------|
| spine1 | 172.20.20.10 | 57400 |
| spine2 | 172.20.20.11 | 57400 |
| leaf1  | 172.20.20.21 | 57400 |
| leaf2  | 172.20.20.22 | 57400 |
| leaf3  | 172.20.20.23 | 57400 |
| leaf4  | 172.20.20.24 | 57400 |

## Troubleshooting

If you can't connect to Prometheus/Grafana:

1. Ensure tunnels are open: `./lab tunnel`
2. Check services are running: `./lab status`
3. Verify on the server: `./lab exec "docker ps | grep -E 'prometheus|grafana'"`
