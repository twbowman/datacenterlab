# Changelog

All notable changes to the Production Network Testing Lab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Changelog and versioning system
- Version tracking in state snapshots
- Version compatibility documentation

## [0.9.0] - 2024-01-15

### Added
- Comprehensive API documentation for state management, validation, and benchmarking
- Developer API reference with code examples
- API documentation for metric normalization
- Vendor requirements documentation for OpenConfig support

### Improved
- Documentation structure and organization
- Code examples in API documentation

## [0.8.0] - 2024-01-14

### Added
- GitHub Actions CI/CD pipeline
- Automated unit tests workflow
- Automated property-based tests workflow
- Automated integration tests workflow
- CI configuration documentation
- Quick start guide for CI

### Improved
- Test reliability and coverage
- Automated testing infrastructure

## [0.7.0] - 2024-01-13

### Added
- Integration tests for end-to-end workflows
- Integration tests for multi-vendor scenarios
- Integration tests for monitoring stack
- Integration test documentation and README

### Improved
- Test coverage for complex scenarios
- Multi-vendor testing capabilities

## [0.6.0] - 2024-01-12

### Added
- Property-based tests for state management
- Property-based tests for telemetry collection
- Test strategies and generators for property tests
- Property test documentation

### Improved
- Test coverage using property-based testing
- Validation of invariants across all inputs

## [0.5.0] - 2024-01-11

### Added
- Unit tests for configuration management
- Unit tests for deployment orchestration
- Unit tests for state management
- Unit tests for validation engine
- Unit tests for telemetry collection
- Unit test documentation and README

### Improved
- Code reliability through comprehensive unit testing
- Test organization and structure

## [0.4.0] - 2024-01-10

### Added
- Juniper vMX/vQFX normalization rules
- SONiC normalization rules
- Transformation validation scripts for all vendors
- Vendor-specific normalization documentation

### Improved
- Metric normalization across all supported vendors
- Telemetry collection reliability

## [0.3.0] - 2024-01-09

### Added
- Prometheus relabeling rules for metric normalization
- Vendor-specific relabeling configurations
- Relabeling validation scripts
- Testing guide for Prometheus rules

### Improved
- Metric consistency across vendors
- Query portability in Grafana

## [0.2.0] - 2024-01-08

### Added
- EVPN/VXLAN configuration roles for SR Linux
- EVPN/VXLAN configuration roles for Juniper
- EVPN verification playbooks
- Multi-vendor EVPN support

### Improved
- Data center fabric capabilities
- Multi-vendor configuration management

## [0.1.0] - 2024-01-07

### Added
- Initial multi-vendor topology support (SR Linux, Arista, SONiC, Juniper)
- Ansible dispatcher pattern for OS detection
- Configuration validation roles
- Configuration rollback capabilities
- Vendor-specific configuration roles (BGP, OSPF, interfaces)
- OS detection guide and documentation

### Improved
- Automation framework flexibility
- Vendor extensibility

## [0.0.1] - 2024-01-01

### Added
- Initial project structure
- Containerlab topology deployment for SR Linux
- Basic Ansible automation framework
- gNMI-based configuration for SR Linux
- OpenConfig telemetry collection (interfaces, BGP, LLDP)
- gNMIc telemetry collector with Prometheus export
- Basic metric normalization
- Grafana dashboards (BGP, OSPF, interfaces)
- Configuration verification playbooks
- Basic documentation structure

## Migration Guides

### Migrating to 1.0.0 (Future Breaking Changes)

When version 1.0.0 is released, the following breaking changes are planned:

#### State Snapshot Format Changes
- **Breaking**: State snapshot format will change from version "1.0" to "2.0"
- **Migration**: Use the provided migration script to convert old snapshots:
  ```bash
  python scripts/migrate-snapshots.py --from 1.0 --to 2.0 snapshots/
  ```
- **Changes**:
  - Device configuration format will be standardized across vendors
  - Metric snapshot format will include additional metadata
  - Topology definition will use enhanced schema

#### Ansible Inventory Changes
- **Breaking**: Inventory variable names will be standardized
- **Migration**: Update inventory files using the provided script:
  ```bash
  python scripts/migrate-inventory.py ansible/inventory.yml
  ```
- **Changes**:
  - `ansible_network_os` becomes `device_os`
  - `device_role` becomes `topology_role`
  - New required variable: `device_vendor`

#### gNMIc Configuration Changes
- **Breaking**: gNMIc configuration structure will be reorganized
- **Migration**: Use the provided migration script:
  ```bash
  python scripts/migrate-gnmic-config.py monitoring/gnmic/gnmic-config.yml
  ```
- **Changes**:
  - Subscriptions will be organized by protocol (BGP, OSPF, interfaces)
  - Processor configuration will use new syntax
  - Target configuration will include additional metadata

#### API Changes
- **Breaking**: State management API will have new method signatures
- **Migration**: Update code using the API:
  ```python
  # Old (0.x)
  snapshot = export_state(lab_name)
  
  # New (1.0)
  snapshot = export_state(lab_name, include_metrics=True, format_version="2.0")
  ```

### Migrating from 0.8.x to 0.9.x

No breaking changes. All features are backward compatible.

### Migrating from 0.7.x to 0.8.x

No breaking changes. CI/CD workflows are additive and don't affect existing functionality.

### Migrating from 0.6.x to 0.7.x

No breaking changes. Integration tests are additive.

### Migrating from 0.5.x to 0.6.x

No breaking changes. Property-based tests are additive.

### Migrating from 0.4.x to 0.5.x

No breaking changes. Unit tests are additive.

### Migrating from 0.3.x to 0.4.x

#### Juniper and SONiC Normalization
- **Change**: Added normalization rules for Juniper and SONiC devices
- **Action Required**: If using Juniper or SONiC devices, update gNMIc configuration:
  ```bash
  # Backup existing config
  cp monitoring/gnmic/gnmic-config.yml monitoring/gnmic/gnmic-config.yml.backup
  
  # Add new processor imports
  # See monitoring/gnmic/JUNIPER-NORMALIZATION.md
  # See monitoring/gnmic/SONIC-NORMALIZATION.md
  ```

### Migrating from 0.2.x to 0.3.x

#### Prometheus Relabeling
- **Change**: Metric names are now normalized at Prometheus level
- **Action Required**: Update Grafana dashboards to use new metric names:
  ```promql
  # Old
  gnmic_srl_interface_in_octets
  
  # New
  network_interface_in_octets
  ```
- **Migration**: Run the dashboard migration script:
  ```bash
  python scripts/migrate-dashboards.py monitoring/grafana/provisioning/dashboards/
  ```

### Migrating from 0.1.x to 0.2.x

#### EVPN/VXLAN Configuration
- **Change**: New EVPN/VXLAN roles added
- **Action Required**: Update inventory to include EVPN variables if deploying EVPN fabrics:
  ```yaml
  evpn_vxlan:
    vni_range:
      start: 10000
      end: 10999
    route_distinguisher: "{{ router_id }}:1"
  ```

### Migrating from 0.0.x to 0.1.x

#### Multi-Vendor Support
- **Change**: Added support for Arista, SONiC, and Juniper devices
- **Action Required**: Update topology files to specify device kind:
  ```yaml
  # Old (SR Linux only)
  nodes:
    spine1:
      image: ghcr.io/nokia/srlinux:latest
  
  # New (multi-vendor)
  nodes:
    spine1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
    spine2:
      kind: arista_ceos
      image: ceos:latest
  ```

#### Ansible Dispatcher Pattern
- **Change**: Ansible now uses dispatcher pattern for OS detection
- **Action Required**: Ensure `ansible_network_os` is set in inventory:
  ```yaml
  hosts:
    spine1:
      ansible_host: 172.20.20.10
      ansible_network_os: srlinux  # Required
  ```

## Version Compatibility Matrix

| Lab Version | State Snapshot Format | gNMIc Config Version | Ansible Inventory Version | Python Version | Containerlab Version |
|-------------|----------------------|---------------------|--------------------------|----------------|---------------------|
| 0.9.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.8.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.7.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.6.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.5.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.4.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.3.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.2.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.1.x       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |
| 0.0.1       | 1.0                  | 1.0                 | 1.0                      | 3.9+           | 0.48+               |

## Deprecation Notices

### Planned for 1.0.0
- Legacy state snapshot format (version 1.0) will be deprecated
- Old inventory variable names will be deprecated
- Legacy gNMIc configuration structure will be deprecated

### Planned for 2.0.0
- Python 3.8 support will be dropped (minimum Python 3.10)
- Containerlab versions older than 0.50 will not be supported
- Legacy metric names (pre-normalization) will be removed

## Support Policy

- **Current Release**: Full support with bug fixes and security updates
- **Previous Minor Release**: Security updates only for 6 months
- **Older Releases**: No support (upgrade recommended)

## Links

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Project Repository](https://github.com/example/production-network-testing-lab)
- [Issue Tracker](https://github.com/example/production-network-testing-lab/issues)
- [Documentation](docs/)
