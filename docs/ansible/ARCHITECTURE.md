# Ansible Multi-Method Architecture

## Overview

This document explains the architecture of the multi-method ansible structure.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Scripts                           │
│                    (deploy-datacenter.sh, etc.)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ansible/site.yml                            │
│                   (Main Entry Point)                             │
│                                                                   │
│  Imports: methods/cli/site.yml (default)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Resources                              │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ inventory.yml│  │ ansible.cfg  │  │ group_vars/  │          │
│  │              │  │              │  │              │          │
│  │ All devices  │  │ Global       │  │ Shared       │          │
│  │ Variables    │  │ settings     │  │ variables    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Methods                         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ CLI Method   │  │ gNMI Method  │  │ REST Method  │          │
│  │ ✅ Ready     │  │ 🚧 Planned   │  │ 💡 Future    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ site.yml     │  │ site.yml     │  │ site.yml     │          │
│  │ playbooks/   │  │ playbooks/   │  │ playbooks/   │          │
│  │ roles/       │  │ roles/       │  │ roles/       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Target Devices                              │
│                                                                   │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ spine1 │  │ spine2 │  │ leaf1  │  │ leaf2  │  │ ...    │   │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Method Architecture

### CLI Method (Implemented)

```
methods/cli/
│
├── site.yml ─────────────────┐
│                              │
├── playbooks/                 │
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml      │
│   └── configure-lldp.yml     │
│                              │
└── roles/                     │
    │                          │
    ├── srlinux_interfaces/ ◄──┤
    │   ├── tasks/             │
    │   │   └── main.yml       │
    │   ├── defaults/          │
    │   └── meta/              │
    │                          │
    ├── srlinux_bgp/ ◄─────────┤
    │   ├── tasks/             │
    │   ├── defaults/          │
    │   └── meta/              │
    │                          │
    └── srlinux_lldp/ ◄────────┘
        ├── tasks/
        ├── defaults/
        └── meta/
```

### gNMI Method (Planned)

```
methods/gnmi/
│
├── site.yml ─────────────────┐
│                              │
├── playbooks/                 │
│   ├── configure-interfaces.yml
│   ├── configure-bgp.yml      │
│   └── configure-lldp.yml     │
│                              │
└── roles/                     │
    │                          │
    ├── gnmi_interfaces/ ◄─────┤
    │   ├── tasks/             │
    │   ├── defaults/          │
    │   └── meta/              │
    │                          │
    ├── gnmi_bgp/ ◄────────────┤
    │   ├── tasks/             │
    │   ├── defaults/          │
    │   └── meta/              │
    │                          │
    └── gnmi_lldp/ ◄───────────┘
        ├── tasks/
        ├── defaults/
        └── meta/
```

## Data Flow

### CLI Method Data Flow

```
User Command
    │
    ▼
ansible-playbook methods/cli/site.yml
    │
    ├─► Read inventory.yml (device list, variables)
    │
    ├─► Read ansible.cfg (roles_path, settings)
    │
    ├─► Load roles from methods/cli/roles/
    │
    ├─► For each device in inventory:
    │   │
    │   ├─► srlinux_interfaces role
    │   │   ├─► Check current state (docker exec sr_cli)
    │   │   ├─► Compare with desired state
    │   │   └─► Apply changes if needed
    │   │
    │   ├─► srlinux_lldp role
    │   │   ├─► Check LLDP state
    │   │   ├─► Compare with desired state
    │   │   └─► Apply changes if needed
    │   │
    │   └─► srlinux_bgp role
    │       ├─► Check BGP state
    │       ├─► Compare with desired state
    │       └─► Apply changes if needed
    │
    └─► Report results (changed/ok/failed)
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                         Inventory                                │
│                                                                   │
│  Defines:                                                        │
│  - Device hostnames                                              │
│  - Management IPs                                                │
│  - Device variables (ASN, router-id, interfaces, etc.)          │
│  - Group variables (spines, leafs)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Roles                                   │
│                                                                   │
│  Use inventory variables to:                                     │
│  - Determine what to configure                                   │
│  - Generate configuration commands                               │
│  - Apply configuration to devices                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Target Devices                              │
│                                                                   │
│  Receive configuration via:                                      │
│  - CLI commands (docker exec sr_cli)                            │
│  - gNMI protocol (future)                                        │
│  - REST API (future)                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Method Selection Flow

```
                    Start
                      │
                      ▼
        ┌─────────────────────────┐
        │ What's your use case?   │
        └─────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   Development   Production    Web Integration
   Learning      Automation
        │             │             │
        ▼             ▼             ▼
   CLI Method    gNMI Method   REST Method
   ✅ Ready      🚧 Planned    💡 Future
        │             │             │
        ▼             ▼             ▼
   Simple &      True           HTTP/JSON
   Reliable      Idempotent     Based
```

## Deployment Patterns

### Pattern 1: Single Method Deployment

```
./redeploy-datacenter.sh
    │
    ├─► Deploy topology (containerlab)
    │
    ├─► Wait for boot
    │
    └─► Configure via CLI method
        ├─► Interfaces
        ├─► LLDP
        └─► BGP
```

### Pattern 2: Method Comparison

```
Deploy with CLI
    │
    ├─► ansible-playbook methods/cli/site.yml
    ├─► ansible-playbook playbooks/verify.yml
    └─► Save results
        │
        ▼
Redeploy topology
        │
        ▼
Deploy with gNMI
    │
    ├─► ansible-playbook methods/gnmi/site.yml
    ├─► ansible-playbook playbooks/verify.yml
    └─► Compare results
```

### Pattern 3: Mixed Method Deployment

```
Deploy topology
    │
    ├─► Use CLI for interfaces (fast to implement)
    │   └─► ansible-playbook methods/cli/playbooks/configure-interfaces.yml
    │
    ├─► Use gNMI for BGP (need idempotency)
    │   └─► ansible-playbook methods/gnmi/playbooks/configure-bgp.yml
    │
    └─► Use CLI for LLDP (simple)
        └─► ansible-playbook methods/cli/playbooks/configure-lldp.yml
```

## Scalability

### Adding New Methods

```
1. Create directory structure
   methods/newmethod/
   ├── site.yml
   ├── playbooks/
   └── roles/

2. Implement roles
   methods/newmethod/roles/
   ├── newmethod_interfaces/
   ├── newmethod_bgp/
   └── newmethod_lldp/

3. Document method
   methods/newmethod/README.md

4. Update shared docs
   - METHODS.md
   - COMPARISON.md
```

### Adding New Features

```
1. Add to inventory
   inventory.yml
   └── Add new variables

2. Implement in each method
   methods/cli/roles/srlinux_newfeature/
   methods/gnmi/roles/gnmi_newfeature/

3. Add to site.yml
   - role: srlinux_newfeature
     tags: [newfeature, config]

4. Create component playbook
   methods/cli/playbooks/configure-newfeature.yml
```

## Benefits of This Architecture

1. **Separation of Concerns**
   - Each method is independent
   - Shared resources are centralized
   - Easy to maintain and update

2. **Flexibility**
   - Choose method per deployment
   - Mix methods if needed
   - Easy to switch between methods

3. **Scalability**
   - Add new methods easily
   - Add new features to all methods
   - Parallel development possible

4. **Testability**
   - Test methods independently
   - Compare method performance
   - Verify method equivalence

5. **Documentation**
   - Each method self-documented
   - Clear comparison available
   - Easy to understand

## Summary

The multi-method architecture provides a flexible, scalable framework for network automation. Each method is self-contained but shares common resources (inventory, variables). This allows easy comparison, testing, and switching between different configuration approaches while maintaining a clean, organized structure.
