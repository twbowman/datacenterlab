#!/bin/bash
# Traffic Generation Script
# Generates test traffic between clients to populate link utilization metrics

set -e

echo "🚦 Generating test traffic between clients..."
echo ""

# Check if network lab is running
if ! docker ps | grep -q "clab-gnmi-clos-client1"; then
    echo "❌ Error: Network lab is not running"
    echo "Run: ./lab start"
    exit 1
fi

# Check if clients can reach each other
echo "🔍 Checking client connectivity..."
if docker exec clab-gnmi-clos-client1 ping -c 1 -W 2 10.10.100.2 &>/dev/null; then
    echo "✅ Clients can reach each other via EVPN-VXLAN"
    EVPN_ENABLED=true
else
    echo "⚠️  WARNING: Clients cannot reach each other!"
    echo "EVPN-VXLAN may not be configured properly."
    echo ""
    EVPN_ENABLED=false
fi

# Function to test connectivity and show results
test_connectivity() {
    local src=$1
    local dst=$2
    local dst_ip=$3
    
    if docker exec "clab-gnmi-clos-$src" ping -c 3 -W 2 "$dst_ip" &>/dev/null; then
        echo "  ✅ $src -> $dst ($dst_ip)"
        return 0
    else
        echo "  ❌ $src -> $dst ($dst_ip) - FAILED"
        return 1
    fi
}

# Function to generate traffic between clients
generate_client_traffic() {
    local src_client=$1
    local dst_ip=$2
    local duration=${3:-30}
    local label=${4:-""}
    
    # Use ping with large packets to generate traffic
    docker exec -d "clab-gnmi-clos-$src_client" \
        ping -i 0.01 -s 1400 -c $((duration * 100)) "$dst_ip" &>/dev/null || true
}

# Function to monitor traffic
monitor_traffic() {
    local duration=$1
    local interval=5
    local elapsed=0
    
    echo ""
    echo "⏱️  Monitoring traffic generation..."
    
    while [ $elapsed -lt $duration ]; do
        sleep $interval
        elapsed=$((elapsed + interval))
        
        # Get packet counts from one of the clients
        local tx_packets=$(docker exec clab-gnmi-clos-client1 cat /sys/class/net/eth1/statistics/tx_packets 2>/dev/null || echo "0")
        local rx_packets=$(docker exec clab-gnmi-clos-client1 cat /sys/class/net/eth1/statistics/rx_packets 2>/dev/null || echo "0")
        
        echo "  ⏱️  ${elapsed}s / ${duration}s - client1 TX: $tx_packets pkts, RX: $rx_packets pkts"
    done
}

# Client IP addresses (EVPN-VXLAN subnet)
CLIENT1_IP="10.10.100.1"
CLIENT2_IP="10.10.100.2"
CLIENT3_IP="10.10.100.3"
CLIENT4_IP="10.10.100.4"

DURATION=60  # seconds

if [ "$EVPN_ENABLED" = true ]; then
    echo ""
    echo "🔍 Testing connectivity between all clients..."
    test_connectivity "client1" "client2" "$CLIENT2_IP"
    test_connectivity "client1" "client3" "$CLIENT3_IP"
    test_connectivity "client1" "client4" "$CLIENT4_IP"
    test_connectivity "client2" "client3" "$CLIENT3_IP"
    test_connectivity "client2" "client4" "$CLIENT4_IP"
    test_connectivity "client3" "client4" "$CLIENT4_IP"
    
    echo ""
    echo "🚀 Starting traffic flows..."
    echo "Duration: ${DURATION} seconds"
    echo ""
    echo "Traffic patterns (EVPN-VXLAN):"
    echo "  • client1 <-> client2 (leaf1 <-> leaf2)"
    echo "  • client1 <-> client3 (leaf1 <-> leaf3)"
    echo "  • client1 <-> client4 (leaf1 <-> leaf4)"
    echo "  • client2 <-> client3 (leaf2 <-> leaf3)"
    echo "  • client2 <-> client4 (leaf2 <-> leaf4)"
    echo "  • client3 <-> client4 (leaf3 <-> leaf4)"
    echo ""
    
    # Generate traffic between all client pairs
    generate_client_traffic "client1" "$CLIENT2_IP" "$DURATION" "leaf1->leaf2" &
    generate_client_traffic "client1" "$CLIENT3_IP" "$DURATION" "leaf1->leaf3" &
    generate_client_traffic "client1" "$CLIENT4_IP" "$DURATION" "leaf1->leaf4" &
    generate_client_traffic "client2" "$CLIENT3_IP" "$DURATION" "leaf2->leaf3" &
    generate_client_traffic "client2" "$CLIENT4_IP" "$DURATION" "leaf2->leaf4" &
    generate_client_traffic "client3" "$CLIENT4_IP" "$DURATION" "leaf3->leaf4" &
    
    echo "✅ Traffic generation started"
    
    # Monitor traffic in real-time
    monitor_traffic "$DURATION"
    
    # Wait for all background jobs to complete
    wait
    
    echo ""
    echo "✅ Traffic generation complete"
    echo ""
    echo "📊 Final statistics:"
    
    # Show final packet counts for all clients
    for client in client1 client2 client3 client4; do
        tx=$(docker exec "clab-gnmi-clos-$client" cat /sys/class/net/eth1/statistics/tx_packets 2>/dev/null || echo "0")
        rx=$(docker exec "clab-gnmi-clos-$client" cat /sys/class/net/eth1/statistics/rx_packets 2>/dev/null || echo "0")
        tx_bytes=$(docker exec "clab-gnmi-clos-$client" cat /sys/class/net/eth1/statistics/tx_bytes 2>/dev/null || echo "0")
        rx_bytes=$(docker exec "clab-gnmi-clos-$client" cat /sys/class/net/eth1/statistics/rx_bytes 2>/dev/null || echo "0")
        
        # Convert bytes to MB
        tx_mb=$((tx_bytes / 1024 / 1024))
        rx_mb=$((rx_bytes / 1024 / 1024))
        
        echo "  $client: TX: $tx pkts (${tx_mb}MB), RX: $rx pkts (${rx_mb}MB)"
    done
    
    echo ""
    echo "📊 Metrics should now be available in Prometheus"
    echo "Run: ./lab analyze-links"
    
else
    echo "⚠️  EVPN not working, cannot generate traffic"
    exit 1
fi

