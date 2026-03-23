# Vendor Extension Guide

## Overview

This guide explains how to add support for new network vendors to the Production Network Testing Lab. The lab is designed to be extensible, allowing you to add new vendors while maintaining the unified automation and monitoring framework.

**Validates: Requirements 10.1, 10.2, 10.7**

## Prerequisites

Before adding a new vendor, ensure you have:

1. **Container Image**: A Docker container image for the network OS
2. **API Access**: Documentation for the device's management API (gNMI, NETCONF, REST, etc.)
3. **Data Models**: YANG models or API schemas for configuration and telemetry
4. **Test Device**: Access to a physical or virtual device for testing
5. **Credentials**: Default username/password for the device

## Integration Template

### Quick Start Checklist

- [ ] Add vendor to Containerlab topology
- [ ] Create OS detection logic
- [ ] Implement Ansible configuration roles
- [ ] Add configuration validation rules
- [ ] Implement rollback capability
- [ ] Configure telemetry subscriptions
- [ ] Add metric normalization rules
- [ ] Create vendor-specific dashboards
- [ ] Write integration tests
- [ ] Update documentation

## Step 1: Containerlab Integration

### 1.1 Add Vendor to Topology

Edit `topologies/topology-multi-vendor.yml`:

```yaml
name: multi-vendor-lab

topology:
  kinds:
    # Existing vendors
    nokia_srlinux:
      image: ghcr.io/nokia/srlinux:latest
    
    # Add your new vendor
    newvendor_newos:
      image: newvendor/newos:latest
      # Vendor-specific settings
      env:
        SOME_ENV_VAR: value
      binds:
        - /path/to/config:/etc/config
  
  nodes:
    # Add device instances
    newvendor-spine1:
      kind: newvendor_newos
      type: device-type
      mgmt_ipv4: 172.20.20.50
      startup-config: configs/newvendor/startup.cfg
      labels:
        vendor: newvendor
        os: newos
        role: spine
  
  links:
    - endpoints: ["newvendor-spine1:eth1", "leaf1:eth49"]
```

### 1.2 Test Deployment

```bash
# Deploy topology
sudo containerlab deploy -t topologies/topology-multi-vendor.yml

# Verify container is running
docker ps | grep newvendor-spine1

# Check container logs
docker logs clab-multi-vendor-lab-newvendor-spine1

# Test connectivity
docker exec clab-multi-vendor-lab-newvendor-spine1 ping 172.20.20.1
```

### 1.3 Document Container Requirements

Create `docs/vendor/newvendor-requirements.md`:

```markdown
# NewVendor NewOS Requirements

## Container Image
- Image: `newvendor/newos:latest`
- Size: ~500MB
- Boot time: ~60 seconds

## Resource Requirements
- CPU: 2 cores
- Memory: 2GB
- Disk: 5GB

## Management Access
- Protocol: SSH, gNMI, REST
- Default port: 22 (SSH), 57400 (gNMI), 443 (REST)
- Default credentials: admin / admin123

## Known Limitations
- OpenConfig support: Partial (interfaces, BGP only)
- gNMI streaming: Supported
- NETCONF: Not supported
```

## Step 2: OS Detection

### 2.1 Add Detection Logic

Edit `ansible/plugins/inventory/dynamic_inventory.py`:

```python
def detect_os_via_gnmi(host, port=57400):
    """Detect device OS via gNMI capabilities"""
    try:
        capabilities = gnmi_capabilities(host, port)
        
        # Existing vendors
        if "Nokia" in capabilities.supported_models:
            return "srlinux"
        elif "Arista" in capabilities.supported_models:
            return "eos"
        elif "SONiC" in capabilities.supported_models:
            return "sonic"
        elif "Juniper" in capabilities.supported_models:
            return "junos"
        
        # Add your new vendor
        elif "NewVendor" in capabilities.supported_models:
            return "newos"
        
        return "unknown"
    except Exception as e:
        logger.warning(f"Could not detect OS for {host}: {e}")
        return "unknown"

def detect_os_via_ssh(host, port=22, username="admin", password="admin"):
    """Fallback: Detect OS via SSH banner"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command("show version")
        output = stdout.read().decode()
        
        # Add your vendor's version string pattern
        if "NewOS" in output:
            return "newos"
        
        ssh.close()
        return "unknown"
    except Exception as e:
        logger.warning(f"SSH detection failed for {host}: {e}")
        return "unknown"
```

### 2.2 Test OS Detection

```bash
# Test detection script
python3 ansible/plugins/inventory/dynamic_inventory.py

# Verify OS is detected
ansible-inventory -i ansible/plugins/inventory/dynamic_inventory.py --list | \
  jq '.newvendor_devices.hosts'
```

## Step 3: Ansible Configuration Roles

### 3.1 Create Role Structure

```bash
# Create role directories
mkdir -p ansible/methods/newvendor_api/roles/{newos_system,newos_interfaces,newos_bgp,newos_ospf}

# Create role templates
for role in newos_system newos_interfaces newos_bgp newos_ospf; do
  mkdir -p ansible/methods/newvendor_api/roles/$role/{tasks,defaults,templates,meta}
  touch ansible/methods/newvendor_api/roles/$role/tasks/main.yml
  touch ansible/methods/newvendor_api/roles/$role/defaults/main.yml
  touch ansible/methods/newvendor_api/roles/$role/meta/main.yml
done
```

### 3.2 Implement System Configuration Role

Create `ansible/methods/newvendor_api/roles/newos_system/tasks/main.yml`:

```yaml
---
- name: Configure NewOS system settings
  # Use vendor's API module (REST, gNMI, NETCONF, etc.)
  newvendor.newos.system:
    hostname: "{{ inventory_hostname }}"
    domain_name: "{{ domain_name | default('lab.local') }}"
    ntp_servers: "{{ ntp_servers | default([]) }}"
    dns_servers: "{{ dns_servers | default([]) }}"
  register: system_config
  
- name: Verify system configuration
  newvendor.newos.system_facts:
  register: system_facts
  
- name: Assert hostname is correct
  assert:
    that:
      - system_facts.hostname == inventory_hostname
    fail_msg: "Hostname mismatch: expected {{ inventory_hostname }}, got {{ system_facts.hostname }}"
```

### 3.3 Implement Interface Configuration Role

Create `ansible/methods/newvendor_api/roles/newos_interfaces/tasks/main.yml`:

```yaml
---
- name: Configure interfaces on NewOS
  newvendor.newos.interfaces:
    config:
      - name: "{{ item.name }}"
        description: "{{ item.description | default(omit) }}"
        enabled: "{{ item.enabled | default(true) }}"
        ipv4:
          address: "{{ item.ipv4_address }}"
          prefix_length: "{{ item.ipv4_prefix_length }}"
        mtu: "{{ item.mtu | default(1500) }}"
    state: merged
  loop: "{{ interfaces }}"
  when: interfaces is defined
  register: interface_config

- name: Verify interface configuration
  newvendor.newos.interfaces_facts:
  register: interface_facts
  
- name: Display configured interfaces
  debug:
    msg: "Configured {{ interface_facts.interfaces | length }} interfaces"
```

### 3.4 Implement BGP Configuration Role

Create `ansible/methods/newvendor_api/roles/newos_bgp/tasks/main.yml`:

```yaml
---
- name: Configure BGP on NewOS
  newvendor.newos.bgp:
    config:
      asn: "{{ bgp_asn }}"
      router_id: "{{ router_id }}"
      neighbors:
        - ip: "{{ item.ip }}"
          peer_as: "{{ item.peer_as }}"
          description: "{{ item.description | default(omit) }}"
          address_families:
            - ipv4_unicast
            - evpn
    state: merged
  loop: "{{ bgp_neighbors }}"
  when: bgp_neighbors is defined
  register: bgp_config

- name: Verify BGP sessions
  newvendor.newos.bgp_facts:
  register: bgp_facts
  
- name: Check BGP session states
  assert:
    that:
      - bgp_facts.neighbors[item.ip].state == "Established"
    fail_msg: "BGP session to {{ item.ip }} is not established"
  loop: "{{ bgp_neighbors }}"
  when: bgp_neighbors is defined
```

### 3.5 Create Role Defaults

Create `ansible/methods/newvendor_api/roles/newos_interfaces/defaults/main.yml`:

```yaml
---
# Default interface settings
default_mtu: 1500
default_enabled: true

# Interface name translation (if needed)
interface_name_format: "ethernet{slot}/{port}"
```

## Step 4: Dispatcher Integration

### 4.1 Add Vendor to Dispatcher

Edit `ansible/site.yml`:

```yaml
- name: Configure Multi-Vendor Datacenter Network
  hosts: all
  gather_facts: no
  tasks:
    # OS Detection
    - name: Detect and normalize OS
      set_fact:
        normalized_os: "{{ ansible_network_os | 
          regex_replace('^nokia\\.', '') | 
          regex_replace('^arista\\.', '') | 
          regex_replace('^dellemc\\.', '') | 
          regex_replace('^juniper\\.', '') |
          regex_replace('^newvendor\\.', '') }}"
    
    # Validation
    - name: Validate OS is supported
      assert:
        that:
          - normalized_os in ['srlinux', 'eos', 'sonic', 'junos', 'newos']
        fail_msg: "Unsupported OS: {{ normalized_os }}"
    
    # Configuration Validation
    - include_role:
        name: config_validation
    
    # Rollback Preparation
    - include_role:
        name: config_rollback
    
    # NewOS Configuration
    - name: Configure NewOS devices
      block:
        - include_role:
            name: newos_system
          vars:
            ansible_role_path: "{{ playbook_dir }}/methods/newvendor_api/roles"
        
        - include_role:
            name: newos_interfaces
          vars:
            ansible_role_path: "{{ playbook_dir }}/methods/newvendor_api/roles"
        
        - include_role:
            name: newos_bgp
          vars:
            ansible_role_path: "{{ playbook_dir }}/methods/newvendor_api/roles"
        
        - include_role:
            name: newos_ospf
          vars:
            ansible_role_path: "{{ playbook_dir }}/methods/newvendor_api/roles"
      
      rescue:
        - include_tasks: "{{ playbook_dir }}/roles/config_rollback/tasks/rollback_newos.yml"
        - fail:
            msg: "Configuration failed for {{ inventory_hostname }}, rollback completed"
      
      when: normalized_os == 'newos'
      tags: [config, newos]
```

## Step 5: Configuration Validation

### 5.1 Add Validation Rules

Create `ansible/roles/config_validation/tasks/validate_newos.yml`:

```yaml
---
- name: Validate NewOS connection variables
  assert:
    that:
      - ansible_host is defined
      - ansible_host | length > 0
    fail_msg: "ansible_host must be defined for {{ inventory_hostname }}"

- name: Validate interface configuration
  assert:
    that:
      - item.name is defined
      - item.ipv4_address is defined
      - item.ipv4_address | ansible.utils.ipaddr
    fail_msg: "Invalid interface configuration for {{ item.name }}"
  loop: "{{ interfaces }}"
  when: interfaces is defined

- name: Validate BGP configuration
  assert:
    that:
      - bgp_asn is defined
      - bgp_asn >= 1
      - bgp_asn <= 4294967295
      - router_id is defined
      - router_id | ansible.utils.ipaddr
    fail_msg: "Invalid BGP configuration"
  when: bgp_asn is defined
```

### 5.2 Add to Validation Dispatcher

Edit `ansible/roles/config_validation/tasks/main.yml`:

```yaml
- name: Validate NewOS configuration
  include_tasks: validate_newos.yml
  when: normalized_os == 'newos'
```

## Step 6: Rollback Capability

### 6.1 Implement State Capture

Create `ansible/roles/config_rollback/tasks/capture_newos.yml`:

```yaml
---
- name: Create rollback directory
  file:
    path: "{{ playbook_dir }}/rollback_configs"
    state: directory
  delegate_to: localhost
  run_once: true

- name: Capture current NewOS configuration
  newvendor.newos.config_facts:
  register: current_config
  
- name: Save configuration snapshot
  copy:
    content: "{{ current_config.config | to_nice_json }}"
    dest: "{{ playbook_dir }}/rollback_configs/{{ inventory_hostname }}_{{ ansible_date_time.epoch }}.json"
  delegate_to: localhost
  
- name: Set rollback available flag
  set_fact:
    rollback_available: true
    rollback_file: "{{ playbook_dir }}/rollback_configs/{{ inventory_hostname }}_{{ ansible_date_time.epoch }}.json"
```

### 6.2 Implement Rollback

Create `ansible/roles/config_rollback/tasks/rollback_newos.yml`:

```yaml
---
- name: Check if rollback is available
  assert:
    that:
      - rollback_available is defined
      - rollback_available | bool
    fail_msg: "No rollback configuration available for {{ inventory_hostname }}"

- name: Load rollback configuration
  set_fact:
    rollback_config: "{{ lookup('file', rollback_file) | from_json }}"

- name: Restore configuration
  newvendor.newos.config:
    config: "{{ rollback_config }}"
    replace: true
  register: rollback_result

- name: Report rollback success
  debug:
    msg: "Configuration rollback successful for {{ inventory_hostname }}"
  when: rollback_result is succeeded
```

## Step 7: Telemetry Configuration

### 7.1 Add gNMI Subscriptions

Edit `monitoring/gnmic/gnmic-config.yml`:

```yaml
targets:
  # Add NewOS devices
  newvendor-spine1:
    address: 172.20.20.50:57400
    username: admin
    password: admin123
    skip-verify: true
    tags:
      vendor: newvendor
      os: newos
      role: spine

subscriptions:
  # OpenConfig paths (if supported)
  oc_interface_stats:
    paths:
      - /interfaces/interface/state/counters
    mode: stream
    stream-mode: sample
    sample-interval: 10s
  
  # Native NewOS paths (fallback)
  newos_interface_stats:
    paths:
      - /newos/interfaces/interface/statistics
    mode: stream
    stream-mode: sample
    sample-interval: 10s
  
  newos_bgp_state:
    paths:
      - /newos/protocols/bgp/neighbor
    mode: stream
    stream-mode: sample
    sample-interval: 30s
```

### 7.2 Add Metric Normalization

Edit `monitoring/gnmic/gnmic-config.yml` processors section:

```yaml
processors:
  normalize_newos_metrics:
    event-processors:
      # Normalize interface metrics
      - event-convert:
          value-names:
            - "^/newos/interfaces/interface/statistics/rx-bytes$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/newos/interfaces/interface/statistics/rx-bytes"
                new: "interface_in_octets"
      
      - event-convert:
          value-names:
            - "^/newos/interfaces/interface/statistics/tx-bytes$"
          transforms:
            - replace:
                apply-on: "name"
                old: "/newos/interfaces/interface/statistics/tx-bytes"
                new: "interface_out_octets"
      
      # Add vendor tag
      - event-add-tag:
          tag-name: vendor
          value: newvendor
      
      # Normalize interface names
      - event-strings:
          tag-names:
            - interface
          transforms:
            - replace:
                apply-on: "value"
                old: "^Ethernet(\\d+)/(\\d+)$"
                new: "eth${1}_${2}"

outputs:
  prom:
    type: prometheus
    listen: :9273
    path: /metrics
    metric-prefix: network
    event-processors:
      - normalize_newos_metrics
```

### 7.3 Document Metric Mappings

Create `monitoring/gnmic/NEWOS-NORMALIZATION.md`:

```markdown
# NewOS Metric Normalization

## Interface Metrics

| Generic Metric | NewOS Path | OpenConfig Path |
|----------------|------------|-----------------|
| `network_interface_in_octets` | `/newos/interfaces/interface/statistics/rx-bytes` | `/interfaces/interface/state/counters/in-octets` |
| `network_interface_out_octets` | `/newos/interfaces/interface/statistics/tx-bytes` | `/interfaces/interface/state/counters/out-octets` |
| `network_interface_in_packets` | `/newos/interfaces/interface/statistics/rx-packets` | `/interfaces/interface/state/counters/in-pkts` |

## BGP Metrics

| Generic Metric | NewOS Path | OpenConfig Path |
|----------------|------------|-----------------|
| `network_bgp_session_state` | `/newos/protocols/bgp/neighbor/state` | `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state` |

## Interface Name Translation

- NewOS format: `Ethernet1/1`
- Normalized format: `eth1_1`
- Regex: `^Ethernet(\\d+)/(\\d+)$ → eth${1}_${2}`
```

## Step 8: Prometheus Relabeling

### 8.1 Add Relabeling Rules

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'gnmic'
    static_configs:
      - targets: ['gnmic:9273']
    
    metric_relabel_configs:
      # Existing rules...
      
      # NewOS interface metrics
      - source_labels: [__name__]
        regex: 'gnmic_newos_interface_stats_.*_rx_bytes'
        target_label: __name__
        replacement: 'network_interface_in_octets'
      
      - source_labels: [__name__]
        regex: 'gnmic_newos_interface_stats_.*_tx_bytes'
        target_label: __name__
        replacement: 'network_interface_out_octets'
      
      # Add vendor label
      - source_labels: [source]
        regex: 'newvendor-.*'
        target_label: vendor
        replacement: 'newvendor'
```

## Step 9: Grafana Dashboards

### 9.1 Verify Universal Dashboards Work

Test that existing universal dashboards display NewOS metrics:

```promql
# Should include NewOS devices
rate(network_interface_in_octets{vendor="newvendor"}[5m]) * 8
```

### 9.2 Create Vendor-Specific Dashboard

Create `monitoring/grafana/provisioning/dashboards/newos-specific.json`:

```json
{
  "dashboard": {
    "title": "NewOS Specific Metrics",
    "panels": [
      {
        "title": "NewOS CPU Usage",
        "targets": [
          {
            "expr": "newos_system_cpu_usage{vendor=\"newvendor\"}",
            "legendFormat": "{{source}} - CPU"
          }
        ]
      },
      {
        "title": "NewOS Memory Usage",
        "targets": [
          {
            "expr": "newos_system_memory_usage{vendor=\"newvendor\"}",
            "legendFormat": "{{source}} - Memory"
          }
        ]
      }
    ]
  }
}
```

## Step 10: Testing

### 10.1 Create Integration Tests

Create `tests/integration/test_newos_integration.py`:

```python
import pytest
from tests.helpers import (
    deploy_topology,
    configure_device,
    verify_telemetry,
    destroy_topology
)

@pytest.fixture(scope="module")
def newos_topology():
    """Deploy topology with NewOS device"""
    topology = deploy_topology("topology-newos-test.yml")
    yield topology
    destroy_topology(topology)

def test_newos_deployment(newos_topology):
    """Test NewOS device deployment"""
    device = newos_topology.get_device("newvendor-spine1")
    assert device.is_reachable()
    assert device.os == "newos"

def test_newos_configuration(newos_topology):
    """Test NewOS configuration"""
    device = newos_topology.get_device("newvendor-spine1")
    
    config = {
        "interfaces": [
            {
                "name": "Ethernet1/1",
                "ipv4_address": "10.1.1.0",
                "ipv4_prefix_length": 31
            }
        ]
    }
    
    result = configure_device(device, config)
    assert result.success
    assert result.changed

def test_newos_telemetry(newos_topology):
    """Test NewOS telemetry collection"""
    device = newos_topology.get_device("newvendor-spine1")
    
    # Verify metrics in Prometheus
    metrics = verify_telemetry(device, [
        "network_interface_in_octets",
        "network_interface_out_octets"
    ])
    
    assert len(metrics) > 0
    assert all(m.vendor == "newvendor" for m in metrics)
```

### 10.2 Run Tests

```bash
# Run NewOS integration tests
pytest tests/integration/test_newos_integration.py -v

# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=ansible --cov=monitoring
```

## Step 11: Documentation

### 11.1 Update Main Documentation

Edit `README.md`:

```markdown
## Supported Vendors

- ✅ Nokia SR Linux
- ✅ Arista cEOS
- ⚠️ Dell SONiC (Placeholder)
- ⚠️ Juniper Junos (Placeholder)
- ✅ NewVendor NewOS (Your contribution!)
```

### 11.2 Create Vendor-Specific Guide

Create `docs/vendor/newos-guide.md`:

```markdown
# NewOS Integration Guide

## Overview
NewOS support was added in [date]. This guide covers NewOS-specific configuration and limitations.

## Requirements
- Container image: `newvendor/newos:latest`
- Management API: gNMI (port 57400)
- Default credentials: admin / admin123

## Configuration
See `ansible/methods/newvendor_api/roles/` for configuration roles.

## Telemetry
- OpenConfig support: Partial (interfaces, BGP)
- Native paths: Full support
- Metric normalization: Implemented

## Known Limitations
- EVPN/VXLAN: Not yet implemented
- OSPF: Basic support only
- LLDP: Not supported

## Examples
See `topologies/examples/newos-example.yml`
```

### 11.3 Update Vendor Requirements

Edit `docs/developer/vendor-requirements.md` to include NewOS requirements.

## Example Implementation: Arista cEOS

For a complete example, see the Arista cEOS implementation:

```
ansible/methods/arista_eos/
├── roles/
│   ├── eos_system/
│   ├── eos_interfaces/
│   ├── eos_bgp/
│   └── eos_ospf/
└── README.md

monitoring/gnmic/
├── ARISTA-NORMALIZATION.md
└── validate-arista-normalization.sh

tests/integration/
└── test_arista_integration.py
```

## Troubleshooting

### Issue: OS Detection Fails

**Diagnosis**:
```bash
# Test gNMI capabilities
gnmic -a 172.20.20.50:57400 -u admin -p admin123 --insecure capabilities
```

**Solution**: Update detection logic to match vendor's capability string.

### Issue: Configuration Fails

**Diagnosis**:
```bash
# Test Ansible role manually
ansible-playbook -i inventory.yml site.yml --limit newvendor-spine1 -vvv
```

**Solution**: Check API documentation, verify credentials, review device logs.

### Issue: No Metrics in Prometheus

**Diagnosis**:
```bash
# Check gNMIc logs
docker logs clab-monitoring-gnmic | grep newvendor

# Test gNMI subscription
gnmic -a 172.20.20.50:57400 -u admin -p admin123 --insecure \
  subscribe --path "/interfaces/interface/state/counters"
```

**Solution**: Verify gNMI paths, check subscription configuration, review normalization rules.

## Best Practices

1. **Start Simple**: Implement basic interface configuration first
2. **Test Incrementally**: Test each component before moving to the next
3. **Document Everything**: Create vendor-specific documentation
4. **Follow Patterns**: Use existing vendor implementations as templates
5. **Normalize Metrics**: Ensure metrics work with universal queries
6. **Write Tests**: Create integration tests for your vendor
7. **Handle Errors**: Implement proper error handling and rollback
8. **Production Ready**: Test with production-like configurations

## Getting Help

- **Slack**: #network-lab-dev
- **GitHub Issues**: https://github.com/org/network-lab/issues
- **Documentation**: `docs/developer/`
- **Examples**: `topologies/examples/`

## Contributing

Once your vendor integration is complete:

1. Create a pull request with your changes
2. Include integration tests
3. Update documentation
4. Add example topology
5. Document any limitations

See `docs/developer/contributing.md` for detailed contribution guidelines.

## Summary

Adding a new vendor involves:
1. Containerlab integration (topology)
2. OS detection (dynamic inventory)
3. Ansible roles (configuration)
4. Validation and rollback
5. Telemetry subscriptions (gNMI)
6. Metric normalization (gNMIc + Prometheus)
7. Dashboards (Grafana)
8. Testing (integration tests)
9. Documentation

Follow this guide step-by-step, and you'll have a fully integrated vendor that works seamlessly with the existing multi-vendor framework!
