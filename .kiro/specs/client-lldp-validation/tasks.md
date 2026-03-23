# Implementation Plan: Client LLDP Validation

## Overview

Add LLDP daemon to client containers and create a gNMI-based validation playbook to verify each leaf switch detects its connected client as an LLDP neighbor on ethernet-1/3. All changes are additive — the existing `validate-lldp.yml` playbook remains untouched.

## Important Context

All containerlab, docker, and ansible commands run via the `./lab` wrapper script on a remote x86_64 Linux server.

## Tasks

- [x] 1. Install and start lldpd on client containers in topology
  - [x] 1.1 Add lldpd exec commands to each client node in topology.yml
    - Prepend `apk add --no-cache lldpd || true` and `lldpd -c -M 1` before existing exec commands on client1, client2, client3, client4
    - `|| true` ensures remaining exec commands (MTU, IP) still run if install fails
    - `-c` flag uses container hostname as LLDP system name, `-M 1` sets management address mode
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 1.2 Write property test for topology exec completeness
    - **Property 1: Topology exec completeness**
    - Parse topology.yml and verify each client node's exec block contains lldpd install (with `|| true`) and daemon start commands
    - **Validates: Requirements 1.1, 1.3, 1.4**

- [x] 2. Define client LLDP neighbor expectations in inventory
  - [x] 2.1 Add client_lldp_neighbor variable to each leaf host in ansible/inventory.yml
    - Add `client_lldp_neighbor: "client1"` to leaf1, `client_lldp_neighbor: "client2"` to leaf2, etc.
    - Only add to leaf hosts, not spine hosts
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.2 Write property test for leaf inventory LLDP neighbor completeness
    - **Property 2: Leaf inventory LLDP neighbor completeness**
    - Parse inventory and verify every host in the leafs group has a non-empty `client_lldp_neighbor` variable
    - **Validates: Requirements 2.1**

  - [ ]* 2.3 Write property test for spine inventory LLDP neighbor exclusion
    - **Property 3: Spine inventory LLDP neighbor exclusion**
    - Parse inventory and verify no host in the spines group has a `client_lldp_neighbor` variable
    - **Validates: Requirements 2.3**

- [x] 3. Checkpoint - Verify topology and inventory changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create client LLDP validation playbook
  - [x] 4.1 Create ansible/playbooks/validate-client-lldp.yml
    - Target the `leafs` host group only
    - Use `gnmi_validate` module with OpenConfig LLDP path `/lldp/interfaces/interface[name=ethernet-1/3]/neighbors/neighbor/state` and `origin: openconfig`
    - Set `check_name: client_lldp_neighbor` and `expected: { system-name: "{{ client_lldp_neighbor }}" }`
    - Include `remediation_hint` about verifying lldpd is running on the client container
    - Use `when: client_lldp_neighbor is defined` to skip hosts without the variable
    - Tag the playbook with `client-lldp` for selective execution
    - Assert `result.status == 'pass'` with failure messages for missing neighbor and system name mismatch
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.2, 5.3_

  - [ ]* 4.2 Write property test for system name comparison correctness
    - **Property 4: System name comparison correctness**
    - Generate random string pairs and verify `semantic_compare({"system-name": expected}, {"system-name": actual})` returns empty diffs iff strings are equal, and non-empty diffs with expected/actual values when they differ
    - **Validates: Requirements 3.2, 3.4**

- [x] 5. Integrate into master validation playbook
  - [x] 5.1 Add import of validate-client-lldp.yml to ansible/playbooks/validate.yml
    - Add `import_playbook: validate-client-lldp.yml` with `tags: [client-lldp]`
    - Append after existing imports so existing playbooks remain untouched
    - _Requirements: 4.1, 4.2, 4.3, 5.1_

- [x] 6. Final checkpoint - Verify end-to-end integration
  - Ensure all tests pass, ask the user if questions arise.
  - Verify validate-client-lldp.yml can run independently via `--tags client-lldp`
  - Verify existing validate-lldp.yml is unmodified
  - Verify scripts/validate-lab.sh picks up the new validation automatically

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- The existing `validate-lldp.yml` and `scripts/validate-lab.sh` require no modifications
