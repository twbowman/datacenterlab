# Implementation Plan: Production Network Testing Lab

## Overview

This implementation plan breaks down the production network testing lab into 9 phases following the design document's roadmap. The lab will support multi-vendor network topologies (SR Linux, Arista cEOS, SONiC, Juniper) with vendor-agnostic automation, OpenConfig-based telemetry, metric normalization, and comprehensive validation.

**Current State**: SR Linux deployment, basic Ansible automation, OpenConfig telemetry collection, and Grafana dashboards are operational.

**Target State**: Full multi-vendor support with EVPN/VXLAN configuration, comprehensive validation framework, state management, performance benchmarking, and complete test coverage.

## Important Context

#[[file:.kiro/steering/containerlab-commands.md]]

This lab runs on macOS with ARM processor using ORB. All containerlab, docker, and ansible commands must be prefixed with `orb -m clab` to run in the correct VM context.

## Tasks

### Phase 1: Multi-Vendor Topology Deployment

- [x] 1. Extend topology definition for multi-vendor support
  - [x] 1.1 Create multi-vendor topology file with all 4 vendors
    - Add Arista cEOS, SONiC, and Juniper device definitions to topology.yml
    - Configure appropriate container images for each vendor
    - Define device roles (spine, leaf) and management IPs
    - _Requirements: 1.2, 10.6_
  
  - [x] 1.2 Implement topology validation before deployment
    - Create topology validator that checks required fields (kind, image)
    - Validate device types are supported
    - Check for circular dependencies in links
    - Provide specific error messages for validation failures
    - _Requirements: 1.6, 1.5_
  
  - [x] 1.3 Update deployment scripts for multi-vendor support
    - Modify deploy.sh to handle multiple vendor types
    - Add device boot time handling per vendor (different boot times)
    - Implement health checks for all vendor types
    - Add cleanup verification in destroy.sh
    - _Requirements: 1.1, 1.3, 1.7_


- [x] 2. Implement OS detection system
  - [x] 2.1 Create dynamic inventory plugin with gNMI capabilities detection
    - Implement ansible/plugins/inventory/dynamic_inventory.py
    - Query gNMI capabilities from each device
    - Map capabilities to OS types (srlinux, eos, sonic, junos)
    - Generate Ansible inventory with ansible_network_os variable
    - _Requirements: 1.4_
  
  - [ ]* 2.2 Write unit tests for OS detection
    - Test detection for each vendor type
    - Test handling of unknown/unreachable devices
    - Test inventory generation format
    - _Requirements: 1.4_
  
  - [x] 2.3 Integrate OS detection into deployment workflow
    - Call dynamic inventory generation after containerlab deploy
    - Verify all devices have detected OS before configuration
    - Add error handling for detection failures
    - _Requirements: 1.4, 1.5_

- [x] 3. Checkpoint - Verify multi-vendor deployment
  - Ensure all 4 vendor types can be deployed in single topology
  - Verify OS detection works for all vendors
  - Confirm health checks pass for all devices
  - Ask user if questions arise

### Phase 2: Multi-Vendor Configuration Roles

- [x] 4. Create Arista EOS configuration roles
  - [x] 4.1 Implement eos_interfaces role
    - Create ansible/roles/eos_interfaces/tasks/main.yml
    - Use arista.eos.eos_interfaces module
    - Implement interface name translation filter (to_arista_interface)
    - Support interface description, enabled state, IP addressing
    - _Requirements: 2.1, 2.8_
  
  - [x] 4.2 Implement eos_bgp role
    - Create ansible/roles/eos_bgp/tasks/main.yml
    - Configure BGP ASN, router-id, and neighbors
    - Support iBGP with route reflectors
    - Configure address families (ipv4-unicast, evpn)
    - _Requirements: 2.2, 2.8_
  
  - [x] 4.3 Implement eos_ospf role
    - Create ansible/roles/eos_ospf/tasks/main.yml
    - Configure OSPF process ID and router-id
    - Configure OSPF areas and interfaces
    - Set network type to point-to-point for fabric links
    - _Requirements: 2.3, 2.8_
  
  - [ ]* 4.4 Write unit tests for Arista roles
    - Test configuration generation from templates
    - Test idempotency of configuration operations
    - Test error handling for invalid configurations
    - _Requirements: 2.7_


- [x] 5. Create SONiC configuration roles
  - [x] 5.1 Implement sonic_interfaces role
    - Create ansible/roles/sonic_interfaces/tasks/main.yml
    - Use dellemc.enterprise_sonic.sonic_interfaces module
    - Implement interface name translation filter (to_sonic_interface)
    - Support interface configuration and IP addressing
    - _Requirements: 2.1, 2.8_
  
  - [x] 5.2 Implement sonic_bgp role
    - Create ansible/roles/sonic_bgp/tasks/main.yml
    - Configure BGP using SONiC data models
    - Support iBGP configuration
    - Configure BGP neighbors and address families
    - _Requirements: 2.2, 2.8_
  
  - [x] 5.3 Implement sonic_ospf role
    - Create ansible/roles/sonic_ospf/tasks/main.yml
    - Configure OSPF using SONiC data models
    - Configure OSPF areas and interfaces
    - _Requirements: 2.3, 2.8_
  
  - [ ]* 5.4 Write unit tests for SONiC roles
    - Test configuration generation
    - Test idempotency
    - Test error handling
    - _Requirements: 2.7_

- [x] 6. Create Juniper configuration roles
  - [x] 6.1 Implement junos_interfaces role
    - Create ansible/roles/junos_interfaces/tasks/main.yml
    - Use junipernetworks.junos.junos_interfaces module
    - Support interface configuration
    - _Requirements: 2.1, 2.8_
  
  - [x] 6.2 Implement junos_bgp role
    - Create ansible/roles/junos_bgp/tasks/main.yml
    - Configure BGP using Junos modules
    - Support iBGP with route reflectors
    - _Requirements: 2.2, 2.8_
  
  - [x] 6.3 Implement junos_ospf role
    - Create ansible/roles/junos_ospf/tasks/main.yml
    - Configure OSPF using Junos modules
    - _Requirements: 2.3, 2.8_
  
  - [ ]* 6.4 Write unit tests for Juniper roles
    - Test configuration generation
    - Test idempotency
    - Test error handling
    - _Requirements: 2.7_


- [x] 7. Update dispatcher pattern for multi-vendor support
  - [x] 7.1 Enhance ansible/site.yml with vendor-specific role routing
    - Add conditional role inclusion based on ansible_network_os
    - Support all 4 vendors (srlinux, eos, sonic, junos)
    - Implement graceful handling of unsupported vendors
    - _Requirements: 2.8, 10.5_
  
  - [x] 7.2 Add configuration syntax validation before deployment
    - Implement pre-deployment validation checks
    - Validate configuration against vendor schemas
    - Provide descriptive error messages for syntax errors
    - _Requirements: 2.5, 11.2_
  
  - [x] 7.3 Implement configuration rollback on failure
    - Capture previous configuration state before changes
    - Implement rollback mechanism on configuration failure
    - Report errors with remediation suggestions
    - _Requirements: 2.6_

- [x] 8. Checkpoint - Verify multi-vendor configuration
  - Deploy multi-vendor topology with all 4 vendors
  - Apply configurations to all devices
  - Verify configurations are idempotent (apply twice, same result)
  - Ensure all tests pass, ask user if questions arise

### Phase 3: EVPN/VXLAN Configuration

- [x] 9. Create EVPN/VXLAN data model
  - [x] 9.1 Define EVPN/VXLAN variables in group_vars
    - Create group_vars/leafs.yml with evpn_vxlan structure
    - Define VNI ranges, route distinguishers, route targets
    - Define VLAN to VNI mappings
    - _Requirements: 2.1_
  
  - [x] 9.2 Create EVPN/VXLAN configuration templates
    - Create vendor-agnostic data model
    - Define template structure for all vendors
    - _Requirements: 2.8_


- [x] 10. Implement SR Linux EVPN/VXLAN role
  - [x] 10.1 Create gnmi_evpn_vxlan role for SR Linux
    - Create ansible/methods/srlinux_gnmi/roles/gnmi_evpn_vxlan/tasks/main.yml
    - Configure EVPN address family in BGP
    - Configure VXLAN interface and tunnel endpoints
    - Configure network instances for L2 VPNs
    - Map VLANs to VNIs
    - _Requirements: 2.1_
  
  - [ ]* 10.2 Write property test for EVPN configuration idempotency
    - **Property 6: Configuration Idempotency**
    - **Validates: Requirements 2.7**
    - Test that applying EVPN config multiple times produces identical state
  
  - [x] 10.3 Create EVPN verification tasks
    - Verify EVPN routes are advertised
    - Verify VXLAN tunnels are established
    - Check VNI to VLAN mappings
    - _Requirements: 7.2_

- [x] 11. Implement Arista EVPN/VXLAN role
  - [x] 11.1 Create eos_evpn_vxlan role
    - Create ansible/roles/eos_evpn_vxlan/tasks/main.yml
    - Configure EVPN in BGP address family
    - Configure VXLAN interface
    - Configure VLANs and VNI mappings
    - _Requirements: 2.1_
  
  - [ ]* 11.2 Write unit tests for Arista EVPN role
    - Test EVPN configuration generation
    - Test VXLAN tunnel configuration
    - _Requirements: 2.1_

- [x] 12. Implement SONiC and Juniper EVPN/VXLAN roles
  - [x] 12.1 Create sonic_evpn_vxlan role
    - Create ansible/roles/sonic_evpn_vxlan/tasks/main.yml
    - Configure EVPN using SONiC data models
    - _Requirements: 2.1_
  
  - [x] 12.2 Create junos_evpn_vxlan role
    - Create ansible/roles/junos_evpn_vxlan/tasks/main.yml
    - Configure EVPN using Junos modules
    - _Requirements: 2.1_

- [x] 13. Checkpoint - Verify EVPN/VXLAN fabric
  - Deploy EVPN/VXLAN fabric across all vendors
  - Verify EVPN routes are exchanged
  - Verify VXLAN tunnels are operational
  - Ensure all tests pass, ask user if questions arise


### Phase 4: Telemetry Normalization

- [x] 14. Create comprehensive normalization mapping table
  - [x] 14.1 Document vendor-specific to OpenConfig path mappings
    - Create monitoring/gnmic/normalization-mappings.yml
    - Map interface counters for all vendors
    - Map BGP metrics for all vendors
    - Map LLDP metrics for all vendors
    - Map OSPF metrics for all vendors
    - _Requirements: 4.1, 4.2, 4.6_
  
  - [x] 14.2 Define metric transformation rules
    - Document value transformations (units, scales)
    - Define label transformations (interface names, states)
    - Specify vendor prefix for native-only metrics
    - _Requirements: 4.1, 4.2, 4.5_

- [x] 15. Implement gNMIc metric normalization processors
  - [x] 15.1 Configure SR Linux metric normalization
    - Add event-convert processors for SR Linux paths
    - Transform /interface/statistics/* to network_interface_*
    - Transform BGP paths to normalized names
    - Add vendor label to all metrics
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 15.2 Configure Arista metric normalization
    - Add event-convert processors for Arista paths
    - Transform OpenConfig paths to normalized names
    - Normalize interface names (Ethernet1/1 -> eth1_1)
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 15.3 Configure SONiC metric normalization
    - Add event-convert processors for SONiC paths
    - Transform SONiC-specific paths to normalized names
    - Handle SONiC interface naming conventions
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 15.4 Configure Juniper metric normalization
    - Add event-convert processors for Juniper paths
    - Transform Juniper paths to normalized names
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 15.5 Write property test for metric transformation preservation
    - **Property 14: Metric Transformation Preservation**
    - **Validates: Requirements 4.3**
    - Test that metric values and timestamps are unchanged after normalization


  - [ ]* 15.6 Write property test for cross-vendor metric consistency
    - **Property 15: Cross-Vendor Metric Path Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.4**
    - Test that equivalent metrics from different vendors have identical normalized paths

- [x] 16. Implement Prometheus relabeling rules
  - [x] 16.1 Add interface name normalization rules
    - Create metric_relabel_configs in prometheus.yml
    - Normalize ethernet-1/1, Ethernet1/1, etc. to eth1_1
    - Add interface_normalized label
    - _Requirements: 4.1, 4.2_
  
  - [x] 16.2 Add vendor-specific relabeling rules
    - Preserve vendor label from gNMIc
    - Add device role labels (spine, leaf)
    - Add topology labels
    - _Requirements: 4.2_
  
  - [x] 16.3 Implement transformation rule validation
    - Create startup validation script for gNMIc config
    - Validate all transformation rules are syntactically correct
    - Test transformation rules with sample data
    - _Requirements: 4.7_

- [x] 17. Create normalization validation script
  - [x] 17.1 Implement metric normalization verification
    - Create validation/check_normalization.py
    - Query Prometheus for normalized metrics
    - Verify all vendors produce expected metric names
    - Check that metric values are preserved
    - _Requirements: 8.3_
  
  - [x]* 17.2 Write unit tests for normalization validation
    - Test validation script with known good data
    - Test detection of normalization failures
    - _Requirements: 8.3_

- [x] 18. Checkpoint - Verify metric normalization
  - Collect metrics from all 4 vendors
  - Verify normalized metric names are consistent
  - Verify metric values and timestamps are preserved
  - Ensure all tests pass, ask user if questions arise


### Phase 5: Universal Monitoring Dashboards

- [x] 19. Create universal interface statistics dashboard
  - [x] 19.1 Design dashboard with normalized metric queries
    - Create monitoring/grafana/provisioning/dashboards/universal-interfaces.json
    - Use network_interface_in_octets and network_interface_out_octets
    - Query by interface_normalized label
    - Support filtering by vendor, role, device
    - _Requirements: 5.1, 5.2_
  
  - [x] 19.2 Add interface bandwidth panels
    - Calculate bandwidth using rate() function
    - Display in/out traffic for all interfaces
    - Use consistent legend format across vendors
    - _Requirements: 5.2_
  
  - [x] 19.3 Add interface error and discard panels
    - Display error counters
    - Display discard counters
    - Show interface operational state
    - _Requirements: 5.2_

- [x] 20. Create universal BGP monitoring dashboard
  - [x] 20.1 Design BGP session status dashboard
    - Create monitoring/grafana/provisioning/dashboards/universal-bgp.json
    - Use network_bgp_session_state metric
    - Display session state for all vendors
    - Color-code by session state (established=green, idle=red)
    - _Requirements: 5.1, 5.3_
  
  - [x] 20.2 Add BGP route statistics panels
    - Display received routes per neighbor
    - Display advertised routes per neighbor
    - Show route counts by address family
    - _Requirements: 5.3_

- [x] 21. Create universal LLDP topology dashboard
  - [x] 21.1 Design LLDP neighbor dashboard
    - Create monitoring/grafana/provisioning/dashboards/universal-lldp.json
    - Use network_lldp_neighbor metric
    - Display topology connections
    - Show neighbor details (system name, port)
    - _Requirements: 5.1, 5.4_


- [x] 22. Create vendor-specific drill-down dashboards
  - [x] 22.1 Create vendor-specific interface dashboards
    - Create separate dashboards for native vendor metrics
    - Link from universal dashboard to vendor-specific views
    - Display vendor-specific metrics not available in OpenConfig
    - _Requirements: 5.6, 6.3_
  
  - [x] 22.2 Implement dashboard persistence
    - Configure Grafana provisioning for all dashboards
    - Ensure dashboards persist across Grafana restarts
    - Version control dashboard JSON files
    - _Requirements: 5.7_
  
  - [ ]* 22.3 Write property test for universal query vendor independence
    - **Property 18: Universal Query Vendor Independence**
    - **Validates: Requirements 5.5**
    - Test that adding new vendor doesn't require dashboard modifications

- [x] 23. Checkpoint - Verify universal dashboards
  - Open Grafana and verify all universal dashboards work
  - Verify queries return data from all 4 vendors
  - Verify drill-down to vendor-specific dashboards works
  - Ensure all tests pass, ask user if questions arise

### Phase 6: Validation Framework

- [ ] 24. Create validation engine core
  - [ ] 24.1 Implement ValidationEngine class
    - Create validation/engine.py with ValidationEngine class
    - Implement validate_all() method orchestrating all checks
    - Implement validate_deployment() for device reachability
    - Implement validate_configuration() for config state
    - Implement validate_telemetry() for metric collection
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2_
  
  - [ ] 24.2 Implement ValidationResult data model
    - Create structured result format with status, message, remediation
    - Support pass/fail/warning/error states
    - Include expected vs actual values
    - _Requirements: 7.7, 8.7_
  
  - [ ] 24.3 Create validation report generator
    - Implement generate_report() method
    - Output structured JSON format
    - Include summary statistics (total, passed, failed)
    - Add timestamps and duration
    - _Requirements: 7.7, 8.7_


- [ ] 25. Implement configuration validation checks
  - [ ] 25.1 Create BGP session validation
    - Implement validate_bgp_sessions() in validation/checks.py
    - Query BGP neighbor state via gNMI
    - Compare actual vs expected neighbors
    - Identify missing, unexpected, and non-established sessions
    - Generate remediation suggestions
    - _Requirements: 7.1, 7.5_
  
  - [ ] 25.2 Create EVPN route validation
    - Implement validate_evpn_routes()
    - Query EVPN routing table
    - Verify routes are advertised and received
    - Check route targets and distinguishers
    - _Requirements: 7.2, 7.5_
  
  - [ ] 25.3 Create LLDP neighbor validation
    - Implement validate_lldp_neighbors()
    - Query LLDP neighbor information
    - Compare against topology definition
    - Identify missing or unexpected neighbors
    - _Requirements: 7.3, 7.5_
  
  - [ ] 25.4 Create interface state validation
    - Implement validate_interface_states()
    - Query interface operational states
    - Compare against expected states
    - Check admin state vs operational state mismatches
    - _Requirements: 7.4, 7.5_
  
  - [ ]* 25.5 Write property test for validation performance
    - **Property 26: Validation Performance**
    - **Validates: Requirements 7.6**
    - Test that validation completes within 60 seconds for various topology sizes

- [ ] 26. Implement telemetry validation checks
  - [ ] 26.1 Create telemetry streaming verification
    - Implement check_telemetry_streaming() in validation/checks.py
    - Verify gNMI subscriptions are active
    - Check subscription state for each device
    - Detect devices not streaming telemetry
    - _Requirements: 8.1, 8.5_
  
  - [ ] 26.2 Create Prometheus metric verification
    - Implement check_prometheus_metrics()
    - Query Prometheus for metrics from each device
    - Verify metrics were received in last 60 seconds
    - Identify devices with missing metrics
    - _Requirements: 8.2, 8.5_


  - [ ] 26.3 Create metric normalization verification
    - Implement check_metric_normalization()
    - Query Prometheus for normalized metric names
    - Verify all vendors produce expected OpenConfig paths
    - Check for missing normalizations
    - _Requirements: 8.3, 8.5_
  
  - [ ] 26.4 Create universal query validation
    - Implement check_universal_queries()
    - Execute universal query patterns
    - Verify data returned from all vendors
    - Check for vendor-specific query failures
    - _Requirements: 8.4, 8.5_
  
  - [ ]* 26.5 Write unit tests for telemetry validation
    - Test each validation check with known good/bad data
    - Test error handling and remediation generation
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 27. Create validation CLI tool
  - [ ] 27.1 Implement validate-lab.sh script
    - Create scripts/validate-lab.sh
    - Accept topology and expected state as inputs
    - Call validation engine
    - Output results in JSON format
    - Exit with appropriate status code
    - _Requirements: 7.7, 8.7_
  
  - [x] 27.2 Add validation report formatting
    - Implement human-readable output format
    - Add colored output for pass/fail
    - Display summary statistics
    - Show remediation suggestions for failures
    - _Requirements: 7.5, 7.7_
  
  - [ ] 27.3 Integrate validation into deployment workflow
    - Add validation step to deploy.sh
    - Run validation after configuration deployment
    - Fail deployment if critical validations fail
    - _Requirements: 7.6_

- [ ] 28. Checkpoint - Verify validation framework
  - Run validation on deployed lab
  - Verify all validation checks execute
  - Introduce intentional failures and verify detection
  - Verify remediation suggestions are helpful
  - Ensure all tests pass, ask user if questions arise


### Phase 7: State Management

- [ ] 29. Implement lab state export
  - [ ] 29.1 Create state export module
    - Create state/export.py with export_lab_state() function
    - Export topology definition
    - Export device configurations via gNMI get
    - Export metrics snapshot from Prometheus
    - Include metadata (timestamp, version, description)
    - _Requirements: 12.1, 12.3_
  
  - [ ] 29.2 Implement configuration export for all vendors
    - Query full configuration from each device
    - Store vendor and OS information
    - Handle vendor-specific configuration formats
    - _Requirements: 12.1_
  
  - [ ] 29.3 Implement Prometheus snapshot export
    - Create Prometheus snapshot using admin API
    - Store snapshot path in state file
    - Include time range information
    - _Requirements: 12.1_
  
  - [ ]* 29.4 Write property test for state export completeness
    - **Property 41: Lab State Export Completeness**
    - **Validates: Requirements 12.1**
    - Test that exported state includes topology, configs, and metrics

- [ ] 30. Implement lab state restore
  - [ ] 30.1 Create state restore module
    - Create state/restore.py with restore_lab_state() function
    - Validate snapshot before restoration
    - Deploy topology from snapshot
    - Restore configurations to devices
    - Optionally restore Prometheus metrics
    - _Requirements: 12.2, 12.4_
  
  - [ ] 30.2 Implement snapshot validation
    - Create validate_snapshot() function
    - Check required fields are present
    - Validate topology structure
    - Verify configuration formats
    - Reject invalid snapshots with clear errors
    - _Requirements: 12.4_


  - [ ] 30.3 Implement configuration restoration for all vendors
    - Apply configurations using vendor-specific methods
    - Handle vendor differences in configuration format
    - Verify configuration applied successfully
    - _Requirements: 12.2_
  
  - [ ]* 30.4 Write property test for state round-trip
    - **Property 42: Lab State Round-Trip**
    - **Validates: Requirements 12.2**
    - Test that exporting then restoring produces equivalent lab state

- [ ] 31. Implement state comparison
  - [ ] 31.1 Create state comparison module
    - Create state/compare.py with compare_snapshots() function
    - Compare topology definitions
    - Compare device configurations
    - Compare metric snapshots
    - _Requirements: 12.6_
  
  - [ ] 31.2 Implement configuration diff generation
    - Create diff_configurations() function
    - Generate structured diff showing changes
    - Support vendor-specific configuration formats
    - Highlight added, removed, and modified sections
    - _Requirements: 11.7, 12.6_
  
  - [ ] 31.3 Create state comparison CLI tool
    - Create scripts/compare-states.sh
    - Accept two snapshot files as input
    - Display human-readable diff
    - Output structured diff in JSON
    - _Requirements: 12.6_

- [ ] 32. Implement incremental state updates
  - [ ] 32.1 Create incremental update module
    - Implement apply_state_update() function
    - Calculate diff between current and target state
    - Apply only changed configurations
    - Avoid full redeployment when possible
    - _Requirements: 12.5_
  
  - [ ]* 32.2 Write unit tests for incremental updates
    - Test update with configuration changes only
    - Test update with topology changes
    - Test handling of conflicts
    - _Requirements: 12.5_


- [ ] 33. Create state management CLI tools
  - [ ] 33.1 Create export-lab-state.sh script
    - Accept lab name and output file as parameters
    - Call state export module
    - Display export summary
    - _Requirements: 12.1_
  
  - [ ] 33.2 Create restore-lab-state.sh script
    - Accept snapshot file as parameter
    - Validate snapshot before restoration
    - Call state restore module
    - Display restoration progress
    - _Requirements: 12.2_
  
  - [ ] 33.3 Ensure state files are version control friendly
    - Use YAML format for state snapshots
    - Format with consistent indentation
    - Sort keys alphabetically where possible
    - _Requirements: 12.7_

- [ ] 34. Checkpoint - Verify state management
  - Export lab state to snapshot file
  - Destroy lab
  - Restore lab from snapshot
  - Verify restored lab matches original
  - Compare two snapshots and verify diff generation
  - Ensure all tests pass, ask user if questions arise

### Phase 8: Performance Benchmarking

- [ ] 35. Create benchmarking framework
  - [ ] 35.1 Implement BenchmarkRunner class
    - Create benchmarks/framework.py with BenchmarkRunner class
    - Implement benchmark_deployment() method
    - Implement benchmark_configuration() method
    - Implement benchmark_telemetry() method
    - Store results with timestamps
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ] 35.2 Implement deployment time benchmarking
    - Measure time from containerlab deploy to all devices ready
    - Test with various topology sizes (2, 4, 8, 16 devices)
    - Record per-device boot time
    - _Requirements: 9.4_
  
  - [ ] 35.3 Implement configuration time benchmarking
    - Measure time to apply full configuration
    - Test with various configuration complexities
    - Record per-device configuration time
    - _Requirements: 9.4_


- [ ] 36. Implement resource utilization measurement
  - [ ] 36.1 Create device CPU utilization measurement
    - Query CPU usage from devices via gNMI
    - Measure during idle and under telemetry load
    - Verify telemetry collection uses <5% CPU
    - _Requirements: 3.7, 9.1_
  
  - [ ] 36.2 Create collector resource measurement
    - Measure gNMIc CPU and memory usage
    - Monitor resource usage over time
    - Identify resource consumption patterns
    - _Requirements: 9.2_
  
  - [ ] 36.3 Create metric ingestion rate measurement
    - Query Prometheus ingestion rate
    - Measure metrics per second per device
    - Calculate total lab metric throughput
    - _Requirements: 9.3_
  
  - [ ]* 36.4 Write property test for telemetry CPU limit
    - **Property 7 (from design): Telemetry CPU usage**
    - **Validates: Requirements 3.7**
    - Test that telemetry collection uses <5% device CPU

- [ ] 37. Create performance reporting
  - [ ] 37.1 Implement performance report generator
    - Create benchmarks/reports.py with generate_performance_report()
    - Aggregate benchmark results
    - Calculate statistics (mean, median, p95, p99)
    - Generate summary report
    - _Requirements: 9.5_
  
  - [ ] 37.2 Implement vendor performance comparison
    - Create compare_vendor_performance() function
    - Compare deployment time across vendors
    - Compare configuration time across vendors
    - Compare resource usage across vendors
    - _Requirements: 9.5_
  
  - [ ] 37.3 Implement performance trend tracking
    - Store benchmark results in time-series database
    - Track performance metrics over time
    - Detect performance degradation
    - Generate trend reports
    - _Requirements: 9.7_


- [ ] 38. Create benchmarking CLI tools
  - [ ] 38.1 Create run-benchmarks.sh script
    - Accept benchmark type as parameter (deployment, config, telemetry, all)
    - Run selected benchmarks
    - Generate performance report
    - Output results in JSON and human-readable format
    - _Requirements: 9.5_
  
  - [ ] 38.2 Implement bottleneck identification
    - Analyze benchmark results
    - Identify performance bottlenecks
    - Provide optimization recommendations
    - _Requirements: 9.6_
  
  - [ ]* 38.3 Write unit tests for benchmarking framework
    - Test benchmark execution
    - Test report generation
    - Test vendor comparison
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 39. Checkpoint - Verify performance benchmarking
  - Run all benchmarks on deployed lab
  - Verify performance reports are generated
  - Review vendor comparison results
  - Check that performance meets requirements
  - Ensure all tests pass, ask user if questions arise

### Phase 9: Testing and Documentation

- [x] 40. Implement property-based tests
  - [x] 40.1 Set up property testing framework
    - Install hypothesis for Python
    - Create tests/property/ directory structure
    - Configure hypothesis settings (100+ examples per test)
    - _Requirements: 15.1, 15.2, 15.3, 15.4_
  
  - [x] 40.2 Create test data generators
    - Implement topologies() strategy for random topology generation
    - Implement bgp_configurations() strategy
    - Implement metrics() strategy for vendor metrics
    - Implement configurations() strategy
    - _Requirements: 15.1, 15.2, 15.3, 15.4_


  - [ ]* 40.3 Implement deployment property tests
    - **Property 1: Deployment Lifecycle Completeness**
    - Test deploy then destroy leaves no resources
    - **Property 2: Multi-Vendor Topology Support**
    - Test all vendor combinations deploy successfully
    - **Property 3: OS Detection Accuracy**
    - Test OS detection for all vendors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.7_
  
  - [ ]* 40.4 Implement configuration property tests
    - **Property 6: Configuration Idempotency**
    - Test applying config multiple times produces same state
    - **Property 10: Configuration Round-Trip Preservation**
    - Test parse-format-parse produces equivalent object
    - _Requirements: 2.7, 11.4_
  
  - [ ]* 40.5 Implement telemetry property tests
    - **Property 14: Metric Transformation Preservation**
    - Test values and timestamps unchanged after normalization
    - **Property 15: Cross-Vendor Metric Path Consistency**
    - Test equivalent metrics have identical normalized paths
    - _Requirements: 4.3, 4.4_
  
  - [ ]* 40.6 Implement state management property tests
    - **Property 42: Lab State Round-Trip**
    - Test export-restore produces equivalent state
    - **Property 47: Version Control Friendly Format**
    - Test snapshots are text-based YAML/JSON
    - _Requirements: 12.2, 12.7_

- [x] 41. Implement unit tests
  - [x] 41.1 Create deployment unit tests
    - Create tests/unit/test_deployment.py
    - Test specific topology configurations
    - Test error conditions (invalid topology, missing images)
    - Test health check functionality
    - _Requirements: 15.1_
  
  - [x] 41.2 Create configuration unit tests
    - Create tests/unit/test_configuration.py
    - Test configuration generation for each vendor
    - Test syntax validation
    - Test rollback on failure
    - _Requirements: 15.2_


  - [x] 41.3 Create telemetry unit tests
    - Create tests/unit/test_telemetry.py
    - Test gNMI subscription creation
    - Test metric normalization rules
    - Test Prometheus export
    - _Requirements: 15.3_
  
  - [x] 41.4 Create validation unit tests
    - Create tests/unit/test_validation.py
    - Test each validation check
    - Test error detection and remediation
    - Test report generation
    - _Requirements: 15.1_
  
  - [x] 41.5 Create state management unit tests
    - Create tests/unit/test_state_management.py
    - Test state export and restore
    - Test state comparison
    - Test incremental updates
    - _Requirements: 15.1_

- [x] 42. Implement integration tests
  - [x] 42.1 Create end-to-end workflow tests
    - Create tests/integration/test_end_to_end.py
    - Test complete workflow: deploy → configure → validate → monitor
    - Test with each vendor individually
    - Test with multi-vendor topology
    - _Requirements: 15.1_
  
  - [x] 42.2 Create multi-vendor integration tests
    - Create tests/integration/test_multi_vendor.py
    - Test all vendor combinations
    - Test vendor interoperability (BGP sessions between vendors)
    - Test telemetry collection from mixed vendors
    - _Requirements: 15.6_
  
  - [x] 42.3 Create monitoring stack integration tests
    - Create tests/integration/test_monitoring_stack.py
    - Test gNMIc → Prometheus → Grafana pipeline
    - Test metric persistence
    - Test dashboard queries
    - _Requirements: 15.1_


- [x] 43. Set up continuous integration
  - [x] 43.1 Create GitHub Actions workflow
    - Create .github/workflows/ci.yml
    - Configure unit test job
    - Configure property test job
    - Configure integration test job (skipped in CI, local only)
    - _Requirements: 15.1, 15.2, 15.3, 15.4_
  
  - [x] 43.2 Configure test execution
    - Set up uv for fast Python environment management
    - Configure lint gates (Ruff, Mypy, yamllint, ShellCheck, ansible-lint)
    - Configure security gates (Bandit, Trivy, Checkov, Gitleaks)
    - Set test timeouts
    - _Requirements: 15.7_
  
  - [x] 43.3 Implement test failure reporting
    - Configure detailed failure reports with JUnit XML output
    - Upload test artifacts and coverage reports
    - Generate pipeline summary with stage-by-stage results
    - PR coverage comments via py-cov-action
    - _Requirements: 15.5_
  
  - [ ]* 43.4 Write property test for test suite performance
    - **Property 55: Test Suite Performance**
    - **Validates: Requirements 15.7**
    - Test that full test suite completes within 10 minutes

- [x] 44. Create user documentation
  - [x] 44.1 Write setup guide
    - Create docs/user/setup.md
    - Document prerequisites (Docker, containerlab, Ansible)
    - Provide step-by-step installation instructions
    - Include troubleshooting for common setup issues
    - _Requirements: 13.1_
  
  - [x] 44.2 Write configuration guide
    - Create docs/user/configuration.md
    - Document topology definition format
    - Explain device inventory structure
    - Provide configuration examples for each vendor
    - _Requirements: 13.3_
  
  - [x] 44.3 Write monitoring guide
    - Create docs/user/monitoring.md
    - Explain metric normalization
    - Document universal dashboard usage
    - Provide query examples
    - _Requirements: 13.4_


  - [x] 44.4 Write troubleshooting guide
    - Create docs/user/troubleshooting.md
    - Document common issues and solutions
    - Provide debugging techniques
    - Include vendor-specific troubleshooting
    - _Requirements: 13.5_
  
  - [x] 44.5 Create example topologies
    - Create topologies/examples/ directory
    - Provide 2-spine-4-leaf example
    - Provide multi-vendor example
    - Provide EVPN/VXLAN fabric example
    - Document expected outcomes for each
    - _Requirements: 13.3_

- [x] 45. Create developer documentation
  - [x] 45.1 Write architecture guide
    - Create docs/developer/architecture.md
    - Document component interactions
    - Include architecture diagrams
    - Explain design decisions
    - _Requirements: 13.6_
  
  - [x] 45.2 Write vendor extension guide
    - Create docs/developer/vendor-extension.md
    - Document how to add new vendor support
    - Provide vendor integration template
    - List required components for vendor integration
    - Include example implementations
    - _Requirements: 10.1, 10.2, 10.7_
  
  - [x] 45.3 Write contribution guide
    - Create docs/developer/contributing.md
    - Document code style and conventions
    - Explain testing requirements
    - Provide pull request guidelines
    - _Requirements: 13.1_
  
  - [x] 45.4 Document vendor-specific requirements
    - Create docs/developer/vendor-requirements.md
    - Document limitations for each vendor
    - List vendor-specific configuration requirements
    - Document OpenConfig support status per vendor
    - _Requirements: 13.2_


  - [x] 45.5 Create metric normalization documentation
    - Create docs/developer/metric-normalization.md
    - Document all normalization mappings
    - Explain transformation rules
    - Provide examples for each vendor
    - _Requirements: 13.4_

- [x] 46. Create API documentation
  - [x] 46.1 Document validation engine API
    - Document ValidationEngine class and methods
    - Document ValidationResult structure
    - Provide usage examples
    - _Requirements: 13.1_
  
  - [x] 46.2 Document state management API
    - Document export/restore functions
    - Document state snapshot format
    - Provide usage examples
    - _Requirements: 13.1_
  
  - [x] 46.3 Document benchmarking API
    - Document BenchmarkRunner class
    - Document performance report format
    - Provide usage examples
    - _Requirements: 13.1_

- [x] 47. Create changelog and versioning
  - [x] 47.1 Create CHANGELOG.md
    - Document all significant changes
    - Use semantic versioning
    - Include migration guides for breaking changes
    - _Requirements: 13.7_
  
  - [x] 47.2 Create version tracking
    - Add version information to state snapshots
    - Track compatibility between versions
    - Document version upgrade procedures
    - _Requirements: 13.7_

- [x] 48. Final checkpoint - Complete testing and documentation
  - Run full test suite and verify all tests pass
  - Review all documentation for completeness
  - Verify examples work as documented
  - Ensure changelog is up to date
  - Ask user if questions arise


## Additional High-Priority Tasks

### Monitoring Stack Reliability

- [ ] 49. Implement monitoring stack health checks
  - [ ] 49.1 Create health check endpoints
    - Implement health checks for Prometheus
    - Implement health checks for Grafana
    - Implement health checks for gNMIc
    - _Requirements: 14.3_
  
  - [ ] 49.2 Implement storage capacity monitoring
    - Monitor Prometheus storage usage
    - Alert when storage reaches 80% capacity
    - _Requirements: 14.2_
  
  - [ ] 49.3 Implement collector failure alerting
    - Detect gNMIc collector failures
    - Alert within 60 seconds of failure
    - _Requirements: 14.4_
  
  - [ ]* 49.4 Write property test for metric persistence
    - **Property 48: Metric Persistence**
    - **Validates: Requirements 14.1**
    - Test that metrics persist across Prometheus restarts

- [ ] 50. Implement monitoring stack backup and restore
  - [ ] 50.1 Create Prometheus backup functionality
    - Implement automated Prometheus snapshots
    - Store snapshots with retention policy
    - _Requirements: 14.6_
  
  - [ ] 50.2 Create Prometheus restore functionality
    - Implement restore from snapshot
    - Verify data integrity after restore
    - _Requirements: 14.6_
  
  - [ ]* 50.3 Write property test for backup round-trip
    - **Property 52: Metric Data Backup Round-Trip**
    - **Validates: Requirements 14.6**
    - Test that backup-restore preserves all metrics


### Configuration Parsing and Validation

- [ ] 51. Implement configuration parsing
  - [ ] 51.1 Create configuration parser
    - Implement parse_configuration() function
    - Parse vendor-specific configuration formats
    - Convert to structured format
    - Handle syntax errors with descriptive messages
    - _Requirements: 11.1, 11.2_
  
  - [ ] 51.2 Create configuration formatter
    - Implement format_configuration() function
    - Generate valid vendor-specific syntax
    - Support all vendor configuration formats
    - _Requirements: 11.3_
  
  - [ ]* 51.3 Write property test for configuration round-trip
    - **Property 10: Configuration Round-Trip Preservation**
    - **Validates: Requirements 11.4**
    - Test parse-format-parse produces equivalent object

- [ ] 52. Implement configuration validation
  - [ ] 52.1 Create schema validation
    - Implement validate_configuration() function
    - Validate against vendor-specific schemas
    - Check for required fields
    - _Requirements: 11.5_
  
  - [ ] 52.2 Create conflict detection
    - Detect duplicate IP addresses
    - Detect overlapping VLAN ranges
    - Detect BGP AS conflicts
    - Provide specific error messages
    - _Requirements: 11.6_
  
  - [ ]* 52.3 Write property test for conflict detection
    - **Property 39: Configuration Conflict Detection**
    - **Validates: Requirements 11.6**
    - Test that conflicts are detected before deployment

### Vendor Extension Framework

- [ ] 53. Create vendor extension framework
  - [ ] 53.1 Create vendor integration template
    - Create templates/vendor-integration/ directory
    - Provide role templates for new vendors
    - Include configuration examples
    - Document required methods
    - _Requirements: 10.1, 10.2_


  - [ ] 53.2 Create vendor capability detection
    - Implement detect_vendor_capabilities() function
    - Query device for supported features
    - Report missing capabilities
    - _Requirements: 10.5_
  
  - [ ] 53.3 Create vendor module validation
    - Implement validate_vendor_module() function
    - Check required components are present
    - Validate role structure
    - Verify configuration templates
    - _Requirements: 10.3_
  
  - [ ]* 53.4 Write unit tests for vendor extension framework
    - Test vendor module validation
    - Test capability detection
    - Test integration template usage
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [ ] 54. Create metric normalizer configuration schema
  - [ ] 54.1 Define normalization configuration schema
    - Create schema for vendor metric mappings
    - Define transformation rule format
    - Document schema with examples
    - _Requirements: 10.4_
  
  - [ ] 54.2 Implement schema validation
    - Validate normalization configurations at startup
    - Check for missing or invalid mappings
    - Provide clear error messages
    - _Requirements: 10.4_

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (55 total properties from design)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows

## Success Criteria

The implementation will be considered complete when:

1. All 4 vendors (SR Linux, Arista, SONiC, Juniper) can be deployed in a single topology
2. All vendors can be configured with EVPN/VXLAN, BGP, and OSPF
3. Universal Grafana queries work across all vendors without modification
4. Validation framework detects configuration issues with remediation suggestions
5. Lab states can be exported and restored reliably
6. Performance benchmarks show acceptable resource usage
7. All non-optional tests pass
8. Documentation enables new users to deploy lab in under 30 minutes


## Implementation Roadmap Summary

### Phase 1: Multi-Vendor Topology Deployment (Tasks 1-3)
- Extend topology support for Arista, SONiC, Juniper
- Implement OS detection via gNMI capabilities
- Update deployment and health check scripts

### Phase 2: Multi-Vendor Configuration Roles (Tasks 4-8)
- Create Arista EOS roles (interfaces, BGP, OSPF)
- Create SONiC roles (interfaces, BGP, OSPF)
- Create Juniper roles (interfaces, BGP, OSPF)
- Enhance dispatcher pattern for multi-vendor routing
- Implement configuration validation and rollback

### Phase 3: EVPN/VXLAN Configuration (Tasks 9-13)
- Define EVPN/VXLAN data model
- Implement EVPN roles for all vendors
- Create EVPN verification and validation

### Phase 4: Telemetry Normalization (Tasks 14-18)
- Create comprehensive normalization mapping tables
- Implement gNMIc processors for all vendors
- Configure Prometheus relabeling rules
- Create normalization validation scripts

### Phase 5: Universal Monitoring Dashboards (Tasks 19-23)
- Create universal interface statistics dashboard
- Create universal BGP monitoring dashboard
- Create universal LLDP topology dashboard
- Implement vendor-specific drill-down dashboards

### Phase 6: Validation Framework (Tasks 24-28)
- Create validation engine core
- Implement configuration validation checks (BGP, EVPN, LLDP, interfaces)
- Implement telemetry validation checks
- Create validation CLI tools

### Phase 7: State Management (Tasks 29-34)
- Implement lab state export (topology, configs, metrics)
- Implement lab state restore with validation
- Create state comparison and diff tools
- Support incremental state updates

### Phase 8: Performance Benchmarking (Tasks 35-39)
- Create benchmarking framework
- Measure deployment, configuration, and telemetry performance
- Implement resource utilization measurement
- Generate performance reports and vendor comparisons

### Phase 9: Testing and Documentation (Tasks 40-48)
- Implement property-based tests (55 properties)
- Implement unit tests for all components
- Implement integration tests for workflows
- Create user documentation (setup, configuration, monitoring, troubleshooting)
- Create developer documentation (architecture, vendor extension, contribution)
- Set up continuous integration

### Additional High-Priority Tasks (Tasks 49-54)
- Monitoring stack reliability and health checks
- Configuration parsing and validation
- Vendor extension framework

## Dependencies

- Phase 2 depends on Phase 1 (need OS detection for dispatcher)
- Phase 3 depends on Phase 2 (need basic BGP roles for EVPN)
- Phase 4 can run in parallel with Phase 3
- Phase 5 depends on Phase 4 (need normalized metrics for universal dashboards)
- Phase 6 can start after Phase 2 (basic validation) and enhance after Phase 3
- Phase 7 can run in parallel with Phase 6
- Phase 8 can run in parallel with Phase 6-7
- Phase 9 should run throughout (test as you build) and finalize at end

## Estimated Timeline

- Phase 1: 2 weeks
- Phase 2: 3 weeks
- Phase 3: 2 weeks
- Phase 4: 2 weeks
- Phase 5: 1 week
- Phase 6: 2 weeks
- Phase 7: 2 weeks
- Phase 8: 1 week
- Phase 9: 2 weeks
- Additional tasks: 1 week

**Total: ~18 weeks** (can be reduced with parallel work and prioritization)

