"""
Test data generators (strategies) for property-based testing

This module provides hypothesis strategies for generating random valid test data
for topologies, configurations, metrics, and other lab components.
"""

from hypothesis import strategies as st
from typing import Dict, List, Any
import ipaddress


# Vendor-specific metric names for testing normalization
VENDOR_METRIC_NAMES = {
    "srlinux": [
        "/interface/statistics/in-octets",
        "/interface/statistics/out-octets",
        "/interface/statistics/in-packets",
        "/interface/statistics/out-packets",
        "/network-instance/protocols/bgp/neighbor/session-state",
    ],
    "eos": [
        "/interfaces/interface/state/counters/in-octets",
        "/interfaces/interface/state/counters/out-octets",
        "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state",
    ],
    "sonic": [
        "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/in-octets",
        "/sonic-port:sonic-port/PORT/PORT_LIST/state/counters/out-octets",
        "/sonic-bgp:sonic-bgp/BGP_NEIGHBOR/state/session-state",
    ],
    "junos": [
        "/interfaces/interface/state/counters/in-octets",
        "/interfaces/interface/state/counters/out-octets",
        "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state",
    ],
}

# Vendor-specific interface naming conventions
VENDOR_INTERFACE_NAMES = {
    "srlinux": ["ethernet-1/1", "ethernet-1/2", "ethernet-1/10", "ethernet-2/1"],
    "eos": ["Ethernet1/1", "Ethernet1/2", "Ethernet10/1", "Management1"],
    "sonic": ["Ethernet0", "Ethernet4", "Ethernet8", "eth0"],
    "junos": ["ge-0/0/0", "ge-0/0/1", "xe-0/0/0", "em0"],
}


@st.composite
def topologies(draw):
    """
    Generate random valid topology definitions
    
    Returns a dictionary representing a containerlab topology with:
    - Random number of spine devices (1-4)
    - Random number of leaf devices (2-8)
    - Random vendor assignments from supported vendors
    """
    vendors = ["srlinux", "eos", "sonic", "junos"]
    
    num_spines = draw(st.integers(min_value=1, max_value=4))
    num_leafs = draw(st.integers(min_value=2, max_value=8))
    
    # Generate topology name
    name = draw(st.text(
        min_size=3,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-")
    ).filter(lambda x: x[0].isalpha()))
    
    # Generate nodes
    nodes = {}
    
    # Create spine nodes
    for i in range(1, num_spines + 1):
        vendor = draw(st.sampled_from(vendors))
        nodes[f"spine{i}"] = {
            "kind": _vendor_to_kind(vendor),
            "vendor": vendor,
            "role": "spine",
        }
    
    # Create leaf nodes
    for i in range(1, num_leafs + 1):
        vendor = draw(st.sampled_from(vendors))
        nodes[f"leaf{i}"] = {
            "kind": _vendor_to_kind(vendor),
            "vendor": vendor,
            "role": "leaf",
        }
    
    # Generate links (full mesh from spines to leafs)
    links = []
    for spine_idx in range(1, num_spines + 1):
        for leaf_idx in range(1, num_leafs + 1):
            spine_name = f"spine{spine_idx}"
            leaf_name = f"leaf{leaf_idx}"
            spine_vendor = nodes[spine_name]["vendor"]
            leaf_vendor = nodes[leaf_name]["vendor"]
            
            # Use vendor-appropriate interface names
            spine_intf = _get_interface_name(spine_vendor, leaf_idx)
            leaf_intf = _get_interface_name(leaf_vendor, spine_idx + 48)  # Offset for uplinks
            
            links.append({
                "endpoints": [f"{spine_name}:{spine_intf}", f"{leaf_name}:{leaf_intf}"]
            })
    
    return {
        "name": name,
        "topology": {
            "nodes": nodes,
            "links": links,
        }
    }


@st.composite
def bgp_configurations(draw):
    """
    Generate random valid BGP configurations
    
    Returns a dictionary with BGP configuration including:
    - ASN (64512-65535 for private AS range)
    - Router ID (valid IPv4 address)
    - List of BGP neighbors
    """
    asn = draw(st.integers(min_value=64512, max_value=65535))
    
    # Generate router ID as valid IPv4
    router_id = str(draw(st.ip_addresses(v=4)))
    
    # Generate 1-8 neighbors
    num_neighbors = draw(st.integers(min_value=1, max_value=8))
    neighbors = []
    
    for _ in range(num_neighbors):
        neighbor_ip = str(draw(st.ip_addresses(v=4)))
        peer_as = draw(st.integers(min_value=64512, max_value=65535))
        
        neighbors.append({
            "ip": neighbor_ip,
            "peer_as": peer_as,
            "description": draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" -_"))),
            "address_families": draw(st.lists(
                st.sampled_from(["ipv4_unicast", "ipv6_unicast", "evpn"]),
                min_size=1,
                max_size=3,
                unique=True
            ))
        })
    
    return {
        "asn": asn,
        "router_id": router_id,
        "neighbors": neighbors,
    }


@st.composite
def metrics(draw, vendor=None):
    """
    Generate random metrics for testing normalization
    
    Args:
        vendor: Optional vendor name. If None, randomly selected.
    
    Returns a dictionary representing a metric with:
    - Vendor-specific metric name
    - Labels (source, interface, vendor, etc.)
    - Value (float)
    - Timestamp (unix timestamp)
    """
    if vendor is None:
        vendor = draw(st.sampled_from(["srlinux", "eos", "sonic", "junos"]))
    
    metric_name = draw(st.sampled_from(VENDOR_METRIC_NAMES[vendor]))
    interface = draw(st.sampled_from(VENDOR_INTERFACE_NAMES[vendor]))
    
    # Generate device name
    device_name = draw(st.text(
        min_size=3,
        max_size=15,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-")
    ).filter(lambda x: x[0].isalpha()))
    
    return {
        "name": metric_name,
        "labels": {
            "source": device_name,
            "vendor": vendor,
            "interface": interface,
            "role": draw(st.sampled_from(["spine", "leaf", "border"])),
        },
        "value": draw(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)),
        "timestamp": draw(st.integers(min_value=1600000000, max_value=1800000000)),
    }


@st.composite
def configurations(draw):
    """
    Generate random valid device configurations
    
    Returns a dictionary with complete device configuration including:
    - Interfaces
    - BGP
    - OSPF
    - System settings
    """
    vendor = draw(st.sampled_from(["srlinux", "eos", "sonic", "junos"]))
    
    # Generate interfaces
    num_interfaces = draw(st.integers(min_value=1, max_value=8))
    interfaces = []
    
    for i in range(num_interfaces):
        intf_name = _get_interface_name(vendor, i + 1)
        interfaces.append({
            "name": intf_name,
            "description": draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" -_"))),
            "enabled": draw(st.booleans()),
            "ipv4_address": str(draw(st.ip_addresses(v=4))),
            "ipv4_prefix_length": draw(st.integers(min_value=24, max_value=31)),
            "mtu": draw(st.sampled_from([1500, 9000, 9216])),
        })
    
    # Generate BGP config
    bgp_config = draw(bgp_configurations())
    
    # Generate OSPF config
    ospf_config = {
        "process_id": draw(st.integers(min_value=1, max_value=65535)),
        "router_id": str(draw(st.ip_addresses(v=4))),
        "areas": [
            {
                "area_id": "0.0.0.0",
                "interfaces": [intf["name"] for intf in interfaces[:num_interfaces//2]],
            }
        ],
    }
    
    return {
        "vendor": vendor,
        "hostname": draw(st.text(
            min_size=3,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-")
        ).filter(lambda x: x[0].isalpha())),
        "interfaces": interfaces,
        "bgp": bgp_config,
        "ospf": ospf_config,
    }


# Helper functions

def _vendor_to_kind(vendor: str) -> str:
    """Convert vendor name to containerlab kind"""
    kind_map = {
        "srlinux": "nokia_srlinux",
        "eos": "arista_ceos",
        "sonic": "sonic-vs",
        "junos": "juniper_crpd",
    }
    return kind_map.get(vendor, "linux")


def _get_interface_name(vendor: str, index: int) -> str:
    """Generate vendor-appropriate interface name"""
    if vendor == "srlinux":
        return f"ethernet-1/{index}"
    elif vendor == "eos":
        return f"Ethernet{index}/1"
    elif vendor == "sonic":
        return f"Ethernet{(index-1)*4}"
    elif vendor == "junos":
        return f"ge-0/0/{index-1}"
    else:
        return f"eth{index}"
