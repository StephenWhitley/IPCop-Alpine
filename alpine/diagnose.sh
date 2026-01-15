#!/bin/sh
# IPCop Diagnostic Script
# Run this on the target machine

echo "=== System Info ==="
uname -a
echo ""

echo "=== Network Interfaces ==="
ip addr show
echo ""

echo "=== Routing Table ==="
ip route show
echo ""

echo "=== Service Status ==="
rc-status
echo ""

echo "=== Listening Ports (Netstat) ==="
netstat -tulpn | grep -E '8443|443|80|81'
echo ""

echo "=== Lighttpd Process ==="
ps aux | grep lighttpd
echo ""

echo "=== Firewall Rules (INPUT Chain) ==="
iptables -L INPUT -n -v | head -n 20
echo ""

echo "=== Firewall Rules (Port 8443) ==="
iptables -L -n -v | grep 8443
echo ""

echo "=== Lighttpd Logs (Last 20 lines) ==="
if [ -f /var/log/lighttpd/error.log ]; then
    tail -n 20 /var/log/lighttpd/error.log
else
    echo "Log file not found"
fi
echo ""

echo "=== System Logs (Last 20 lines) ==="
if [ -f /var/log/messages ]; then
    tail -n 20 /var/log/messages
else
    echo "Log file not found"
fi
