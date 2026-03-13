# Troubleshooting Guide

This guide provides solutions to common issues, debugging techniques, and vendor-specific troubleshooting procedures.

## Quick Diagnostics

### Check Lab Status

```bash
# Check all containers
docker ps --filter "name=clab-"

# Check specific lab
docker ps --filter "name=clab-gnmi-clos"

# Check monitoring stack
docker ps --filter "name=clab-monitoring"
```

### Check Device Reachability

```bash
# Ping device management IP
ping -c 3 172.20.20.10

# Test gNMI connectivity
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities
```

### Check Logs

```bash
# Device logs
docker logs clab-gnmi-clos-spine1

# gNMIc logs
docker logs clab-monitoring-gnmic

# Prometheus logs
docker logs clab-monitoring-prometheus

# Grafana logs
docker logs clab-monitoring-grafana
```

## Deployment Issues

### Issue: Containerlab Deploy Fails

**Symptoms**:
- `containerlab deploy` command fails
- Error messages about missing images or invalid topology

**Diagnosis**:
```bash
# Validate topology file
python3 scripts/validate-topology.py topology.yml

# Check Docker is running
docker info

# Check available images
docker images | grep srlinux
```

**Solutions**:

**Missing Images**:
```bash
# Pull SR Linux image
docker pull ghcr.io/nokia/srlinux:latest

# For other vendors, follow vendor-specific image instructions
```

**Invalid Topology**:
```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('topology.yml'))"

# Common issues:
# - Missing 'kind' field
# - Invalid interface names
# - Circular link dependencies
```

**Insufficient Resources**:
```bash
# Check Docker resources
docker system df

# Clean up old containers/images
docker system prune -a
```

### Issue: Devices Don't Start

**Symptoms**:
- Containers start but immediately exit
- Containers stuck in "Restarting" state

**Diagnosis**:
```bash
# Check container status
docker ps -a --filter "name=clab-gnmi-clos-spine1"

# Check logs for errors
docker logs clab-gnmi-clos-spine1

# Check resource usage
docker stats clab-gnmi-clos-spine1
```

**Solutions**:

**Startup Config Errors**:
```bash
# Check startup config syntax
cat configs/spine1/srlinux/config.json | jq .

# Use minimal config (hostname + gNMI only)
```

**Resource Constraints**:
```bash
# Check available memory
free -h

# Check available disk
df -h

# Increase Docker resources (macOS/Windows)
# Docker Desktop → Settings → Resources
```

**Image Compatibility**:
```bash
# Check image architecture
docker inspect ghcr.io/nokia/srlinux:latest | grep Architecture

# On ARM Macs, ensure using ORB
orb -m clab docker ps
```

### Issue: Devices Boot Slowly

**Symptoms**:
- Devices take 5+ minutes to boot
- Ansible fails with connection timeout

**Diagnosis**:
```bash
# Check boot progress
docker logs -f clab-gnmi-clos-spine1

# Look for "All applications started successfully"
```

**Solutions**:

**Wait Longer**:
```bash
# SR Linux: 2-3 minutes
# Arista cEOS: 3-4 minutes
# SONiC: 4-5 minutes
# Juniper: 3-4 minutes

# Increase wait time in deployment scripts
sleep 300  # 5 minutes
```

**Check Resource Allocation**:
```bash
# Ensure sufficient CPU/RAM
docker stats

# Reduce number of concurrent devices
# Deploy in stages (spines first, then leafs)
```

## Configuration Issues

### Issue: Ansible Cannot Connect

**Symptoms**:
- "Failed to connect to device" errors
- "Connection timeout" errors
- "Authentication failed" errors

**Diagnosis**:
```bash
# Test gNMI connectivity
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify capabilities

# Check device is reachable
ping -c 3 172.20.20.10

# Check gNMI is enabled
docker exec clab-gnmi-clos-spine1 sr_cli "show system gnmi-server"
```

**Solutions**:

**Device Not Ready**:
```bash
# Wait for device to fully boot
sleep 180

# Check device status
docker exec clab-gnmi-clos-spine1 sr_cli "show version"
```

**Wrong Credentials**:
```bash
# Check inventory credentials
cat ansible/inventory.yml | grep -A 5 "vars:"

# Default SR Linux: admin / NokiaSrl1!
# Default Arista: admin / admin
# Default SONiC: admin / YourPaSsWoRd
```

**gNMI Not Enabled**:
```bash
# SR Linux - enable gNMI
docker exec clab-gnmi-clos-spine1 sr_cli "set / system gnmi-server admin-state enable"

# Arista - enable gNMI
docker exec clab-gnmi-clos-spine1 Cli -c "configure
management api gnmi
  transport grpc default
  no shutdown"
```

**Network Issues**:
```bash
# Check Docker network
docker network inspect clab-gnmi-mgmt

# Check device IP
docker inspect clab-gnmi-clos-spine1 | grep IPAddress
```

### Issue: Configuration Fails with Syntax Error

**Symptoms**:
- Ansible playbook fails with "invalid configuration" error
- Device rejects configuration

**Diagnosis**:
```bash
# Run Ansible with verbose output
ansible-playbook -i ansible/inventory.yml ansible/site.yml -vvv

# Check device logs
docker logs clab-gnmi-clos-spine1 | grep -i error
```

**Solutions**:

**Invalid JSON/YAML**:
```bash
# Validate JSON configuration
cat configs/spine1/srlinux/config.json | jq .

# Validate YAML inventory
python3 -c "import yaml; yaml.safe_load(open('ansible/inventory.yml'))"
```

**Vendor-Specific Syntax**:
```bash
# Check vendor documentation for correct syntax
# SR Linux: https://learn.srlinux.dev
# Arista: https://www.arista.com/en/support/product-documentation
# SONiC: https://github.com/sonic-net/SONiC/wiki
# Juniper: https://www.juniper.net/documentation/
```

**Interface Name Mismatch**:
```bash
# Verify interface names match vendor conventions
# SR Linux: ethernet-1/1
# Arista: Ethernet1
# SONiC: Ethernet0
# Juniper: ge-0/0/0

# Check topology links match inventory interfaces
```

### Issue: Configuration Not Idempotent

**Symptoms**:
- Running playbook twice produces different results
- "Changed" status on every run

**Diagnosis**:
```bash
# Run playbook twice and compare output
ansible-playbook -i ansible/inventory.yml ansible/site.yml | tee run1.log
ansible-playbook -i ansible/inventory.yml ansible/site.yml | tee run2.log
diff run1.log run2.log
```

**Solutions**:

**Use gNMI SET (Replace)**:
```yaml
# In Ansible tasks, use replace mode
- name: Configure interface
  gnmi_set:
    path: /interface[name=ethernet-1/1]
    value: "{{ interface_config }}"
    mode: replace  # Not update
```

**Check for Dynamic Values**:
```yaml
# Avoid timestamps, random values, etc.
# Bad:
timestamp: "{{ ansible_date_time.iso8601 }}"

# Good:
description: "Configured by Ansible"
```

## Monitoring Issues

### Issue: No Metrics in Grafana

**Symptoms**:
- Grafana dashboards show "No Data"
- Queries return empty results

**Diagnosis**:
```bash
# Check gNMIc is collecting
curl -s http://localhost:9273/metrics | grep network_interface

# Check Prometheus is scraping
curl -s http://localhost:9090/api/v1/targets | jq

# Check Grafana data source
# Grafana → Configuration → Data Sources → Prometheus → Test
```

**Solutions**:

**gNMIc Not Collecting**:
```bash
# Check gNMIc logs
docker logs clab-monitoring-gnmic --tail 50

# Check gNMIc can reach devices
docker exec clab-monitoring-gnmic ping -c 3 clab-gnmi-clos-spine1

# Restart gNMIc
docker restart clab-monitoring-gnmic
```

**Prometheus Not Scraping**:
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets

# Check Prometheus config
cat monitoring/prometheus/prometheus.yml

# Restart Prometheus
docker restart clab-monitoring-prometheus
```

**Grafana Data Source Issue**:
```bash
# Check Grafana can reach Prometheus
docker exec clab-monitoring-grafana wget -qO- http://clab-monitoring-prometheus:9090/api/v1/query?query=up

# Check data source URL in Grafana
# Should be: http://clab-monitoring-prometheus:9090
```

**Time Range Issue**:
```bash
# In Grafana, check time range (top right)
# Set to "Last 15 minutes" or "Last 1 hour"
# Ensure time range includes recent data
```

### Issue: Metrics Missing for Specific Vendor

**Symptoms**:
- SR Linux metrics work, but Arista metrics don't
- Some devices show data, others don't

**Diagnosis**:
```bash
# Check which devices have metrics
curl -s http://localhost:9273/metrics | grep -o 'source="[^"]*"' | sort -u

# Check gNMIc target configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 2 "targets:"

# Test gNMI connection to specific device
gnmic -a clab-gnmi-clos-arista-leaf1:57400 -u admin -p admin --skip-verify capabilities
```

**Solutions**:

**Device Not in gNMIc Config**:
```yaml
# Add device to monitoring/gnmic/gnmic-config.yml
targets:
  arista-leaf1:
    address: clab-gnmi-clos-arista-leaf1:57400
```

**Wrong Credentials**:
```yaml
# Update credentials in gNMIc config
username: admin
password: admin  # Arista default
```

**gNMI Not Enabled**:
```bash
# Arista - enable gNMI
docker exec clab-gnmi-clos-arista-leaf1 Cli -c "configure
management api gnmi
  transport grpc default
  no shutdown"
```

**Vendor-Specific Paths**:
```bash
# Check if device supports OpenConfig paths
gnmic -a clab-gnmi-clos-arista-leaf1:57400 -u admin -p admin --skip-verify get --path /interfaces

# If not, add vendor-specific subscriptions
```

### Issue: Metric Names Don't Match Documentation

**Symptoms**:
- Expected `network_interface_in_octets` but see `gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_in_octets`
- Normalization not working

**Diagnosis**:
```bash
# Check if normalization is applied
curl -s http://localhost:9273/metrics | grep "network_interface_in_octets"

# Check gNMIc processor configuration
cat monitoring/gnmic/gnmic-config.yml | grep -A 30 "normalize_interface_metrics"
```

**Solutions**:

**Processors Not Applied**:
```yaml
# Ensure processors are listed in output
outputs:
  prom:
    type: prometheus
    event-processors:
      - normalize_interface_metrics  # Must be listed
      - normalize_bgp_metrics
      - add_vendor_tags
```

**Restart gNMIc**:
```bash
# Reload configuration
docker restart clab-monitoring-gnmic

# Wait 30 seconds for collection to resume
sleep 30

# Check metrics again
curl -s http://localhost:9273/metrics | grep "network_interface_in_octets"
```

## Network Connectivity Issues

### Issue: Devices Cannot Ping Each Other

**Symptoms**:
- `ping` fails between devices
- BGP sessions don't establish
- OSPF neighbors don't form

**Diagnosis**:
```bash
# Check interface status
docker exec clab-gnmi-clos-spine1 sr_cli "show interface brief"

# Check IP addressing
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default route-table"

# Check LLDP neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"
```

**Solutions**:

**Interfaces Not Configured**:
```bash
# Run interface configuration
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags interfaces

# Verify interfaces are up
docker exec clab-gnmi-clos-spine1 sr_cli "show interface brief"
```

**IP Address Mismatch**:
```bash
# Check inventory IP addresses match topology
cat ansible/inventory.yml | grep -A 5 "interfaces:"

# Verify /31 point-to-point links
# spine1 ethernet-1/1: 10.1.1.0/31
# leaf1 ethernet-1/1: 10.1.1.1/31
```

**Link Not Connected**:
```bash
# Check containerlab links
docker exec clab-gnmi-clos-spine1 ip link show

# Check LLDP sees neighbor
docker exec clab-gnmi-clos-spine1 sr_cli "show system lldp neighbor"
```

### Issue: BGP Sessions Don't Establish

**Symptoms**:
- BGP session state is "Idle" or "Active"
- No BGP routes received

**Diagnosis**:
```bash
# Check BGP configuration
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp"

# Check BGP neighbor state
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols bgp neighbor"

# Check connectivity to BGP peer
docker exec clab-gnmi-clos-spine1 sr_cli "ping network-instance default 10.0.1.1"
```

**Solutions**:

**BGP Not Configured**:
```bash
# Run BGP configuration
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags bgp
```

**Wrong Peer IP**:
```bash
# Check inventory BGP neighbor IPs
cat ansible/inventory.yml | grep -A 5 "bgp_neighbors:"

# Verify peer IPs are reachable
docker exec clab-gnmi-clos-spine1 sr_cli "ping network-instance default 10.0.1.1"
```

**AS Number Mismatch**:
```bash
# Check local and peer AS numbers
cat ansible/inventory.yml | grep "asn:"

# For iBGP (current setup), all devices should have same ASN (65000)
# For eBGP alternative, each device would have unique ASN
```

**No Underlay Routing**:
```bash
# BGP requires underlay routing (OSPF) for next-hop resolution
# Run OSPF configuration first
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags ospf

# Verify OSPF neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf neighbor"
```

### Issue: OSPF Neighbors Don't Form

**Symptoms**:
- OSPF neighbor state is "Down" or "Init"
- No OSPF routes learned

**Diagnosis**:
```bash
# Check OSPF configuration
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf"

# Check OSPF neighbors
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf neighbor"

# Check OSPF interfaces
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf interface"
```

**Solutions**:

**OSPF Not Configured**:
```bash
# Run OSPF configuration
ansible-playbook -i ansible/inventory.yml ansible/site.yml --tags ospf
```

**Area Mismatch**:
```bash
# Check OSPF area configuration
cat ansible/inventory.yml | grep "ospf_area:"

# All interfaces in same area should use same area ID
# Typically: 0.0.0.0 (backbone area)
```

**Network Type Mismatch**:
```bash
# Point-to-point links should use network-type point-to-point
# Check configuration:
docker exec clab-gnmi-clos-spine1 sr_cli "show network-instance default protocols ospf interface ethernet-1/1"

# Should show: network-type: point-to-point
```

**MTU Mismatch**:
```bash
# Check interface MTU
docker exec clab-gnmi-clos-spine1 sr_cli "show interface ethernet-1/1"

# Ensure MTU is consistent across link
# Default: 1500 bytes
```

## Vendor-Specific Troubleshooting

### SR Linux

**Access CLI**:
```bash
docker exec -it clab-gnmi-clos-spine1 sr_cli
```

**Common Commands**:
```bash
# Show version
show version

# Show interfaces
show interface brief

# Show BGP
show network-instance default protocols bgp neighbor

# Show OSPF
show network-instance default protocols ospf neighbor

# Show routes
show network-instance default route-table

# Show LLDP
show system lldp neighbor

# Show configuration
info from running
```

**Enable gNMI**:
```bash
sr_cli
enter candidate
set / system gnmi-server admin-state enable
set / system gnmi-server network-instance mgmt admin-state enable
commit now
```

**Check gNMI Status**:
```bash
sr_cli "show system gnmi-server"
```

**Common Issues**:

- **gNMI not enabled**: Run enable commands above
- **Wrong network-instance**: gNMI must be enabled in mgmt network-instance
- **Firewall blocking**: Check if port 57400 is accessible

### Arista cEOS

**Access CLI**:
```bash
docker exec -it clab-gnmi-clos-arista-spine1 Cli
```

**Common Commands**:
```bash
# Show version
show version

# Show interfaces
show ip interface brief

# Show BGP
show ip bgp summary

# Show OSPF
show ip ospf neighbor

# Show routes
show ip route

# Show LLDP
show lldp neighbors

# Show configuration
show running-config
```

**Enable gNMI**:
```bash
Cli
configure
management api gnmi
  transport grpc default
  no shutdown
exit
write memory
```

**Check gNMI Status**:
```bash
show management api gnmi
```

**Common Issues**:

- **gNMI not enabled**: Run enable commands above
- **Wrong transport**: Ensure using `grpc default` transport
- **Certificate issues**: Use `--skip-verify` in gnmic for self-signed certs

### SONiC

**Access CLI**:
```bash
docker exec -it clab-gnmi-clos-sonic-leaf1 bash
```

**Common Commands**:
```bash
# Show version
show version

# Show interfaces
show interfaces status

# Show BGP
show ip bgp summary

# Show OSPF (if configured)
show ip ospf neighbor

# Show routes
show ip route

# Show LLDP
show lldp table
```

**Enable gNMI**:
```bash
# gNMI is typically enabled by default in SONiC
# Check status:
show gnmi status
```

**Common Issues**:

- **gNMI not running**: `sudo systemctl start gnmi`
- **Wrong port**: SONiC may use different gNMI port (check with `show gnmi status`)
- **OpenConfig support**: SONiC has limited OpenConfig support, may need native paths

### Juniper cRPD

**Access CLI**:
```bash
docker exec -it clab-gnmi-clos-juniper-leaf1 cli
```

**Common Commands**:
```bash
# Show version
show version

# Show interfaces
show interfaces terse

# Show BGP
show bgp summary

# Show OSPF
show ospf neighbor

# Show routes
show route

# Show LLDP
show lldp neighbors

# Show configuration
show configuration
```

**Enable gNMI**:
```bash
cli
configure
set system services extension-service request-response grpc clear-text port 57400
set system services extension-service request-response grpc skip-authentication
commit
```

**Check gNMI Status**:
```bash
show system services extension-service
```

**Common Issues**:

- **gNMI not enabled**: Run enable commands above
- **Authentication required**: Use `skip-authentication` for lab
- **Port conflict**: Ensure port 57400 is not in use

## Platform-Specific Issues

### macOS ARM (Apple Silicon)

**Issue: Commands Fail with "command not found"**

**Solution**: Use `orb -m clab` prefix
```bash
# Wrong
docker ps

# Correct
orb -m clab docker ps
```

**Issue: ORB VM Out of Disk Space**

**Solution**: Clean up and increase disk
```bash
# Check disk usage
orb -m clab df -h

# Clean up
orb -m clab docker system prune -a

# Increase VM disk in ORB settings
```

**Issue: File Sync Issues**

**Solution**: Restart ORB
```bash
orb restart
```

### Linux

**Issue: Permission Denied**

**Solution**: Add user to docker group
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Issue: Containerlab Requires Sudo**

**Solution**: This is expected, always use `sudo containerlab`
```bash
sudo containerlab deploy -t topology.yml
```

## Getting Help

### Collect Diagnostic Information

```bash
# System info
uname -a
docker version
containerlab version

# Container status
docker ps -a

# Container logs
docker logs clab-gnmi-clos-spine1 > spine1.log
docker logs clab-monitoring-gnmic > gnmic.log

# Network info
docker network ls
docker network inspect clab-gnmi-mgmt

# Resource usage
docker stats --no-stream
```

### Enable Debug Logging

**gNMIc Debug**:
```yaml
# In monitoring/gnmic/gnmic-config.yml
log: true
log-file: /tmp/gnmic.log
debug: true
```

**Ansible Verbose**:
```bash
ansible-playbook -i ansible/inventory.yml ansible/site.yml -vvv
```

**Containerlab Debug**:
```bash
sudo containerlab deploy -t topology.yml --debug
```

### Resources

- **Containerlab Docs**: https://containerlab.dev
- **SR Linux Learn**: https://learn.srlinux.dev
- **gNMIc Docs**: https://gnmic.openconfig.net
- **Prometheus Docs**: https://prometheus.io/docs
- **Grafana Docs**: https://grafana.com/docs

### Community Support

- **Containerlab Slack**: https://containerlab.dev/community
- **SR Linux Discord**: https://discord.gg/tZvgjQ6PZf
- **Network to Code Slack**: https://networktocode.slack.com

## Common Error Messages

### "Error: failed to create container"

**Cause**: Docker resource constraints or image issues

**Solution**:
```bash
# Check Docker resources
docker system df

# Clean up
docker system prune

# Pull image again
docker pull ghcr.io/nokia/srlinux:latest
```

### "Error: failed to create network"

**Cause**: Network name conflict or Docker network issues

**Solution**:
```bash
# List networks
docker network ls

# Remove conflicting network
docker network rm clab-gnmi-mgmt

# Redeploy
sudo containerlab deploy -t topology.yml
```

### "Error: connection refused"

**Cause**: Device not ready or gNMI not enabled

**Solution**:
```bash
# Wait for device to boot
sleep 180

# Check device is running
docker ps | grep spine1

# Enable gNMI (see vendor-specific sections)
```

### "Error: authentication failed"

**Cause**: Wrong credentials

**Solution**:
```bash
# Check default credentials:
# SR Linux: admin / NokiaSrl1!
# Arista: admin / admin
# SONiC: admin / YourPaSsWoRd
# Juniper: root / (no password)

# Update inventory or gNMIc config with correct credentials
```

### "Error: path not found"

**Cause**: Device doesn't support requested gNMI path

**Solution**:
```bash
# Check supported paths
gnmic -a 172.20.20.10:57400 -u admin -p NokiaSrl1! --skip-verify get --path /

# Use vendor-specific paths instead of OpenConfig
# See monitoring/gnmic/gnmic-config.yml for examples
```
