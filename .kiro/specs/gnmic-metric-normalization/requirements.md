# Requirements Document

## Introduction

This feature moves metric name normalization from Prometheus `metric_relabel_configs` into gNMIc event processors. Currently, ~50 individual regex replacements in `prometheus.yml` (~300 lines) map auto-generated gNMIc metric names (e.g., `gnmic_oc_interface_stats_openconfig_interfaces_interfaces_interface_state_counters_in_octets`) to normalized `network_*` names (e.g., `network_interface_in_octets`). This approach is brittle, verbose, and does not scale when adding new vendors or metrics.

The new design uses a two-tier normalization strategy inside gNMIc:
- **Tier 1 (OpenConfig):** Light cleanup of OpenConfig-sourced metrics (interfaces, BGP, LLDP, QoS) that are universal across vendors.
- **Tier 2 (Native):** Full path-to-name mapping for vendor-specific paths (SR Linux OSPF, EVPN, VXLAN) that are not exposed via OpenConfig.

gNMIc event processors become the vendor abstraction layer. Each vendor gets its own processor chain. Prometheus relabeling is reduced to label enrichment only (vendor, role, interface normalization). Existing Grafana dashboards continue working unchanged with the same `network_*` metric names.

## Glossary

- **gNMIc_Processor**: A gNMIc event processor that transforms telemetry event names and values before export to Prometheus.
- **Normalization_Engine**: The complete set of gNMIc event processors responsible for mapping raw telemetry metric names to normalized `network_*` names.
- **OpenConfig_Subscription**: A gNMIc subscription using vendor-neutral OpenConfig YANG paths (e.g., `/interfaces/interface/state/counters`).
- **Native_Subscription**: A gNMIc subscription using vendor-specific YANG paths prefixed with a vendor module (e.g., `srl_nokia:/network-instance/.../ospf/...`).
- **Normalized_Metric**: A Prometheus metric using the `network_*` naming convention that is vendor-agnostic and consumed by Grafana dashboards.
- **Mapping_File**: The `normalization-mappings.yml` file that serves as the source of truth for all path-to-metric-name mappings.
- **Prometheus_Relabeling**: The `metric_relabel_configs` section in `prometheus.yml` that performs regex-based metric and label transformations at scrape time.
- **Label_Enrichment**: The process of adding contextual labels (vendor, role, interface_normalized) to metrics, retained in Prometheus relabeling.
- **Tier_1_Processor**: A gNMIc event processor that normalizes OpenConfig-sourced metrics common to all vendors.
- **Tier_2_Processor**: A gNMIc event processor that normalizes vendor-specific native path metrics to the common `network_*` namespace.

## Requirements

### Requirement 1: OpenConfig Interface Metric Normalization (Tier 1)

**User Story:** As a network operator, I want OpenConfig interface counter metrics normalized to `network_interface_*` names inside gNMIc, so that Prometheus receives clean metric names without regex post-processing.

#### Acceptance Criteria

1. WHEN the `oc_interface_stats` subscription delivers interface counter events, THE Tier_1_Processor SHALL rename each metric to its corresponding `network_interface_*` Normalized_Metric name as defined in the Mapping_File.
2. WHEN the `oc_interface_stats` subscription delivers `oper-status` or `admin-status` events, THE Tier_1_Processor SHALL rename the metrics to `network_interface_oper_status` and `network_interface_admin_status` respectively.
3. THE Tier_1_Processor SHALL preserve all original gNMIc labels (source, interface_name, subscription-name) on renamed interface metrics.
4. IF an interface counter event does not match any mapping in the Mapping_File, THEN THE Tier_1_Processor SHALL pass the event through unchanged.

### Requirement 2: OpenConfig BGP Metric Normalization (Tier 1)

**User Story:** As a network operator, I want OpenConfig BGP neighbor state metrics normalized to `network_bgp_*` names inside gNMIc, so that BGP monitoring dashboards work without Prometheus regex rules.

#### Acceptance Criteria

1. WHEN the `oc_bgp_neighbors` subscription delivers BGP neighbor state events, THE Tier_1_Processor SHALL rename each metric to its corresponding `network_bgp_*` Normalized_Metric name as defined in the Mapping_File.
2. THE Tier_1_Processor SHALL map `session_state` string values (IDLE, CONNECT, ACTIVE, OPENSENT, OPENCONFIRM, ESTABLISHED) to the `network_bgp_session_state` metric without altering the value representation.
3. THE Tier_1_Processor SHALL preserve all original gNMIc labels (source, neighbor_address, network_instance_name) on renamed BGP metrics.
4. IF a BGP state event does not match any mapping in the Mapping_File, THEN THE Tier_1_Processor SHALL pass the event through unchanged.

### Requirement 3: OpenConfig LLDP Metric Normalization (Tier 1)

**User Story:** As a network operator, I want OpenConfig LLDP neighbor state metrics normalized to `network_lldp_*` names inside gNMIc, so that topology discovery dashboards work without Prometheus regex rules.

#### Acceptance Criteria

1. WHEN the `oc_lldp` subscription delivers LLDP neighbor state events, THE Tier_1_Processor SHALL rename each metric to its corresponding `network_lldp_*` Normalized_Metric name as defined in the Mapping_File.
2. THE Tier_1_Processor SHALL preserve all original gNMIc labels (source, interface_name, neighbor system-name) on renamed LLDP metrics.
3. IF an LLDP state event does not match any mapping in the Mapping_File, THEN THE Tier_1_Processor SHALL pass the event through unchanged.

### Requirement 4: OpenConfig QoS Metric Normalization (Tier 1)

**User Story:** As a network operator, I want OpenConfig QoS queue state metrics normalized to `network_qos_*` names inside gNMIc, so that congestion monitoring dashboards work without Prometheus regex rules.

#### Acceptance Criteria

1. WHEN the `oc_qos_queues` subscription delivers QoS queue state events, THE Tier_1_Processor SHALL rename each metric to its corresponding `network_qos_*` Normalized_Metric name as defined in the Mapping_File.
2. THE Tier_1_Processor SHALL preserve all original gNMIc labels (source, interface_name, queue_name) on renamed QoS metrics.
3. IF a QoS state event does not match any mapping in the Mapping_File, THEN THE Tier_1_Processor SHALL pass the event through unchanged.

### Requirement 5: SR Linux Native OSPF Metric Normalization (Tier 2)

**User Story:** As a network operator, I want SR Linux native OSPF telemetry metrics normalized to `network_ospf_*` names inside gNMIc, so that OSPF monitoring works with the same metric names that future vendors will also produce.

#### Acceptance Criteria

1. WHEN the `srl_ospf` subscription delivers OSPF adjacency-state events, THE Tier_2_Processor SHALL rename the metric to `network_ospf_neighbor_state`.
2. WHEN the `srl_ospf` subscription delivers retransmission-queue-length events, THE Tier_2_Processor SHALL rename the metric to `network_ospf_retransmission_queue_length`.
3. THE Tier_2_Processor SHALL add a `vendor=nokia` label to all SR Linux OSPF metrics.
4. THE Tier_2_Processor SHALL preserve the `source`, `network_instance_name`, `area_id`, and `interface_name` labels on renamed OSPF metrics.
5. IF an SR Linux OSPF event does not match any mapping in the Mapping_File, THEN THE Tier_2_Processor SHALL pass the event through unchanged.

### Requirement 6: SR Linux Native EVPN Metric Normalization (Tier 2)

**User Story:** As a network operator, I want SR Linux native EVPN telemetry metrics normalized to `network_evpn_*` names inside gNMIc, so that EVPN monitoring works with vendor-agnostic metric names.

#### Acceptance Criteria

1. WHEN the `srl_evpn` subscription delivers bgp-evpn oper-state events, THE Tier_2_Processor SHALL rename the metric to `network_evpn_oper_state`.
2. WHEN the `srl_evpn` subscription delivers bgp-evpn evi events, THE Tier_2_Processor SHALL rename the metric to `network_evpn_evi`.
3. WHEN the `srl_evpn` subscription delivers bgp-evpn ecmp events, THE Tier_2_Processor SHALL rename the metric to `network_evpn_ecmp`.
4. THE Tier_2_Processor SHALL add a `vendor=nokia` label to all SR Linux EVPN metrics.
5. THE Tier_2_Processor SHALL preserve the `source` and `network_instance_name` labels on renamed EVPN metrics.
6. IF an SR Linux EVPN event does not match any mapping in the Mapping_File, THEN THE Tier_2_Processor SHALL pass the event through unchanged.

### Requirement 7: SR Linux Native VXLAN Metric Normalization (Tier 2)

**User Story:** As a network operator, I want SR Linux native VXLAN telemetry metrics normalized to `network_vxlan_*` names inside gNMIc, so that VXLAN tunnel monitoring works with vendor-agnostic metric names.

#### Acceptance Criteria

1. WHEN the `srl_vxlan` subscription delivers vxlan-interface oper-state events, THE Tier_2_Processor SHALL rename the metric to `network_vxlan_oper_state`.
2. WHEN the `srl_vxlan` subscription delivers vxlan-interface index events, THE Tier_2_Processor SHALL rename the metric to `network_vxlan_index`.
3. WHEN the `srl_vxlan` subscription delivers bridge-table statistics events, THE Tier_2_Processor SHALL rename each statistic metric to its corresponding `network_vxlan_bridge_*` Normalized_Metric name.
4. WHEN the `srl_vxlan` subscription delivers multicast-limit events, THE Tier_2_Processor SHALL rename the metric to `network_vxlan_multicast_limit`.
5. THE Tier_2_Processor SHALL add a `vendor=nokia` label to all SR Linux VXLAN metrics.
6. THE Tier_2_Processor SHALL preserve the `source` and `tunnel_interface_name` labels on renamed VXLAN metrics.
7. IF an SR Linux VXLAN event does not match any mapping in the Mapping_File, THEN THE Tier_2_Processor SHALL pass the event through unchanged.

### Requirement 8: Prometheus Relabeling Reduction

**User Story:** As a platform engineer, I want the Prometheus `metric_relabel_configs` reduced to label enrichment only, so that metric name normalization is handled entirely by gNMIc and the Prometheus config is maintainable.

#### Acceptance Criteria

1. THE Prometheus_Relabeling SHALL retain rules that add the `vendor` label to scraped metrics.
2. THE Prometheus_Relabeling SHALL retain rules that derive the `role` label (spine, leaf) from the `source` label.
3. THE Prometheus_Relabeling SHALL retain rules that normalize interface names into the `interface_normalized` label.
4. THE Prometheus_Relabeling SHALL retain rules that set the `topology` and `fabric_type` labels.
5. THE Prometheus_Relabeling SHALL remove all `__name__` regex replacement rules that map `gnmic_*` metric names to `network_*` metric names.
6. WHEN the updated Prometheus configuration is applied, THE Prometheus_Relabeling SHALL contain fewer than 20 relabeling rules total.

### Requirement 9: gNMIc Configuration Integration

**User Story:** As a platform engineer, I want the gNMIc event processors wired into the existing gNMIc configuration, so that normalization is active for all subscriptions without changing subscription paths or intervals.

#### Acceptance Criteria

1. THE Normalization_Engine SHALL be defined in the gNMIc configuration file (`gnmic-config.yml`) or in a file referenced by the gNMIc configuration.
2. THE Normalization_Engine SHALL be applied to the Prometheus output target so that all exported metrics pass through normalization.
3. THE Normalization_Engine SHALL not modify subscription paths, modes, or sample intervals of existing subscriptions.
4. THE Normalization_Engine SHALL process Tier_1_Processor rules before Tier_2_Processor rules when both apply to the same event.
5. IF the Normalization_Engine encounters an event with no matching processor rule, THEN THE Normalization_Engine SHALL export the event with its original metric name.

### Requirement 10: Dashboard Backward Compatibility

**User Story:** As a network operator, I want existing Grafana dashboards to continue working after the normalization migration, so that there is no monitoring downtime during the transition.

#### Acceptance Criteria

1. WHEN the Normalization_Engine is active, THE Normalization_Engine SHALL produce the same set of `network_*` Normalized_Metric names that the previous Prometheus_Relabeling rules produced.
2. WHEN the Normalization_Engine is active, THE Normalization_Engine SHALL preserve all label key-value pairs that existing Grafana dashboard queries depend on (source, interface_name, neighbor_address, network_instance_name).
3. IF a Grafana dashboard query references a `network_*` metric name, THEN THE Normalization_Engine SHALL ensure that metric is available in Prometheus with identical label dimensions.

### Requirement 11: Vendor Extensibility

**User Story:** As a platform engineer, I want the normalization architecture to support adding new vendors without modifying existing processor chains, so that the system scales to multi-vendor environments.

#### Acceptance Criteria

1. THE Normalization_Engine SHALL organize Tier_2_Processor rules by vendor, so that each vendor's native path mappings are isolated in a separate processor chain.
2. WHEN a new vendor is added, THE Normalization_Engine SHALL allow adding a new Tier_2_Processor chain without modifying existing Tier_1_Processor or other vendor Tier_2_Processor configurations.
3. THE Mapping_File SHALL document the expected Normalized_Metric name for each protocol (OSPF, EVPN, VXLAN) independent of vendor, so that new vendor processor chains target the same output names.

### Requirement 12: Mapping File as Source of Truth

**User Story:** As a platform engineer, I want `normalization-mappings.yml` to be the authoritative reference for all path-to-metric-name mappings, so that gNMIc processor configurations and documentation stay in sync.

#### Acceptance Criteria

1. THE Mapping_File SHALL document every OpenConfig path to Normalized_Metric name mapping used by Tier_1_Processor rules.
2. THE Mapping_File SHALL document every vendor-native path to Normalized_Metric name mapping used by Tier_2_Processor rules.
3. WHEN a new metric mapping is added to the Normalization_Engine, THE Mapping_File SHALL be updated to include the new mapping before the processor configuration is deployed.
