# Implementation Plan: gNMIc Metric Normalization

## Overview

Move metric name normalization from ~50 Prometheus `metric_relabel_configs` regex rules into gNMIc event processors. Implementation proceeds tier-by-tier: Tier 1 OpenConfig processors first, then Tier 2 SR Linux native processors, then Prometheus reduction, then dashboard updates, then validation scripts.

## Tasks

- [x] 1. Add Tier 1 OpenConfig interface processor to gNMIc config
  - [x] 1.1 Add `normalize-oc-interfaces` processor to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for all 18 interface metrics (in_octets, out_octets, in_packets, out_packets, in_errors, out_errors, in_discards, out_discards, in_unicast_packets, out_unicast_packets, in_broadcast_packets, out_broadcast_packets, in_multicast_packets, out_multicast_packets, carrier_transitions, in_fcs_errors, oper_status, admin_status)
    - Each `replace` uses `apply-on: "name"`, `old:` matching the full `gnmic_oc_interface_stats_openconfig_interfaces_...` name, `new:` the `network_interface_*` name
    - Use the exact `old` names from the current `prometheus.yml` `__name__` rules (Steps 5) as reference
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 12.1_

  - [x] 1.2 Add `normalize-oc-bgp` processor to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for all 20 BGP metrics (session_state, established_transitions, last_established, peer_as, local_as, enabled, neighbor_address, peer_group, peer_type, queues_input, queues_output, messages_received_update, messages_sent_update, messages_received_notification, messages_sent_notification, remove_private_as, supported_capabilities, last_notification_received, last_notification_sent)
    - Use the exact `old` names from the current `prometheus.yml` `__name__` rules (Step 6) as reference
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 12.1_

  - [x] 1.3 Add `normalize-oc-lldp` processor to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for all 10 LLDP metrics (neighbor_system_name, neighbor_port_id, neighbor_chassis_id, neighbor_port_description, neighbor_system_description, neighbor_chassis_id_type, neighbor_port_id_type, neighbor_age, neighbor_last_update, neighbor_id)
    - Use the exact `old` names from the current `prometheus.yml` `__name__` rules (Step 7) as reference
    - _Requirements: 3.1, 3.2, 3.3, 12.1_

  - [x] 1.4 Add `normalize-oc-qos` processor to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for all 7 QoS metrics (transmit_packets, transmit_octets, dropped_packets, dropped_octets, max_queue_length, queue_name, queue_management_profile)
    - Use the exact `old` names from the current `prometheus.yml` `__name__` rules (Step 8) as reference
    - _Requirements: 4.1, 4.2, 4.3, 12.1_

- [x] 2. Add Tier 2 SR Linux native processors to gNMIc config
  - [x] 2.1 Add `normalize-srl-ospf` and `tag-srl-ospf` processors to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for 2 OSPF metrics: `network_ospf_neighbor_state`, `network_ospf_retransmission_queue_length`
    - The `old` values must match the auto-generated gNMIc names for the `srl_ospf` subscription paths (derive from the raw metric names visible in the current `vendor-srlinux.json` and `ospf-stability.json` dashboards)
    - Define `event-add-tag` processor `tag-srl-ospf` with condition `value-names: ["^network_ospf_.*"]` and `add: { vendor: nokia }`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 11.1, 12.2_

  - [x] 2.2 Add `normalize-srl-evpn` and `tag-srl-evpn` processors to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for 3 EVPN metrics: `network_evpn_oper_state`, `network_evpn_evi`, `network_evpn_ecmp`
    - The `old` values must match the auto-generated gNMIc names (derive from the raw metric names in `evpn-vxlan-stability.json` and `vendor-srlinux.json`)
    - Define `event-add-tag` processor `tag-srl-evpn` with condition `value-names: ["^network_evpn_.*"]` and `add: { vendor: nokia }`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 11.1, 12.2_

  - [x] 2.3 Add `normalize-srl-vxlan` and `tag-srl-vxlan` processors to `monitoring/gnmic/gnmic-config.yml`
    - Define `event-strings` processor with `replace` transforms for 6 VXLAN metrics: `network_vxlan_oper_state`, `network_vxlan_index`, `network_vxlan_bridge_active_entries`, `network_vxlan_bridge_total_entries`, `network_vxlan_bridge_failed_entries`, `network_vxlan_multicast_limit`
    - The `old` values must match the auto-generated gNMIc names (derive from the raw metric names in `evpn-vxlan-stability.json` and `vendor-srlinux.json`)
    - Define `event-add-tag` processor `tag-srl-vxlan` with condition `value-names: ["^network_vxlan_.*"]` and `add: { vendor: nokia }`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 11.1, 12.2_

- [x] 3. Wire processors to Prometheus output
  - [x] 3.1 Add `event-processors` list to the `prom` output in `monitoring/gnmic/gnmic-config.yml`
    - Add all 10 processors in order: `normalize-oc-interfaces`, `normalize-oc-bgp`, `normalize-oc-lldp`, `normalize-oc-qos`, `normalize-srl-ospf`, `tag-srl-ospf`, `normalize-srl-evpn`, `tag-srl-evpn`, `normalize-srl-vxlan`, `tag-srl-vxlan`
    - Tier 1 processors listed before Tier 2 processors
    - Do NOT modify any subscription paths, modes, or sample intervals
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 4. Checkpoint - Verify gNMIc config structure
  - Ensure the gNMIc config YAML is valid and all processors are correctly defined and wired. Ask the user if questions arise.

- [x] 5. Reduce Prometheus relabeling to label enrichment only
  - [x] 5.1 Remove all `__name__` regex replacement rules from `monitoring/prometheus/prometheus.yml`
    - Delete Steps 5, 6, 7, and 8 (all `source_labels: [__name__]` / `target_label: __name__` rules)
    - Retain Step 2 (vendor label), Step 3 (role derivation), Step 4 (interface normalization), and topology/fabric_type rules
    - Verify the remaining rule count is under 20
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 6. Update Grafana dashboards to use normalized metric names
  - [x] 6.1 Update `monitoring/grafana/provisioning/dashboards/vendor-srlinux.json`
    - Replace all `gnmic_srl_ospf_*` metric references with `network_ospf_*` names
    - Replace all `gnmic_srl_evpn_*` metric references with `network_evpn_*` names
    - Replace all `gnmic_srl_vxlan_*` metric references with `network_vxlan_*` names
    - Update the template variable query to use `network_ospf_neighbor_state` instead of the raw gNMIc name
    - Update `exported_source` label references to `source` (gNMIc processors preserve `source` directly)
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 6.2 Update `monitoring/grafana/provisioning/dashboards/evpn-vxlan-stability.json`
    - Replace all `gnmic_srl_evpn_*` metric references with `network_evpn_*` names
    - Replace all `gnmic_srl_vxlan_*` metric references with `network_vxlan_*` names
    - Update `exported_source` label references to `source`
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 6.3 Update `monitoring/grafana/provisioning/dashboards/ospf-stability.json`
    - Replace all `gnmic_srl_ospf_*` metric references with `network_ospf_*` names
    - Update `exported_source` label references to `source`
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 7. Update normalization mappings file
  - [x] 7.1 Verify `monitoring/gnmic/normalization-mappings.yml` covers all 58 normalized metric names
    - Cross-reference the complete metric list from the design document against the mapping file
    - Add any missing EVPN/VXLAN bridge table metric entries if not already documented
    - Ensure each Tier 2 mapping entry includes the auto-generated gNMIc name (the `old` value used in processors)
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 8. Checkpoint - Verify all config files are consistent
  - Ensure all YAML files are valid, all 58 metrics are covered, dashboards reference only `network_*` names, and Prometheus has no `__name__` rules. Ask the user if questions arise.

- [x] 9. Create Python validation script
  - [x] 9.1 Create `monitoring/tests/validate_normalization.py` with config validation functions
    - Parse `gnmic-config.yml` and verify all 10 processors exist in the `event-processors` list
    - Parse `prometheus.yml` and verify no `target_label: __name__` rules remain
    - Verify Tier 1 processors are listed before Tier 2 in the output's event-processors
    - Verify total Prometheus relabeling rule count < 20
    - Use `pyyaml` for YAML parsing
    - _Requirements: 8.5, 8.6, 9.1, 9.2, 9.4_

  - [ ]* 9.2 Write property test: Mapping correctness (Property 1)
    - **Property 1: Mapping correctness**
    - Using `hypothesis`, generate random (input_name, expected_output) pairs from the mapping file and verify the corresponding processor `replace` entry exists with matching `old`/`new` values
    - **Validates: Requirements 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 10.1**

  - [ ]* 9.3 Write property test: No metric name rewriting in Prometheus (Property 5)
    - **Property 5: No metric name rewriting in Prometheus config**
    - Using `hypothesis`, parse all rules in `metric_relabel_configs` and for each rule verify `target_label != "__name__"`
    - **Validates: Requirements 8.5**

  - [ ]* 9.4 Write property test: Dashboard metric coverage (Property 7)
    - **Property 7: Dashboard metric coverage**
    - Extract all `network_*` metric names from dashboard JSON `expr` fields, and for each name verify a processor `replace` with that `new` value exists in the gNMIc config
    - **Validates: Requirements 10.3**

  - [ ]* 9.5 Write property test: Mapping file completeness (Property 8)
    - **Property 8: Mapping file completeness**
    - Extract all `replace` transforms from gNMIc processors, and for each transform's `new` value verify a corresponding entry exists in `normalization-mappings.yml`
    - **Validates: Requirements 12.1, 12.2**

- [x] 10. Final checkpoint - Ensure all tests pass
  - Run `uv run pytest monitoring/tests/validate_normalization.py -v` and ensure all tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The design uses YAML configuration for gNMIc processors — no application code to write
- Python with `hypothesis` is used for validation scripts (project uses `uv` for Python tooling)
- The `old` values for Tier 1 processors can be copied directly from the existing Prometheus `__name__` rules
- The `old` values for Tier 2 processors must be derived from the raw metric names currently used in dashboard JSON files
- Dashboards that already use `network_*` names (universal-interfaces, universal-bgp, universal-lldp, network-congestion) need no changes
- Property tests validate config structure, not runtime behavior — gNMIc processor behavior is validated by integration testing in the lab
