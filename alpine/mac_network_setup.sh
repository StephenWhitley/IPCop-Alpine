#!/bin/bash
# ============================================================================
# IPCop Mac Host Network Configurator
# ============================================================================
# Run this script on your Mac Terminal (NOT on the IPCop VM)
# Usage: sudo ./mac_network_setup.sh
#
# This script helps map VMware Fusion "VNETs" to Mac "Bridge" interfaces
# and assigns the correct IP addresses so you can access the IPCop networks.
#
# COMPATIBILITY: Works with Bash 3.2 (macOS default)
# ============================================================================

CONFIG_FILE="/Library/Preferences/VMware Fusion/networking"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: VMware Fusion networking config not found at:"
    echo "$CONFIG_FILE"
    exit 1
fi

echo "=== Current Bridge Status ==="
echo "Identifying interfaces..."
echo ""

for iface in $(ifconfig | grep "^bridge" | cut -d: -f1); do
    echo "Interface: $iface"
    ifconfig "$iface" | grep "inet " | sed 's/^/  /'
    echo "------------------------------------------------"
done

echo ""
echo "=== Configuration ==="
echo "The configuration file did not contain direct mappings."
echo "Please identify the interface from the list above."
echo " - bridge100/101 are usually standard vmnet1/vmnet8."
echo " - Look for one that has NO IP, or a 192.168.10.x IP."
echo ""
echo "Target: GREEN Network -> 192.168.10.1"
echo ""

# Function to configure interface
configure_net() {
    local name=$1 # e.g. GREEN
    local ip=$2   # e.g. 192.168.10.1
    
    read -p "Enter interface name for $name (e.g. bridge102) [press ENTER to skip]: " iface
    
    if [ -z "$iface" ]; then
        echo "Skipping..."
        return
    fi
    
    echo "-> Configuring $iface to $ip..."
    
    # Configure
    ifconfig "$iface" "$ip" netmask 255.255.255.0 up
    
    if [ $? -eq 0 ]; then
        echo "SUCCESS: $iface set to $ip"
    else
        echo "FAILED: Could not configure $iface"
    fi
}

configure_net "GREEN"  "192.168.10.1"
echo ""
configure_net "ORANGE" "192.168.20.1"
echo ""
configure_net "BLUE"   "192.168.30.1"

echo ""
echo "=== Verification ==="
echo "Try pinging the IPCop interfaces now:"
echo "ping -c 2 192.168.10.254"
echo "ping -c 2 192.168.20.254"
echo "ping -c 2 192.168.30.254"
