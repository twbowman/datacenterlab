#!/bin/bash
# Configure OpenConfig on all SR Linux devices via CLI

set -e

DEVICES="spine1 spine2 leaf1 leaf2 leaf3 leaf4"

echo "Configuring OpenConfig on all SR Linux devices..."
echo ""

for device in $DEVICES; do
    echo "Configuring $device..."
    
    # Create config directly in container
    orb -m clab docker exec clab-gnmi-clos-$device bash -c "cat > /tmp/oc-config.txt << 'EOF'
enter candidate
system lldp admin-state enable
system management openconfig admin-state enable
system grpc-server mgmt yang-models openconfig
commit stay
quit
EOF"
    
    # Execute the script
    orb -m clab docker exec clab-gnmi-clos-$device sr_cli -c "source /tmp/oc-config.txt" 2>&1 | grep -E "commit|error|Error" || echo "  Done"
    
    echo "✓ $device configured"
done

echo ""
echo "OpenConfig configuration complete!"
echo ""
echo "Verifying configuration on spine1..."
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli "info from state /system management openconfig"
orb -m clab docker exec clab-gnmi-clos-spine1 sr_cli "info from state /system grpc-server mgmt yang-models"
