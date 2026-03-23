#!/usr/bin/env python3
"""
Ansible filter plugins for translating interface names between vendor formats
"""

import re


class FilterModule:
    """Interface name translation filters"""

    def filters(self):
        return {
            "to_arista_interface": self.to_arista_interface,
            "to_sonic_interface": self.to_sonic_interface,
            "to_srlinux_interface": self.to_srlinux_interface,
            "to_junos_interface": self.to_junos_interface,
            "normalize_interface": self.normalize_interface,
        }

    def to_arista_interface(self, interface_name):
        """
        Convert generic interface name to Arista EOS format
        ethernet-1/1 -> Ethernet1/1
        eth-1/1 -> Ethernet1/1
        """
        # Handle SR Linux format: ethernet-1/1
        match = re.match(r"ethernet-(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            return f"Ethernet{match.group(1)}/{match.group(2)}"

        # Handle short format: eth-1/1
        match = re.match(r"eth-(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            return f"Ethernet{match.group(1)}/{match.group(2)}"

        # Already in Arista format or unknown
        return interface_name

    def to_sonic_interface(self, interface_name, port_increment=1):
        """
        Convert generic interface name to SONiC format
        ethernet-1/1 -> Ethernet0 (Dell)
        ethernet-1/2 -> Ethernet1 (Dell)

        Note: SONiC naming varies by vendor:
        - Dell: Ethernet0, Ethernet1, Ethernet2... (increment by 1)
        - Mellanox: Ethernet0, Ethernet4, Ethernet8... (increment by 4)
        """
        # Handle SR Linux format: ethernet-1/1
        match = re.match(r"ethernet-(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            module = int(match.group(1))
            port = int(match.group(2))
            # Calculate flat port number (assuming module 1 starts at port 0)
            flat_port = ((module - 1) * 48 + (port - 1)) * port_increment
            return f"Ethernet{flat_port}"

        # Already in SONiC format or unknown
        return interface_name

    def to_srlinux_interface(self, interface_name):
        """
        Convert generic interface name to SR Linux format
        Ethernet1/1 -> ethernet-1/1
        Ethernet0 -> ethernet-1/1 (assuming first module)
        """
        # Handle Arista format: Ethernet1/1
        match = re.match(r"Ethernet(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            return f"ethernet-{match.group(1)}/{match.group(2)}"

        # Handle SONiC flat format: Ethernet0
        match = re.match(r"Ethernet(\d+)", interface_name, re.IGNORECASE)
        if match:
            port_num = int(match.group(1))
            # Assume 48 ports per module
            module = (port_num // 48) + 1
            port = (port_num % 48) + 1
            return f"ethernet-{module}/{port}"

        # Already in SR Linux format or unknown
        return interface_name

    def to_junos_interface(self, interface_name):
        """
        Convert generic interface name to Juniper Junos format
        ethernet-1/1 -> ge-0/0/0
        eth-1/1 -> ge-0/0/0

        Note: Junos uses format ge-fpc/pic/port
        For simplicity, mapping ethernet-X/Y to ge-0/0/Y (single FPC/PIC)
        """
        # Handle SR Linux format: ethernet-1/1
        match = re.match(r"ethernet-(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            port = int(match.group(2)) - 1  # Junos ports are 0-indexed
            return f"ge-0/0/{port}"

        # Handle short format: eth-1/1
        match = re.match(r"eth-(\d+)/(\d+)", interface_name, re.IGNORECASE)
        if match:
            port = int(match.group(2)) - 1  # Junos ports are 0-indexed
            return f"ge-0/0/{port}"

        # Already in Junos format or unknown
        return interface_name

    def normalize_interface(self, interface_name):
        """
        Normalize interface name to a common format (SR Linux style)
        This is useful for comparisons and lookups
        """
        return self.to_srlinux_interface(interface_name)


# Test the filters
if __name__ == "__main__":
    fm = FilterModule()
    filters = fm.filters()

    test_cases = [
        "ethernet-1/1",
        "ethernet-1/2",
        "Ethernet1/1",
        "Ethernet0",
        "Ethernet4",
    ]

    print("Interface Name Translation Tests:")
    print("-" * 60)
    for name in test_cases:
        print(f"Original: {name}")
        print(f"  -> Arista:  {filters['to_arista_interface'](name)}")
        print(f"  -> SONiC:   {filters['to_sonic_interface'](name)}")
        print(f"  -> SR Linux: {filters['to_srlinux_interface'](name)}")
        print(f"  -> Junos:   {filters['to_junos_interface'](name)}")
        print()
