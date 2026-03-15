# Requirements Document

## Introduction

This feature enables LLDP (Link Layer Discovery Protocol) on the Linux client containers (client1–client4) in the containerlab topology and extends the existing gNMI-based validation framework to verify that each leaf switch detects its connected client as an LLDP neighbor on the expected interface (ethernet-1/3). Currently, LLDP runs only between SR Linux switches on spine-leaf links. Adding LLDP to clients provides end-to-end link-layer visibility and validates physical connectivity from client to leaf.

## Glossary

- **Client_Container**: A Linux container (nicolaka/netshoot:latest, Alpine-based) representing an end host in the topology. There are four: client1, client2, client3, client4.
- **Leaf_Switch**: An SR Linux network device acting as a top-of-rack switch. There are four: leaf1, leaf2, leaf3, leaf4.
- **LLDP_Daemon**: The `lldpd` process running inside a Client_Container that transmits and receives LLDP frames on the container's eth1 interface.
- **Topology_File**: The `topology.yml` file that defines containerlab nodes, links, and startup exec commands.
- **Validation_Playbook**: An Ansible playbook that uses the gnmi_validate module to query device state via gNMI and assert expected conditions.
- **Client_LLDP_Map**: A data structure in the Ansible inventory that maps each Leaf_Switch's client-facing interface to the expected LLDP neighbor system name.
- **gnmi_validate_Module**: The custom Ansible module (`ansible/library/gnmi_validate.py`) that performs gNMI Get operations and compares actual state against expected state.

## Requirements

### Requirement 1: Install and Start LLDP Daemon on Client Containers

**User Story:** As a network engineer, I want LLDP to run on all client containers at lab startup, so that leaf switches can discover client endpoints via LLDP without manual intervention.

#### Acceptance Criteria

1. WHEN the containerlab topology is deployed, THE Topology_File SHALL include exec commands on each Client_Container that install the `lldpd` package and start the LLDP_Daemon.
2. WHEN the LLDP_Daemon starts on a Client_Container, THE LLDP_Daemon SHALL transmit LLDP frames on the eth1 interface within 30 seconds of container startup.
3. THE Topology_File SHALL configure each Client_Container's LLDP_Daemon with a system name matching the container's hostname (client1, client2, client3, client4).
4. IF the `lldpd` package installation fails on a Client_Container, THEN THE Client_Container SHALL still complete its remaining exec commands (IP address configuration).

### Requirement 2: Define Client-to-Leaf LLDP Neighbor Expectations in Inventory

**User Story:** As a network engineer, I want the expected client LLDP neighbor relationships defined in the Ansible inventory, so that validation can check specific neighbor identities rather than just presence.

#### Acceptance Criteria

1. THE Ansible inventory SHALL define a Client_LLDP_Map for each Leaf_Switch that specifies the expected LLDP neighbor system name on interface ethernet-1/3.
2. THE Client_LLDP_Map for leaf1 SHALL specify "client1" as the expected neighbor on ethernet-1/3. THE Client_LLDP_Map for leaf2 SHALL specify "client2". THE Client_LLDP_Map for leaf3 SHALL specify "client3". THE Client_LLDP_Map for leaf4 SHALL specify "client4".
3. THE Client_LLDP_Map SHALL only be defined on Leaf_Switch hosts, not on spine hosts.

### Requirement 3: Validate Client LLDP Neighbors on Leaf Switches

**User Story:** As a network engineer, I want an Ansible playbook that validates each leaf switch sees its expected client as an LLDP neighbor, so that I can confirm end-to-end physical connectivity from client to leaf.

#### Acceptance Criteria

1. THE Validation_Playbook SHALL query each Leaf_Switch via gNMI for LLDP neighbor state on the client-facing interface (ethernet-1/3).
2. WHEN the gNMI query returns LLDP neighbor data, THE Validation_Playbook SHALL verify that the neighbor's system name matches the expected value from the Client_LLDP_Map.
3. IF a Leaf_Switch has no LLDP neighbor on ethernet-1/3, THEN THE Validation_Playbook SHALL report a failure with a remediation hint indicating that the LLDP_Daemon may not be running on the connected Client_Container.
4. IF the LLDP neighbor system name does not match the expected value, THEN THE Validation_Playbook SHALL report a failure with the expected and actual system names.
5. THE Validation_Playbook SHALL use the existing gnmi_validate_Module for gNMI queries and state comparison.
6. THE Validation_Playbook SHALL target only the leafs host group, not spines.

### Requirement 4: Integrate Client LLDP Validation into Existing Validation Framework

**User Story:** As a network engineer, I want client LLDP validation included in the master validation playbook and validation script, so that it runs as part of the standard lab validation workflow.

#### Acceptance Criteria

1. THE master validation playbook (validate.yml) SHALL import the client LLDP Validation_Playbook with a dedicated tag for selective execution.
2. WHEN the validation script (`scripts/validate-lab.sh`) runs, THE client LLDP validation SHALL execute as part of the configuration validation phase.
3. THE client LLDP Validation_Playbook SHALL be runnable independently using its tag without executing other validation checks.

### Requirement 5: Preserve Existing LLDP Validation for Spine-Leaf Links

**User Story:** As a network engineer, I want the existing spine-leaf LLDP validation to continue working unchanged, so that adding client LLDP validation does not regress existing checks.

#### Acceptance Criteria

1. THE existing validate-lldp.yml playbook SHALL continue to validate LLDP neighbor presence on all network-facing interfaces without modification.
2. THE client LLDP Validation_Playbook SHALL be a separate playbook file from the existing validate-lldp.yml.
3. WHEN both LLDP validation playbooks run, THE results SHALL be independently reportable (separate check names in the validation report).
