#!/usr/bin/env python3
"""
Link Utilization Analysis Tool

Analyzes network link utilization to identify:
- Underutilized links (wasted capacity)
- Overutilized links (potential bottlenecks)
- ECMP load balancing issues
- Parallel path imbalances

Queries Prometheus for interface metrics and provides actionable insights.
"""

import requests
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
PROMETHEUS_URL = "http://clab-monitoring-prometheus:9090"  # Prometheus container DNS name
INTERFACE_SPEED_GBPS = 10  # Assume 10G interfaces
IMBALANCE_THRESHOLD = 20  # Alert if parallel links differ by >20%
OVERUTIL_THRESHOLD = 80   # Alert if link >80% utilized
UNDERUTIL_THRESHOLD = 10  # Alert if link <10% utilized

def query_prometheus(query, time_range="5m"):
    """Query Prometheus and return results"""
    url = f"{PROMETHEUS_URL}/api/v1/query"
    params = {
        "query": query
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "success":
            print(f"Error: Prometheus query failed: {data}")
            return []
        
        return data["data"]["result"]
    except requests.exceptions.RequestException as e:
        print(f"Error: Cannot connect to Prometheus at {PROMETHEUS_URL}")
        print(f"Details: {e}")
        sys.exit(1)

def get_interface_utilization():
    """Get current interface utilization for all devices"""
    # Query for interface throughput (rate of change over 5 minutes)
    query = 'rate(gnmic_interface_stats_srl_nokia_interfaces_interface_statistics_out_octets[5m]) * 8 / 1000000000'  # Convert to Gbps
    
    results = query_prometheus(query)
    
    utilization = {}
    for result in results:
        metric = result["metric"]
        value = float(result["value"][1])
        
        # Get device name from the 'exported_source' label (set by gNMIc)
        device_name = metric.get("exported_source", "unknown")
        
        interface = metric.get("interface_name", "unknown")
        
        # Skip management interfaces
        if interface == "mgmt0":
            continue
        
        # Calculate utilization percentage
        util_percent = (value / INTERFACE_SPEED_GBPS) * 100
        
        if device_name not in utilization:
            utilization[device_name] = {}
        
        utilization[device_name][interface] = {
            "gbps": round(value, 2),
            "percent": round(util_percent, 2)
        }
    
    return utilization

def analyze_parallel_paths(utilization):
    """Analyze parallel paths for load balancing issues"""
    issues = []
    
    # Group interfaces by connection pairs
    # e.g., spine1 -> leaf1 via ethernet-1/1 and spine2 -> leaf1 via ethernet-1/1
    connections = defaultdict(list)
    
    for device, interfaces in utilization.items():
        for interface, stats in interfaces.items():
            # Extract connection info (simplified - assumes naming convention)
            if "ethernet" in interface:
                connections[interface].append({
                    "device": device,
                    "interface": interface,
                    "gbps": stats["gbps"],
                    "percent": stats["percent"]
                })
    
    # Check for imbalances in parallel paths
    for conn_name, links in connections.items():
        if len(links) > 1:
            # Multiple devices using same interface number = parallel paths
            utils = [link["percent"] for link in links]
            max_util = max(utils)
            min_util = min(utils)
            diff = max_util - min_util
            
            if diff > IMBALANCE_THRESHOLD:
                issues.append({
                    "type": "imbalance",
                    "severity": "warning",
                    "interface": conn_name,
                    "links": links,
                    "difference": round(diff, 2),
                    "message": f"Parallel paths imbalanced by {diff:.1f}%"
                })
    
    return issues

def analyze_utilization(utilization):
    """Analyze individual link utilization"""
    issues = []
    
    for device, interfaces in utilization.items():
        for interface, stats in interfaces.items():
            util = stats["percent"]
            
            if util > OVERUTIL_THRESHOLD:
                issues.append({
                    "type": "overutilized",
                    "severity": "critical",
                    "device": device,
                    "interface": interface,
                    "utilization": util,
                    "gbps": stats["gbps"],
                    "message": f"Link overutilized at {util:.1f}%"
                })
            elif util < UNDERUTIL_THRESHOLD and util > 0.1:
                issues.append({
                    "type": "underutilized",
                    "severity": "info",
                    "device": device,
                    "interface": interface,
                    "utilization": util,
                    "gbps": stats["gbps"],
                    "message": f"Link underutilized at {util:.1f}%"
                })
    
    return issues

def print_report(utilization, issues):
    """Print formatted analysis report"""
    print("=" * 80)
    print("LINK UTILIZATION ANALYSIS REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analysis Period: Last 5 minutes")
    print()
    
    # Summary statistics
    total_links = sum(len(interfaces) for interfaces in utilization.values())
    total_issues = len(issues)
    critical = len([i for i in issues if i["severity"] == "critical"])
    warnings = len([i for i in issues if i["severity"] == "warning"])
    
    print("SUMMARY")
    print("-" * 80)
    print(f"Total Links Monitored: {total_links}")
    print(f"Issues Found: {total_issues} (Critical: {critical}, Warnings: {warnings})")
    print()
    
    # Current utilization table
    print("CURRENT LINK UTILIZATION")
    print("-" * 80)
    print(f"{'Device':<15} {'Interface':<20} {'Gbps':<10} {'Utilization':<15} {'Status'}")
    print("-" * 80)
    
    for device in sorted(utilization.keys()):
        for interface in sorted(utilization[device].keys()):
            stats = utilization[device][interface]
            util = stats["percent"]
            
            # Status indicator
            if util > OVERUTIL_THRESHOLD:
                status = "⚠️  OVERUTILIZED"
            elif util < UNDERUTIL_THRESHOLD:
                status = "ℹ️  UNDERUTILIZED"
            else:
                status = "✓ OK"
            
            print(f"{device:<15} {interface:<20} {stats['gbps']:<10.2f} {util:<14.1f}% {status}")
    
    print()
    
    # Issues detail
    if issues:
        print("ISSUES DETECTED")
        print("-" * 80)
        
        # Group by severity
        for severity in ["critical", "warning", "info"]:
            severity_issues = [i for i in issues if i["severity"] == severity]
            if severity_issues:
                print(f"\n{severity.upper()}:")
                for issue in severity_issues:
                    if issue["type"] == "imbalance":
                        print(f"\n  ⚠️  Parallel Path Imbalance: {issue['interface']}")
                        print(f"     Difference: {issue['difference']}%")
                        for link in issue["links"]:
                            print(f"     - {link['device']}: {link['percent']:.1f}% ({link['gbps']:.2f} Gbps)")
                    else:
                        print(f"\n  • {issue['device']} - {issue['interface']}")
                        print(f"    {issue['message']}")
                        print(f"    Current: {issue['gbps']:.2f} Gbps ({issue['utilization']:.1f}%)")
    else:
        print("✓ NO ISSUES DETECTED")
        print("-" * 80)
        print("All links are within normal utilization ranges.")
        print("Load balancing across parallel paths is optimal.")
    
    print()
    print("=" * 80)
    
    # Recommendations
    if issues:
        print("\nRECOMMENDATIONS")
        print("-" * 80)
        
        if any(i["type"] == "overutilized" for i in issues):
            print("• Overutilized Links:")
            print("  - Consider adding capacity or redistributing traffic")
            print("  - Check for traffic anomalies or DDoS")
            print("  - Review QoS policies")
        
        if any(i["type"] == "imbalance" for i in issues):
            print("• Load Balancing Issues:")
            print("  - Verify ECMP is configured correctly")
            print("  - Check BGP/OSPF path costs are equal")
            print("  - Review traffic hashing algorithm")
        
        if any(i["type"] == "underutilized" for i in issues):
            print("• Underutilized Links:")
            print("  - Consider if link is needed")
            print("  - May indicate ECMP not working")
            print("  - Could be backup path (expected)")
        
        print()

def main():
    """Main execution"""
    print("Querying Prometheus for interface metrics...")
    print()
    
    # Get utilization data
    utilization = get_interface_utilization()
    
    if not utilization:
        print("Error: No interface metrics found in Prometheus")
        print("Ensure gNMIc is collecting data and Prometheus is scraping it")
        sys.exit(1)
    
    # Analyze for issues
    util_issues = analyze_utilization(utilization)
    balance_issues = analyze_parallel_paths(utilization)
    all_issues = util_issues + balance_issues
    
    # Print report
    print_report(utilization, all_issues)
    
    # Exit code based on severity
    if any(i["severity"] == "critical" for i in all_issues):
        sys.exit(2)  # Critical issues
    elif any(i["severity"] == "warning" for i in all_issues):
        sys.exit(1)  # Warnings
    else:
        sys.exit(0)  # All OK

if __name__ == "__main__":
    main()
