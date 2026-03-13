# Architecture Guide

## Overview

The Production Network Testing Lab is a comprehensive multi-vendor network testing environment that enables engineers to deploy, configure, and monitor production-grade network topologies using containerized network operating systems. This guide explains the system architecture, component interactions, and design decisions.

**Validates: Requirements 10.1, 13.1, 13.6**

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ CLI Scripts  │  │ Ansible      │  │ Python Tools │          │
│  │ (deploy.sh)  │  │ (site.yml)   │  │ (validate)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Containerlab │  │ Ansible      │  │ Validation   │          │
│  │ Deployment   │  │ Dispatcher   │  │ Engine       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Network Devices                             │
│                                                                   │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐               │
│  │SR Linux│  │Arista  │  │ SONiC  │  │Juniper │               │
│  │Devices │  │ cEOS   │  │Devices │  │Devices │               │
│  └────┬───┘  └────┬───┘  └────┬───┘  └────┬───┘               │
│       │           │           │           │                     │
│       └───────────┴───────────┴───────────┘                     │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Telemetry Collection                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ gNMIc        │  │ Metric       │  │ Prometheus   │          │
│  │ Collector    │─▶│ Normalizer   │─▶│ Exporter     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                              │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Prometheus   │  │ Grafana      │                            │
│  │ (Storage)    │─▶│ (Dashboards) │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Production Datacenter Compatibility

**Critical Principle**: All automation tools, monitoring configurations, and operational procedures are designed for direct production use. The lab is not a simulation—it's a production operations platform running on containerized hardware.

**Key Guarantees**:
- Same Ansible playbooks work for lab and production
- Same gNMI subscriptions work for lab and production
- Same Grafana dashboards work for lab and production
- Only inventory/target addresses change between environments

### 2. Vendor-Agnostic by Default

**Approach**: Use OpenConfig models for telemetry where vendor support exists, fall back to native vendor models when OpenConfig is incomplete.

**Benefits**:
- Universal queries work across all vendors
- Add new vendors without changing dashboards
- Simplified monitoring and alerting

### 3. Dispatcher Pattern

**Concept**: Single Ansible playbook automatically routes configuration tasks to vendor-specific implementations based on detected network operating system.

**Benefits**:
- Single entry point for all vendors
- Automatic OS detection
- Unified error handling and rollback
- Mixed-vendor topology support

### 4. Idempotent Operations

**Guarantee**: All configuration operations can be safely repeated without side effects.

**Implementation**:
- Ansible roles check current state before applying changes
- gNMI replace operations ensure desired state
- Configuration validation before deployment

### 5. Separation of Concerns

**Architecture**:
- Network lab (Containerlab)
- Automation framework (Ansible)
- Telemetry collection (gNMIc)
- Monitoring stack (Prometheus + Grafana)

**Benefits**:
- Independent lifecycle management
- Modular testing and updates
- Clear component boundaries

## Component Architecture

### 1. Deployment Orchestrator (Containerlab)

**Purpose**: Manages topology lifecycle (deploy, validate, destroy)

**Key Files**:
```
deploy.sh                    # Deploy topology
destroy.sh                   # Destroy topology
topology.yml                 # SR Linux topology
topology-multi-vendor.yml    # Multi-vendor topology
```

**Topology Definition Format**:
```yaml
name: production-lab
topology:
  kinds:
    nokia_srlinux:
      image: ghcr.io/nokia/srlinux:latest
    arista_ceos:
      image: ceos:latest
  
  nodes:
    spine1:
      kind: nokia_srlinux
      type: ixrd3
    arista-spine1:
      kind: arista_ceos
  
  links:
    - endpoints: ["spine1:e1-1", "leaf1:e1-49"]
```

**Deployment Flow**:
```
1. Validate topology definition
2. Pull container images
3. Create containers and networks
4. Wait for device boot (120s)
5. Verify device reachability
6. Generate dynamic inventory
```

### 2. Configuration Manager (Ansible)

**Purpose**: Apply vendor-specific configurations using unified playbooks

**Key Files**:
```
ansible/
├── site.yml                          # Main playbook (dispatcher)
├── inventory.yml                     # Device inventory
├── methods/
│   └── srlinux_gnmi/                # SR Linux gNMI method
│       ├── playbooks/               # Configuration playbooks
│       └── roles/                   # Configuration roles
├── roles/
│   ├── config_validation/           # Pre-deployment validation
│   └── config_rollback/             # Rollback capability
└── plugins/
    └── inventory/
        └── dynamic_inventory.py     # OS detection
```

**Dispatcher Pattern**:
```yaml
# ansible/site.yml
- name: Configure Multi-Vendor Network
  hosts: all
  tasks:
    # 1. Detect and validate OS
    - assert: ansible_network_os in supported_vendors
    
    # 2. Validate configuration syntax
    - include_role: config_validation
    
    # 3. Capture state for rollback
    - include_role: config_rollback
    
    # 4. Route to vendor-specific roles
    - block:
        - include_role: vendor_specific_roles
      rescue:
        - include_tasks: rollback.yml
      when: normalized_os == 'vendor'
```

**OS Detection**:
```python
def detect_os_via_gnmi(host, port=57400):
    """Detect device OS via gNMI capabilities"""
    capabilities = gnmi_capabilities(host, port)
    
    if "Nokia" in capabilities.supported_models:
        return "srlinux"
    elif "Arista" in capabilities.supported_models:
        return "eos"
    elif "SONiC" in capabilities.supported_models:
        return "sonic"
    elif "Juniper" in capabilities.supported_models:
        return "junos"
    
    return "unknown"
```

### 3. Telemetry Collector (gNMIc)

**Purpose**: Collect metrics via gNMI streaming and normalize to OpenConfig paths

**Key Files**:
```
monitoring/gnmic/
├── gnmic-config.yml         # Main configuration
├── subscriptions.yml        # gNMI subscriptions
├── processors.yml           # Metric normalization
└── METRIC-NORMALIZATION-GUIDE.md
```

**Configuration Structure**:
```yaml
# Targets (devices to collect from)
targets:
  spine1:
    address: 172.20.20.10:57400
    tags:
      vendor: nokia
      os: srlinux
      role: spine

# Subscriptions (what to collect)
subscriptions:
  oc_interface_stats:
    paths:
      - /interfaces/interface/state/counters
    mode: stream
    stream-mode: sample
    sample-interval: 10s

# Processors (how to normalize)
processors:
  normalize_metrics:
    event-processors:
      - event-convert:
          value-names:
            - "^/srl_nokia/interface/statistics/in-octets$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/srl_nokia/interface/statistics/in-octets"
                new: "interface_in_octets"

# Outputs (where to send)
outputs:
  prom:
    type: prometheus
    listen: :9273
    path: /metrics
    metric-prefix: network
    event-processors:
      - normalize_metrics
```

**Telemetry Pipeline**:
```
Device → gNMI Stream → gNMIc Collector → Processors → Prometheus Exporter
                                            ↓
                                    Metric Normalization
                                    (vendor → OpenConfig)
```

### 4. Metric Storage (Prometheus)

**Purpose**: Store time-series metrics with 30-day retention

**Key Files**:
```
monitoring/prometheus/
├── prometheus.yml           # Main configuration
├── alerts.yml              # Alert rules
└── validate-relabeling.sh  # Validation script
```

**Configuration**:
```yaml
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: 'gnmic'
    static_configs:
      - targets: ['gnmic:9273']
    
    # Additional normalization at Prometheus level
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'gnmic_srl_.*_in_octets'
        target_label: __name__
        replacement: 'network_interface_in_octets'

storage:
  tsdb:
    retention.time: 30d
    retention.size: 50GB
```

### 5. Visualization (Grafana)

**Purpose**: Provide universal and vendor-specific dashboards

**Key Files**:
```
monitoring/grafana/
├── provisioning/
│   ├── dashboards/          # Dashboard definitions
│   └── datasources/         # Prometheus datasource
└── VENDOR-SPECIFIC-DASHBOARDS-GUIDE.md
```

**Universal Query Pattern**:
```promql
# Works across all vendors
rate(network_interface_in_octets{role="spine"}[5m]) * 8

# Vendor-specific drill-down
rate(network_interface_in_octets{
  vendor="nokia",
  interface="ethernet-1/1"
}[5m]) * 8
```

### 6. Validation Engine

**Purpose**: Verify deployed configurations match expected state

**Key Files**:
```
tests/
├── unit/                    # Unit tests
├── integration/             # Integration tests
└── property/                # Property-based tests
```

**Validation Checks**:
- BGP sessions established
- EVPN routes advertised/received
- LLDP neighbors match topology
- Interface operational states
- Telemetry streaming active
- Metrics in Prometheus

## Data Flow

### Deployment Flow

```
User runs: ./deploy.sh
    ↓
1. Containerlab creates containers
    ↓
2. Devices boot (120s wait)
    ↓
3. Dynamic inventory detects OS
    ↓
4. Ansible validates configuration
    ↓
5. Ansible captures current state
    ↓
6. Ansible applies configuration
    ↓
7. Validation engine verifies state
    ↓
8. gNMIc starts telemetry collection
    ↓
9. Metrics flow to Prometheus
    ↓
10. Grafana displays dashboards
```

### Telemetry Flow

```
Network Device
    ↓ (gNMI stream)
gNMIc Collector
    ↓ (event processing)
Metric Normalization
    ↓ (Prometheus export)
Prometheus Storage
    ↓ (PromQL query)
Grafana Dashboard
    ↓
User Visualization
```

### Configuration Flow

```
User defines: inventory.yml
    ↓
Ansible Dispatcher
    ↓
OS Detection
    ↓
Configuration Validation
    ↓
State Capture (rollback)
    ↓
Vendor-Specific Role
    ↓ (gNMI/API)
Network Device
    ↓
Verification
    ↓
Success or Rollback
```

## Design Decisions

### Decision 1: Containerlab for Topology Management

**Rationale**:
- Industry-standard tool for network labs
- Supports multiple vendors
- Simple YAML topology definition
- Automatic network creation
- Built-in management network

**Alternatives Considered**:
- Docker Compose: Less network-aware
- Custom scripts: Reinventing the wheel
- Virtual machines: Resource-intensive

### Decision 2: Ansible for Configuration Management

**Rationale**:
- Industry-standard automation tool
- Idempotent operations
- Rich ecosystem of modules
- Production-ready
- Supports multiple connection methods (gNMI, NETCONF, API)

**Alternatives Considered**:
- Python scripts: Less structured
- Terraform: Not designed for network config
- Custom DSL: Maintenance burden

### Decision 3: gNMI for Telemetry Collection

**Rationale**:
- Modern streaming protocol
- Vendor-neutral (OpenConfig support)
- Efficient (streaming vs polling)
- Rich data (structured YANG models)
- Production-ready

**Alternatives Considered**:
- SNMP: Legacy, polling-based
- REST APIs: Not standardized
- Syslog: Unstructured

### Decision 4: Two-Stage Metric Normalization

**Rationale**:
- gNMIc processors: Basic normalization, vendor tagging
- Prometheus relabeling: Final standardization
- Flexibility for debugging
- Separation of concerns

**Alternatives Considered**:
- gNMIc only: Less flexible
- Prometheus only: More complex rules
- No normalization: Vendor-specific queries

### Decision 5: Dispatcher Pattern for Multi-Vendor

**Rationale**:
- Single entry point
- Automatic OS detection
- Unified error handling
- Mixed-vendor support
- Production-ready

**Alternatives Considered**:
- Separate playbooks: Multiple runs needed
- Manual OS specification: Error-prone
- Vendor-specific inventories: Duplicate data

## Component Interactions

### Ansible ↔ Network Devices

**Protocol**: gNMI (SR Linux), eAPI (Arista), REST (SONiC), NETCONF (Juniper)

**Operations**:
- Configuration deployment (gNMI set)
- State verification (gNMI get)
- Rollback (gNMI replace)

**Error Handling**:
- Connection timeout: Retry with backoff
- Configuration error: Automatic rollback
- Validation failure: Report with remediation

### gNMIc ↔ Network Devices

**Protocol**: gNMI streaming

**Operations**:
- Subscribe to telemetry paths
- Receive streaming updates
- Process and normalize metrics
- Export to Prometheus

**Error Handling**:
- Connection failure: Exponential backoff reconnection
- Subscription error: Log and continue with other subscriptions
- Processing error: Skip metric, log error

### Prometheus ↔ gNMIc

**Protocol**: HTTP (Prometheus scrape)

**Operations**:
- Scrape metrics from gNMIc exporter
- Apply relabeling rules
- Store in time-series database

**Error Handling**:
- Scrape failure: Retry on next interval
- Storage full: Alert operator
- Query timeout: Return partial results

### Grafana ↔ Prometheus

**Protocol**: HTTP (PromQL queries)

**Operations**:
- Query metrics via PromQL
- Render dashboards
- Generate alerts

**Error Handling**:
- Query timeout: Display error
- No data: Show "No data" message
- Connection failure: Retry

## Scalability Considerations

### Lab Scale
- 10-20 devices
- ~1,000 metrics per device
- 10-second collection interval
- Single gNMIc collector
- Single Prometheus instance

### Production Scale
- 1,000+ devices
- 10,000+ metrics per device
- 10-second collection interval
- Multiple gNMIc collectors (horizontal scaling)
- Prometheus federation or Thanos

### Scaling Strategies

**Horizontal Scaling**:
- Multiple gNMIc collectors (shard by device)
- Prometheus federation (aggregate metrics)
- Load balancer for Grafana

**Vertical Scaling**:
- Increase Prometheus storage
- Increase gNMIc memory
- Optimize metric cardinality

**Optimization**:
- Reduce collection frequency for stable metrics
- Use recording rules for expensive queries
- Implement metric retention policies

## Security Considerations

### Authentication
- gNMI: Username/password or certificate-based
- Ansible: SSH keys or username/password
- Prometheus: Basic auth (optional)
- Grafana: User authentication

### Encryption
- gNMI: TLS (can be disabled for lab)
- Ansible: SSH encryption
- Prometheus: HTTPS (optional)
- Grafana: HTTPS (optional)

### Access Control
- Network devices: Role-based access control
- Grafana: User roles and permissions
- Prometheus: Read-only access for Grafana

### Lab vs Production
- Lab: Relaxed security (skip-verify, default passwords)
- Production: Strict security (certificates, strong passwords, RBAC)

## Performance Characteristics

### Deployment Time
- 2-spine, 4-leaf topology: ~120 seconds
- Configuration deployment: ~30 seconds
- Validation: ~60 seconds
- Total: ~210 seconds (3.5 minutes)

### Telemetry Performance
- Device CPU impact: <5%
- gNMIc CPU usage: ~10% per 100 devices
- gNMIc memory: ~100MB per 100 devices
- Metric ingestion rate: ~10,000 metrics/second

### Query Performance
- Simple query (<10 series): <100ms
- Complex query (100+ series): <1s
- Dashboard load: <2s

## Troubleshooting Architecture

### Logging Layers

**Containerlab**:
```bash
# Container logs
docker logs clab-<topology>-<device>

# Containerlab logs
containerlab inspect --name <topology>
```

**Ansible**:
```bash
# Verbose output
ansible-playbook -vvv site.yml

# Log file
tail -f /var/log/ansible.log
```

**gNMIc**:
```bash
# Container logs
docker logs clab-monitoring-gnmic

# Debug mode
gnmic --debug subscribe ...
```

**Prometheus**:
```bash
# Container logs
docker logs clab-monitoring-prometheus

# Query logs
curl http://localhost:9090/api/v1/query?query=up
```

**Grafana**:
```bash
# Container logs
docker logs clab-monitoring-grafana

# Access logs
tail -f /var/log/grafana/grafana.log
```

### Common Issues

**Issue**: Device not reachable
**Diagnosis**: Check container status, network connectivity
**Resolution**: Restart container, verify network configuration

**Issue**: Configuration failed
**Diagnosis**: Check Ansible logs, device logs
**Resolution**: Fix configuration syntax, verify credentials

**Issue**: No metrics in Prometheus
**Diagnosis**: Check gNMIc logs, Prometheus scrape status
**Resolution**: Verify gNMI subscriptions, check network connectivity

**Issue**: Dashboard shows no data
**Diagnosis**: Check Prometheus data, verify query syntax
**Resolution**: Verify metrics exist, fix PromQL query

## Related Documentation

- **User Documentation**: `docs/user/`
- **Vendor Extension Guide**: `docs/developer/vendor-extension.md`
- **Contribution Guide**: `docs/developer/contributing.md`
- **Metric Normalization**: `docs/developer/metric-normalization.md`
- **Ansible Architecture**: `ansible/ARCHITECTURE.md`
- **Dispatcher Pattern**: `ansible/DISPATCHER-PATTERN.md`
- **OS Detection**: `ansible/OS-DETECTION-GUIDE.md`

## Summary

The Production Network Testing Lab architecture is designed for:
- **Production compatibility**: Same code works for lab and production
- **Multi-vendor support**: Unified framework for all vendors
- **Vendor-agnostic telemetry**: Universal queries across vendors
- **Idempotent operations**: Safe to repeat
- **Separation of concerns**: Modular, testable components
- **Scalability**: From lab (10 devices) to production (1000+ devices)

The architecture balances simplicity (easy to understand and use) with power (production-ready features) while maintaining clear component boundaries and well-defined interfaces.
