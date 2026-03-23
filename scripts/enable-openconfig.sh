#!/bin/bash
# Enable OpenConfig on all SR Linux devices

set -e

DEVICES="spine1 spine2 leaf1 leaf2 leaf3 leaf4"

echo "Enabling OpenConfig on all SR Linux devices..."

for device in $DEVICES; do
    echo "Updating $device config..."
    
    # Update config file
    cat > "configs/$device/srlinux/config.json" << 'EOF'
{
  "system": {
    "name": {
      "host-name": "DEVICE_NAME"
    },
    "gnmi-server": {
      "admin-state": "enable",
      "network-instance": [
        {
          "name": "mgmt"
        }
      ]
    },
    "management": {
      "openconfig": {
        "admin-state": "enable"
      }
    }
  }
}
EOF
    
    # Replace device name
    sed -i.bak "s/DEVICE_NAME/$device/" "configs/$device/srlinux/config.json"
    rm "configs/$device/srlinux/config.json.bak"
    
    echo "✓ $device config updated"
done

echo ""
echo "OpenConfig enabled in all device configs"
echo ""
echo "To apply changes, restart the lab:"
echo "  orb -m clab sudo containerlab destroy -t topology-srlinux.yml"
echo "  orb -m clab sudo containerlab deploy -t topology-srlinux.yml"
echo ""
echo "Or reload configs on running devices:"
for device in $DEVICES; do
    echo "  orb -m clab docker exec clab-gnmi-clos-$device sr_cli 'tools system configuration load factory'"
done
