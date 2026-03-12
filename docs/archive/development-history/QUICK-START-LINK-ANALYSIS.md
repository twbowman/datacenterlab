# Quick Start: Link Utilization Analysis

Fast track to testing the link utilization analysis tool.

## 5-Minute Quick Start

```bash
# 1. Enter orb VM
orb -m clab

# 2. Install Python dependencies (first time only)
./install-dependencies.sh
# Or manually: sudo apt update && sudo apt install -y python3-requests

# 3. Start everything
./lab start && ./lab mon-start

# 4. Configure network
./lab configure

# 5. Wait for metrics (2 minutes)
sleep 120

# 6. Generate traffic (optional, for more realistic data)
./lab generate-traffic

# 7. Analyze links
./lab analyze-links
```

## What You'll See

The analysis report shows:
- **Current utilization** of all links (Gbps and %)
- **Overutilized links** (>80%) - potential bottlenecks
- **Underutilized links** (<10%) - wasted capacity  
- **ECMP imbalances** - parallel paths with >20% difference
- **Recommendations** - actionable next steps

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
spine1          ethernet-1/1         8.75       87.5%           ⚠️  OVERUTILIZED
spine2          ethernet-1/1         3.18       31.8%           ✓ OK
leaf1           ethernet-1/1         0.45       4.5%            ℹ️  UNDERUTILIZED
...

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
```

## Troubleshooting

### externally-managed-environment error

**Problem**: `pip install -r requirements.txt` fails with "externally-managed-environment"

**Cause**: Modern Python environments prevent system-wide pip installs to avoid conflicts.

**Solution**: Use one of these methods:

```bash
# Method 1: System package (recommended for orb VM)
sudo apt update && sudo apt install -y python3-requests

# Method 2: Virtual environment
python3 -m venv ~/venv-lab
source ~/venv-lab/bin/activate
pip install -r requirements.txt
# Remember to activate venv before running scripts

# Method 3: pipx
sudo apt install -y pipx
pipx install requests
```

### No metrics found
```bash
# Check monitoring is running
./lab status

# Verify gNMIc is collecting
curl http://172.20.20.5:9273/metrics | grep interface_statistics

# Wait longer (metrics collect every 10s)
sleep 60
```

### All links show 0%
```bash
# Generate traffic
./lab generate-traffic

# Verify BGP is working
./lab verify-detailed
```

### Cannot connect to Prometheus
```bash
# Check Prometheus is running
docker ps | grep prometheus

# Restart monitoring if needed
./lab mon-stop && ./lab mon-start
```

## Next Steps

1. **Grafana Dashboards** - Visual real-time monitoring
2. **Alerting** - Automated notifications for issues
3. **Historical Analysis** - Trending and capacity planning
4. **Production Deployment** - See LINK-UTILIZATION-TESTING.md

## Commands Reference

```bash
./lab start              # Deploy network lab
./lab mon-start          # Deploy monitoring
./lab configure          # Configure OSPF+BGP
./lab verify-detailed    # Verify configuration
./lab generate-traffic   # Generate test traffic
./lab analyze-links      # Run link analysis
./lab status             # Check status
./lab grafana            # Open Grafana
./lab prometheus         # Open Prometheus
```

## Monitoring URLs

When accessing from your host machine (outside orb VM):
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **gNMIc Metrics**: http://localhost:9273/metrics

When accessing from inside orb VM (for scripts):
- **Grafana**: http://172.20.20.2:3000
- **Prometheus**: http://172.20.20.3:9090
- **gNMIc Metrics**: http://172.20.20.5:9273/metrics

## Files

- `analyze-link-utilization.py` - Main analysis script
- `generate-traffic.sh` - Traffic generator
- `LINK-UTILIZATION-TESTING.md` - Detailed testing guide
- `requirements.txt` - Python dependencies
