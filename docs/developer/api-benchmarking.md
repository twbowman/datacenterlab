# Benchmarking API

## Overview

The Benchmarking API provides comprehensive performance measurement and analysis for the network testing lab. It measures deployment times, configuration performance, telemetry overhead, and resource utilization across different vendors and topology sizes.

## Core Components

### BenchmarkRunner Class

The main orchestrator for all benchmarking operations.

**Location**: `benchmarks/framework.py`

#### Constructor

```python
from benchmarks.framework import BenchmarkRunner

runner = BenchmarkRunner(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml",
    prometheus_url="http://localhost:9090",
    results_dir="benchmarks/results"
)
```

**Parameters**:
- `topology_file` (str): Path to containerlab topology definition
- `inventory_file` (str): Path to Ansible inventory file
- `prometheus_url` (str, optional): Prometheus API endpoint (default: "http://localhost:9090")
- `results_dir` (str, optional): Directory for benchmark results (default: "benchmarks/results")

#### Methods

##### benchmark_all()

Runs all benchmark suites and generates comprehensive report.

```python
report = runner.benchmark_all(
    iterations=3,
    include_deployment=True,
    include_configuration=True,
    include_telemetry=True,
    include_resource_usage=True
)
```

**Parameters**:
- `iterations` (int, optional): Number of iterations per benchmark (default: 3)
- `include_deployment` (bool, optional): Run deployment benchmarks (default: True)
- `include_configuration` (bool, optional): Run configuration benchmarks (default: True)
- `include_telemetry` (bool, optional): Run telemetry benchmarks (default: True)
- `include_resource_usage` (bool, optional): Measure resource usage (default: True)

**Returns**: `BenchmarkReport` object

**Example**:
```python
# Run all benchmarks with 5 iterations
report = runner.benchmark_all(iterations=5)

print(f"Benchmark Report - {report.lab_name}")
print(f"Total duration: {report.total_duration_seconds:.1f}s")
print(f"\nDeployment: {report.deployment.mean_time:.1f}s (±{report.deployment.std_dev:.1f}s)")
print(f"Configuration: {report.configuration.mean_time:.1f}s (±{report.configuration.std_dev:.1f}s)")
print(f"Telemetry overhead: {report.telemetry.cpu_overhead_percent:.2f}%")

# Save report
report.save("benchmarks/results/full-benchmark.json")
```

##### benchmark_deployment()

Measures topology deployment performance.

```python
result = runner.benchmark_deployment(
    iterations=5,
    topology_sizes=[2, 4, 8, 16],
    measure_per_device=True
)
```

**Parameters**:
- `iterations` (int, optional): Number of iterations (default: 3)
- `topology_sizes` (list, optional): Device counts to test (default: [current topology size])
- `measure_per_device` (bool, optional): Measure individual device boot times (default: True)

**Returns**: `DeploymentBenchmark` object

**Example**:
```python
# Benchmark deployment with different topology sizes
result = runner.benchmark_deployment(
    iterations=3,
    topology_sizes=[2, 4, 8, 16]
)

print("Deployment Performance:")
for size, metrics in result.by_size.items():
    print(f"  {size} devices: {metrics.mean:.1f}s (p95: {metrics.p95:.1f}s)")

# Per-device boot times
print("\nPer-device boot times:")
for device, time in result.device_boot_times.items():
    print(f"  {device}: {time:.1f}s")
```

##### benchmark_configuration()

Measures configuration deployment performance.

```python
result = runner.benchmark_configuration(
    iterations=3,
    config_types=["interfaces", "bgp", "ospf", "evpn"],
    measure_per_device=True,
    measure_per_vendor=True
)
```

**Parameters**:
- `iterations` (int, optional): Number of iterations (default: 3)
- `config_types` (list, optional): Configuration types to benchmark (default: all)
- `measure_per_device` (bool, optional): Measure per-device times (default: True)
- `measure_per_vendor` (bool, optional): Compare vendors (default: True)

**Returns**: `ConfigurationBenchmark` object

**Example**:
```python
result = runner.benchmark_configuration(
    iterations=5,
    config_types=["bgp", "ospf"]
)

print("Configuration Performance:")
print(f"  Total time: {result.total_time.mean:.1f}s")
print(f"  BGP config: {result.by_type['bgp'].mean:.1f}s")
print(f"  OSPF config: {result.by_type['ospf'].mean:.1f}s")

# Vendor comparison
print("\nVendor comparison:")
for vendor, metrics in result.by_vendor.items():
    print(f"  {vendor}: {metrics.mean:.1f}s (±{metrics.std_dev:.1f}s)")
```

##### benchmark_telemetry()

Measures telemetry collection performance and overhead.

```python
result = runner.benchmark_telemetry(
    duration_seconds=300,
    measure_cpu_overhead=True,
    measure_ingestion_rate=True,
    measure_latency=True
)
```

**Parameters**:
- `duration_seconds` (int, optional): Measurement duration (default: 300)
- `measure_cpu_overhead` (bool, optional): Measure device CPU impact (default: True)
- `measure_ingestion_rate` (bool, optional): Measure metric ingestion rate (default: True)
- `measure_latency` (bool, optional): Measure collection latency (default: True)

**Returns**: `TelemetryBenchmark` object

**Example**:
```python
result = runner.benchmark_telemetry(duration_seconds=600)

print("Telemetry Performance:")
print(f"  CPU overhead: {result.cpu_overhead_percent:.2f}%")
print(f"  Ingestion rate: {result.ingestion_rate_per_second:.0f} metrics/s")
print(f"  Collection latency: {result.latency_p95:.1f}s (p95)")

# Per-device CPU usage
print("\nDevice CPU usage:")
for device, cpu in result.device_cpu_usage.items():
    print(f"  {device}: {cpu:.2f}%")
    if cpu > 5.0:
        print(f"    ⚠️  Exceeds 5% threshold!")
```

##### measure_resource_usage()

Measures resource consumption of lab components.

```python
result = runner.measure_resource_usage(
    duration_seconds=300,
    measure_devices=True,
    measure_collector=True,
    measure_prometheus=True,
    measure_grafana=True
)
```

**Parameters**:
- `duration_seconds` (int, optional): Measurement duration (default: 300)
- `measure_devices` (bool, optional): Measure network device resources (default: True)
- `measure_collector` (bool, optional): Measure gNMIc collector resources (default: True)
- `measure_prometheus` (bool, optional): Measure Prometheus resources (default: True)
- `measure_grafana` (bool, optional): Measure Grafana resources (default: True)

**Returns**: `ResourceUsage` object

**Example**:
```python
result = runner.measure_resource_usage(duration_seconds=600)

print("Resource Usage:")
print(f"\nDevices:")
print(f"  CPU: {result.devices.cpu_percent:.1f}%")
print(f"  Memory: {result.devices.memory_mb:.0f} MB")

print(f"\ngNMIc Collector:")
print(f"  CPU: {result.collector.cpu_percent:.1f}%")
print(f"  Memory: {result.collector.memory_mb:.0f} MB")

print(f"\nPrometheus:")
print(f"  CPU: {result.prometheus.cpu_percent:.1f}%")
print(f"  Memory: {result.prometheus.memory_mb:.0f} MB")
print(f"  Storage: {result.prometheus.storage_gb:.2f} GB")
```

##### compare_vendors()

Compares performance across different vendors.

```python
comparison = runner.compare_vendors(
    metrics=["deployment_time", "config_time", "cpu_usage"],
    iterations=5
)
```

**Parameters**:
- `metrics` (list): Metrics to compare
- `iterations` (int, optional): Number of iterations (default: 3)

**Returns**: `VendorComparison` object

**Example**:
```python
comparison = runner.compare_vendors(
    metrics=["deployment_time", "config_time", "cpu_usage"],
    iterations=5
)

print("Vendor Performance Comparison:")
for metric in comparison.metrics:
    print(f"\n{metric}:")
    for vendor, value in comparison.by_vendor[metric].items():
        print(f"  {vendor}: {value.mean:.2f} (±{value.std_dev:.2f})")
    
    # Show fastest vendor
    fastest = comparison.get_fastest(metric)
    print(f"  ⭐ Fastest: {fastest}")
```

##### identify_bottlenecks()

Analyzes benchmark results to identify performance bottlenecks.

```python
bottlenecks = runner.identify_bottlenecks(
    benchmark_report=report,
    thresholds={
        "deployment_time": 120,  # seconds
        "config_time": 60,
        "cpu_overhead": 5.0,  # percent
        "memory_usage": 1024  # MB
    }
)
```

**Parameters**:
- `benchmark_report` (BenchmarkReport): Report to analyze
- `thresholds` (dict, optional): Performance thresholds

**Returns**: `BottleneckAnalysis` object

**Example**:
```python
bottlenecks = runner.identify_bottlenecks(report)

if bottlenecks.found:
    print("⚠️  Performance Bottlenecks Detected:")
    for bottleneck in bottlenecks.issues:
        print(f"\n{bottleneck.category}: {bottleneck.description}")
        print(f"  Current: {bottleneck.current_value}")
        print(f"  Threshold: {bottleneck.threshold}")
        print(f"  Recommendation: {bottleneck.recommendation}")
else:
    print("✅ No performance bottlenecks detected")
```

## Data Models

### BenchmarkReport

Complete benchmark report with all measurements.

```python
@dataclass
class BenchmarkReport:
    """Complete benchmark report"""
    
    timestamp: str  # ISO8601 timestamp
    lab_name: str  # Lab/topology name
    topology_size: int  # Number of devices
    
    deployment: DeploymentBenchmark  # Deployment metrics
    configuration: ConfigurationBenchmark  # Configuration metrics
    telemetry: TelemetryBenchmark  # Telemetry metrics
    resource_usage: ResourceUsage  # Resource consumption
    
    vendor_comparison: Optional[VendorComparison]  # Vendor comparison
    bottlenecks: Optional[BottleneckAnalysis]  # Bottleneck analysis
    
    total_duration_seconds: float  # Total benchmark time
    
    def save(self, output_file: str):
        """Save report to file"""
    
    def to_json(self) -> str:
        """Export as JSON"""
    
    def to_html(self) -> str:
        """Generate HTML report"""
    
    def print_summary(self):
        """Print human-readable summary"""
```

**Example**:
```python
report = runner.benchmark_all()

# Print summary
report.print_summary()

# Save as JSON
report.save("benchmarks/results/report.json")

# Generate HTML report
html = report.to_html()
with open("benchmarks/results/report.html", "w") as f:
    f.write(html)
```

### DeploymentBenchmark

Deployment performance metrics.

```python
@dataclass
class DeploymentBenchmark:
    """Deployment performance metrics"""
    
    iterations: int  # Number of iterations
    
    mean_time: float  # Mean deployment time (seconds)
    median_time: float  # Median deployment time
    std_dev: float  # Standard deviation
    min_time: float  # Minimum time
    max_time: float  # Maximum time
    p95: float  # 95th percentile
    p99: float  # 99th percentile
    
    by_size: Dict[int, BenchmarkMetrics]  # Metrics by topology size
    device_boot_times: Dict[str, float]  # Per-device boot times
    
    raw_measurements: List[float]  # All measurements
```

### ConfigurationBenchmark

Configuration deployment performance metrics.

```python
@dataclass
class ConfigurationBenchmark:
    """Configuration performance metrics"""
    
    iterations: int
    
    total_time: BenchmarkMetrics  # Total configuration time
    by_type: Dict[str, BenchmarkMetrics]  # Per config type (bgp, ospf, etc.)
    by_vendor: Dict[str, BenchmarkMetrics]  # Per vendor
    by_device: Dict[str, BenchmarkMetrics]  # Per device
    
    idempotency_overhead: float  # Overhead of idempotent operations (%)
```

### TelemetryBenchmark

Telemetry collection performance metrics.

```python
@dataclass
class TelemetryBenchmark:
    """Telemetry performance metrics"""
    
    duration_seconds: int  # Measurement duration
    
    cpu_overhead_percent: float  # Device CPU overhead
    device_cpu_usage: Dict[str, float]  # Per-device CPU usage
    
    ingestion_rate_per_second: float  # Metrics ingested per second
    total_metrics: int  # Total metrics collected
    metrics_per_device: Dict[str, int]  # Metrics per device
    
    latency_mean: float  # Mean collection latency (seconds)
    latency_p95: float  # 95th percentile latency
    latency_p99: float  # 99th percentile latency
    
    collector_cpu_percent: float  # gNMIc CPU usage
    collector_memory_mb: float  # gNMIc memory usage
```

### ResourceUsage

Resource consumption measurements.

```python
@dataclass
class ResourceUsage:
    """Resource consumption measurements"""
    
    devices: ComponentResources  # Network devices
    collector: ComponentResources  # gNMIc collector
    prometheus: ComponentResources  # Prometheus
    grafana: ComponentResources  # Grafana
    
    total_cpu_percent: float  # Total CPU usage
    total_memory_mb: float  # Total memory usage
    total_storage_gb: float  # Total storage usage

@dataclass
class ComponentResources:
    """Resource usage for a component"""
    
    cpu_percent: float  # CPU usage percentage
    memory_mb: float  # Memory usage in MB
    storage_gb: Optional[float]  # Storage usage in GB
    
    cpu_peak: float  # Peak CPU usage
    memory_peak: float  # Peak memory usage
```

### VendorComparison

Performance comparison across vendors.

```python
@dataclass
class VendorComparison:
    """Vendor performance comparison"""
    
    vendors: List[str]  # Vendors compared
    metrics: List[str]  # Metrics compared
    
    by_vendor: Dict[str, Dict[str, BenchmarkMetrics]]  # Results by vendor and metric
    
    def get_fastest(self, metric: str) -> str:
        """Get fastest vendor for metric"""
    
    def get_ranking(self, metric: str) -> List[Tuple[str, float]]:
        """Get vendor ranking for metric"""
```

### BottleneckAnalysis

Performance bottleneck analysis.

```python
@dataclass
class BottleneckAnalysis:
    """Performance bottleneck analysis"""
    
    found: bool  # Whether bottlenecks were found
    issues: List[BottleneckIssue]  # Identified issues
    
    recommendations: List[str]  # Optimization recommendations

@dataclass
class BottleneckIssue:
    """Single bottleneck issue"""
    
    category: str  # "deployment", "configuration", "telemetry", "resources"
    severity: str  # "critical", "warning", "info"
    description: str  # Issue description
    current_value: Any  # Current measured value
    threshold: Any  # Expected threshold
    recommendation: str  # How to fix
```

### BenchmarkMetrics

Statistical metrics for a benchmark.

```python
@dataclass
class BenchmarkMetrics:
    """Statistical benchmark metrics"""
    
    mean: float
    median: float
    std_dev: float
    min: float
    max: float
    p95: float
    p99: float
    
    samples: int  # Number of samples
    raw_values: List[float]  # Raw measurements
```

## Usage Examples

### Basic Benchmarking

```python
from benchmarks.framework import BenchmarkRunner

# Initialize runner
runner = BenchmarkRunner(
    topology_file="topology.yml",
    inventory_file="ansible/inventory.yml"
)

# Run all benchmarks
report = runner.benchmark_all(iterations=5)

# Print summary
report.print_summary()

# Save results
report.save("benchmarks/results/full-benchmark.json")
```

### Deployment Performance Testing

```python
# Test deployment with different topology sizes
runner = BenchmarkRunner("topology.yml", "ansible/inventory.yml")

result = runner.benchmark_deployment(
    iterations=3,
    topology_sizes=[2, 4, 8, 16]
)

print("Deployment Scaling:")
for size, metrics in result.by_size.items():
    time_per_device = metrics.mean / size
    print(f"{size} devices: {metrics.mean:.1f}s ({time_per_device:.1f}s per device)")

# Check if deployment meets requirements
if result.mean_time > 120:
    print("⚠️  Deployment exceeds 120s requirement")
else:
    print("✅ Deployment within 120s requirement")
```

### Configuration Performance Analysis

```python
# Benchmark configuration deployment
result = runner.benchmark_configuration(
    iterations=5,
    config_types=["interfaces", "bgp", "ospf", "evpn"]
)

print("Configuration Performance:")
for config_type, metrics in result.by_type.items():
    print(f"{config_type}: {metrics.mean:.1f}s (±{metrics.std_dev:.1f}s)")

# Vendor comparison
print("\nVendor Comparison:")
for vendor, metrics in result.by_vendor.items():
    print(f"{vendor}: {metrics.mean:.1f}s")

fastest_vendor = min(result.by_vendor.items(), key=lambda x: x[1].mean)
print(f"\n⭐ Fastest: {fastest_vendor[0]}")
```

### Telemetry Overhead Measurement

```python
# Measure telemetry overhead
result = runner.benchmark_telemetry(duration_seconds=600)

print("Telemetry Overhead:")
print(f"Average CPU overhead: {result.cpu_overhead_percent:.2f}%")

# Check per-device CPU usage
print("\nPer-device CPU usage:")
for device, cpu in result.device_cpu_usage.items():
    status = "✅" if cpu < 5.0 else "⚠️"
    print(f"{status} {device}: {cpu:.2f}%")

# Check requirement compliance
if result.cpu_overhead_percent < 5.0:
    print("\n✅ Telemetry overhead within 5% requirement")
else:
    print(f"\n⚠️  Telemetry overhead exceeds 5% requirement ({result.cpu_overhead_percent:.2f}%)")
```

### Resource Usage Monitoring

```python
# Measure resource usage
result = runner.measure_resource_usage(duration_seconds=600)

print("Resource Usage Summary:")
print(f"\nTotal:")
print(f"  CPU: {result.total_cpu_percent:.1f}%")
print(f"  Memory: {result.total_memory_mb:.0f} MB")
print(f"  Storage: {result.total_storage_gb:.2f} GB")

print(f"\nBreakdown:")
print(f"  Devices: {result.devices.cpu_percent:.1f}% CPU, {result.devices.memory_mb:.0f} MB")
print(f"  gNMIc: {result.collector.cpu_percent:.1f}% CPU, {result.collector.memory_mb:.0f} MB")
print(f"  Prometheus: {result.prometheus.cpu_percent:.1f}% CPU, {result.prometheus.memory_mb:.0f} MB")
print(f"  Grafana: {result.grafana.cpu_percent:.1f}% CPU, {result.grafana.memory_mb:.0f} MB")
```

### Vendor Performance Comparison

```python
# Compare vendors
comparison = runner.compare_vendors(
    metrics=["deployment_time", "config_time", "cpu_usage"],
    iterations=5
)

print("Vendor Performance Comparison:")

for metric in comparison.metrics:
    print(f"\n{metric}:")
    
    # Get ranking
    ranking = comparison.get_ranking(metric)
    
    for rank, (vendor, value) in enumerate(ranking, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{medal} {rank}. {vendor}: {value:.2f}")
```

### Bottleneck Identification

```python
# Run benchmarks
report = runner.benchmark_all(iterations=5)

# Identify bottlenecks
bottlenecks = runner.identify_bottlenecks(
    benchmark_report=report,
    thresholds={
        "deployment_time": 120,
        "config_time": 60,
        "cpu_overhead": 5.0,
        "memory_usage": 1024
    }
)

if bottlenecks.found:
    print("⚠️  Performance Issues Detected:\n")
    
    for issue in bottlenecks.issues:
        severity_icon = "🔴" if issue.severity == "critical" else "🟡"
        print(f"{severity_icon} {issue.category}: {issue.description}")
        print(f"   Current: {issue.current_value}")
        print(f"   Threshold: {issue.threshold}")
        print(f"   Fix: {issue.recommendation}\n")
    
    print("Recommendations:")
    for rec in bottlenecks.recommendations:
        print(f"  • {rec}")
else:
    print("✅ No performance bottlenecks detected")
```

### Continuous Performance Monitoring

```python
import time
from datetime import datetime

runner = BenchmarkRunner("topology.yml", "ansible/inventory.yml")

# Track performance over time
results = []

for i in range(10):
    print(f"\nIteration {i+1}/10 - {datetime.now()}")
    
    # Run quick benchmark
    result = runner.benchmark_telemetry(duration_seconds=60)
    
    results.append({
        "timestamp": datetime.now().isoformat(),
        "cpu_overhead": result.cpu_overhead_percent,
        "ingestion_rate": result.ingestion_rate_per_second,
        "latency_p95": result.latency_p95
    })
    
    # Check for degradation
    if len(results) > 1:
        prev = results[-2]
        curr = results[-1]
        
        cpu_change = curr["cpu_overhead"] - prev["cpu_overhead"]
        if cpu_change > 1.0:
            print(f"⚠️  CPU overhead increased by {cpu_change:.2f}%")
    
    time.sleep(300)  # Wait 5 minutes

# Save trend data
import json
with open("benchmarks/results/performance-trend.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Generate Performance Report

```python
# Run comprehensive benchmarks
runner = BenchmarkRunner("topology.yml", "ansible/inventory.yml")

report = runner.benchmark_all(iterations=5)

# Generate HTML report
html = report.to_html()
with open("benchmarks/results/performance-report.html", "w") as f:
    f.write(html)

print("✅ Performance report generated: benchmarks/results/performance-report.html")

# Also save JSON for programmatic access
report.save("benchmarks/results/performance-report.json")
```

## CLI Tools

### Run Benchmarks

```bash
# Run all benchmarks
./scripts/run-benchmarks.sh

# Run specific benchmark
./scripts/run-benchmarks.sh --type deployment
./scripts/run-benchmarks.sh --type configuration
./scripts/run-benchmarks.sh --type telemetry

# Specify iterations
./scripts/run-benchmarks.sh --iterations 10

# Output format
./scripts/run-benchmarks.sh --format json > results.json
./scripts/run-benchmarks.sh --format html > report.html
```

### Compare Vendors

```bash
# Compare all vendors
./scripts/compare-vendor-performance.sh

# Compare specific metrics
./scripts/compare-vendor-performance.sh --metrics deployment_time,config_time

# Output ranking
./scripts/compare-vendor-performance.sh --show-ranking
```

### Identify Bottlenecks

```bash
# Analyze performance
./scripts/identify-bottlenecks.sh benchmarks/results/report.json

# Custom thresholds
./scripts/identify-bottlenecks.sh \
    benchmarks/results/report.json \
    --deployment-threshold 90 \
    --cpu-threshold 3.0
```

## Performance Requirements

The benchmarking framework validates these requirements:

- **Deployment**: Complete within 120 seconds
- **Configuration**: Apply within 60 seconds
- **Telemetry CPU**: Less than 5% device CPU usage
- **Validation**: Complete within 60 seconds
- **Test Suite**: Complete within 10 minutes

## Best Practices

1. **Multiple Iterations**: Run at least 3-5 iterations for statistical significance
2. **Stable Environment**: Ensure system is idle during benchmarking
3. **Warm-up**: Discard first iteration (cold start effects)
4. **Consistent Conditions**: Use same hardware and network conditions
5. **Baseline Tracking**: Establish baseline and track changes over time
6. **Vendor Comparison**: Test all vendors under identical conditions
7. **Document Changes**: Record system changes that affect performance

## See Also

- [Validation Engine API](api-validation-engine.md) - Configuration validation
- [State Management API](api-state-management.md) - Lab state management
- [Architecture Guide](architecture.md) - Overall system architecture
- [Performance Requirements](../user/monitoring.md) - Performance targets
