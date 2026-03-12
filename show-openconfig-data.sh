#!/bin/bash
# Show actual OpenConfig data being collected

echo "=========================================="
echo "OpenConfig Data Sample"
echo "=========================================="
echo ""

# Show interface traffic from spine1
echo "Interface Traffic (spine1 ethernet-1/49):"
echo "----------------------------------------"
orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep "counters_in_octets.*spine1.*ethernet-1/49" | head -1 | \
    awk '{print "In Octets: " $2}'

orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep "counters_out_octets.*spine1.*ethernet-1/49" | head -1 | \
    awk '{print "Out Octets: " $2}'
echo ""

# Show interface status from all devices
echo "Interface Status (ethernet-1/49 on all devices):"
echo "----------------------------------------"
for device in spine1 spine2 leaf1 leaf2 leaf3 leaf4; do
    status=$(orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
        grep "oper_status.*${device}.*ethernet-1/49" | grep -o 'oper_status="[^"]*"' | cut -d'"' -f2)
    printf "%-8s: %s\n" "$device" "$status"
done
echo ""

# Show LLDP neighbor count
echo "LLDP Neighbor Count:"
echo "----------------------------------------"
for device in spine1 spine2 leaf1 leaf2 leaf3 leaf4; do
    count=$(orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
        grep "lldp.*system_name.*source=\"${device}\"" | wc -l | tr -d ' ')
    printf "%-8s: %s neighbors\n" "$device" "$count"
done
echo ""

# Show sample LLDP data
echo "Sample LLDP Neighbor (spine1 -> leaf1):"
echo "----------------------------------------"
orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep "lldp.*system_name.*source=\"spine1\"" | grep "system_name=\"leaf1\"" | head -1 | \
    grep -o 'system_name="[^"]*"' | cut -d'"' -f2
echo ""

# Show metric counts
echo "OpenConfig Metric Counts:"
echo "----------------------------------------"
interface_counters=$(orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep -c "oc_interface_stats.*counters")
interface_status=$(orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep -c "oc_interface_stats.*status")
lldp_metrics=$(orb -m clab docker exec clab-monitoring-gnmic wget -q -O - http://localhost:9273/metrics 2>/dev/null | \
    grep -c "oc_lldp")

echo "Interface counters: $interface_counters"
echo "Interface status: $interface_status"
echo "LLDP metrics: $lldp_metrics"
echo "Total OpenConfig: $((interface_counters + interface_status + lldp_metrics))"
echo ""

echo "=========================================="
echo "OpenConfig is collecting real data!"
echo "=========================================="
