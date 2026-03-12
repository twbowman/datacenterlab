# Link Utilization Analysis - Testing Guide

This guide walks through testing the link utilization analysis tool.

## Overview

The `analyze-link-utilization.py` script analyzes network link utilization to identify:
- Overutilized links (>80% capacity) - potential bottlenecks
- Underutilized links (<10% capacity) - wasted resources
- ECMP load balancing issues - parallel paths with >20% difference
- Provides actionable recommendations

## Prerequisites

1. Network lab must be running
2. Monitoring stack must be running
3. Network must be configured with OSPF+BGP
4. Python 3 with requests library

### Installing Python Dependencies

The orb VM uses an externally-managed Python environment. Choose one option:

**Option 1: Use the helper script (easiest)**
```bash
./install-dependencies.sh
```

**Option 2: System package (manual)**
```bash
sudo apt update && sudo apt install -y python3-requests
```

**Option 3: Virtual environment (best practice)**
```bash
# Create and activate virtual environment
python3 -m venv ~/venv-lab
source ~/venv-lab/bin/activate

# Install requirements
pip install -r requirements.txt

# Run scripts (venv must be activated)
python3 analyze-link-utilization.py

# Deactivate when done
deactivate
```

**Option 4: pipx (for standalone scripts)**
```bash
sudo apt install -y pipx
pipx install requests
```

## Step-by-Step Testing

### 1. Start the Lab Environment

```bash
# Enter the orb VM
orb -m clab

# Deploy network lab
./lab start

# Deploy monitoring stack
./lab mon-start

# Configure network (OSPF + BGP)
./lab configure

# Verify configuration
./lab verify-detailed
```

### 2. Verify Monitoring Stack

Check that all monitoring components are running:

```bash
./lab status
```

You should see:
- gnmic container running
- prometheus container running
- grafana container running

Verify gNMIc is collecting metrics:
```bash
curl -s http://172.20.20.5:9273/metrics | grep gnmic_interface_statistics_out_octets | head -5
```

You should see interface metrics with device labels.

### 3. Wait for Initial Metrics

gNMIc collects interface statistics every 10 seconds. Wait at least 1-2 minutes for initial data:

```bash
# Wait 2 minutes
sleep 120

# Check Prometheus has data
curl -s 'http://172.20.20.3:9090/api/v1/query?query=gnmic_interface_statistics_out_octets' | jq '.data.result | length'
```

Should return a number > 0 (number of interfaces being monitored).

### 4. Generate Test Traffic (Optional)

To see more realistic utilization, generate traffic between clients:

```bash
./generate-traffic.sh
```

This will:
- Generate traffic between client pairs
- Run for 60 seconds
- Create various traffic patterns to test ECMP

### 5. Run Link Utilization Analysis

```bash
# Install Python dependencies (first time only)
./install-dependencies.sh
# Or manually: sudo apt update && sudo apt install -y python3-requests

# Run the analysis
python3 analyze-link-utilization.py

# Or use the lab command
./lab analyze-links
```

### 6. Interpret Results

The script outputs a detailed report with:

#### Summary Section
```
SUMMARY
--------------------------------------------------------------------------------
Total Links Monitored: 24
Issues Found: 3 (Critical: 1, Warnings: 2)
```

#### Current Utilization Table
```
Device          Interface            Gbps       Utilization     Status
--------------------------------------------------------------------------------
leaf1           ethernet-1/1         0.45       4.5%            ℹ️  UNDERUTILIZED
spine1          ethernet-1/1         8.75       87.5%           ⚠️  OVERUTILIZED
```

#### Issues Detected
- **CRITICAL**: Links >80% utilized (potential bottlenecks)
- **WARNING**: Parallel paths imbalanced >20% (ECMP issues)
- **INFO**: Links <10% utilized (wasted capacity)

#### Recommendations
Actionable suggestions based on detected issues.

### 7. Exit Codes

The script returns different exit codes for automation:
- `0`: All OK, no issues
- `1`: Warnings found (imbalances, underutilization)
- `2`: Critical issues (overutilization)

Use in automation:
```bash
python3 analyze-link-utilization.py
if [ $? -eq 2 ]; then
    echo "Critical issues detected!"
    # Send alert, page on-call, etc.
fi
```

## Troubleshooting

### No metrics found

**Problem**: Script reports "No interface metrics found in Prometheus"

**Solutions**:
1. Check monitoring stack is running: `./lab status`
2. Verify gNMIc is collecting: `curl http://172.20.20.5:9273/metrics`
3. Check Prometheus is scraping: `curl http://172.20.20.3:9090/targets`
4. Wait longer for initial metrics (2-3 minutes)

### Cannot connect to Prometheus

**Problem**: "Cannot connect to Prometheus at http://172.20.20.3:9090"

**Solutions**:
1. Check Prometheus is running: `docker ps | grep prometheus`
2. Verify port mapping: `docker port clab-monitoring-prometheus`
3. Check from inside orb VM (not host machine)
4. Verify container IP: `docker inspect clab-monitoring-prometheus | grep IPAddress`

### All links show 0% utilization

**Problem**: Metrics exist but all show 0 Gbps

**Causes**:
- No traffic flowing through network
- Clients not generating traffic
- Interfaces are up but idle

**Solutions**:
1. Generate test traffic: `./generate-traffic.sh`
2. Check BGP routes are installed: `./lab verify-detailed`
3. Verify OSPF neighbors are up
4. Check client connectivity

### Parallel path detection not working

**Problem**: Script doesn't detect ECMP imbalances

**Cause**: The current implementation uses simplified connection grouping based on interface names.

**Enhancement needed**: Parse LLDP data to identify actual parallel paths between device pairs.

## Configuration Tuning

### Adjust Thresholds

Edit `analyze-link-utilization.py`:

```python
INTERFACE_SPEED_GBPS = 10  # Change if using different speed interfaces
IMBALANCE_THRESHOLD = 20   # Alert if parallel links differ by >20%
OVERUTIL_THRESHOLD = 80    # Alert if link >80% utilized
UNDERUTIL_THRESHOLD = 10   # Alert if link <10% utilized
```

### Change Analysis Period

Default is 5 minutes. To change:

```python
# In get_interface_utilization() function
query = 'rate(gnmic_interface_statistics_out_octets[5m]) * 8 / 1000000000'
#                                                      ^^^ change this
```

Options: `1m`, `5m`, `15m`, `1h`

### Prometheus URL

If running Prometheus on different host/port:

```python
PROMETHEUS_URL = "http://172.20.20.3:9090"  # Change this
```

Note: The default uses the container IP (172.20.20.3) which works when running scripts inside the orb VM. If running from host machine, use `http://localhost:9090`.

## Next Steps

After validating the Python script works:

1. **Grafana Dashboards** - Create visual dashboards for real-time monitoring
2. **Alerting** - Set up Prometheus alerts for critical thresholds
3. **Historical Analysis** - Add trending and capacity planning features
4. **Enhanced ECMP Detection** - Use LLDP data for accurate parallel path identification
5. **Automation** - Run periodically via cron or monitoring system

## Production Deployment

For production use:

1. **Secure Prometheus**: Add authentication, TLS
2. **High Availability**: Run multiple Prometheus instances
3. **Long-term Storage**: Configure remote write to time-series database
4. **Alerting**: Integrate with PagerDuty, Slack, etc.
5. **Dashboards**: Create role-based Grafana dashboards
6. **Documentation**: Document thresholds and escalation procedures

## Example Output

```
================================================================================
LINK UTILIZATION ANALYSIS REPORT
================================================================================
Timestamp: 2026-03-11 15:30:45
Analysis Period: Last 5 minutes

SUMMARY
--------------------------------------------------------------------------------
Total Links Monitored: 24
Issues Found: 2 (Critical: 1, Warnings: 1)

CURRENT LINK UTILIZATION
--------------------------------------------------------------------------------
Device          Interface            Gbps       Utilization     Status
--------------------------------------------------------------------------------
leaf1           ethernet-1/1         0.45       4.5%            ℹ️  UNDERUTILIZED
leaf1           ethernet-1/2         0.52       5.2%            ℹ️  UNDERUTILIZED
spine1          ethernet-1/1         8.75       87.5%           ⚠️  OVERUTILIZED
spine1          ethernet-1/2         3.21       32.1%           ✓ OK
spine2          ethernet-1/1         3.18       31.8%           ✓ OK
spine2          ethernet-1/2         3.25       32.5%           ✓ OK

ISSUES DETECTED
--------------------------------------------------------------------------------

CRITICAL:

  • spine1 - ethernet-1/1
    Link overutilized at 87.5%
    Current: 8.75 Gbps (87.5%)

WARNING:

  ⚠️  Parallel Path Imbalance: ethernet-1/1
     Difference: 55.7%
     - spine1: 87.5% (8.75 Gbps)
     - spine2: 31.8% (3.18 Gbps)

================================================================================

RECOMMENDATIONS
--------------------------------------------------------------------------------
• Overutilized Links:
  - Consider adding capacity or redistributing traffic
  - Check for traffic anomalies or DDoS
  - Review QoS policies
• Load Balancing Issues:
  - Verify ECMP is configured correctly
  - Check BGP/OSPF path costs are equal
  - Review traffic hashing algorithm

================================================================================
```
