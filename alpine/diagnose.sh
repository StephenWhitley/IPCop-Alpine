#!/bin/sh
# IPCop Runtime Diagnostic Script
# Run this on the Alpine VM to verify environment state

echo "=== IPCop Runtime Diagnosis ==="
date
echo "User: $(whoami)"

echo -e "\n--- System Info ---"
uname -a
if [ -f /etc/alpine-release ]; then
    echo "Alpine Version: $(cat /etc/alpine-release)"
fi

echo -e "\n--- Process Status (Key Services) ---"
ps ax | grep -E "lighttpd|openvpn|wireguard|suricata|rsyslog|fcron" | grep -v grep

echo -e "\n--- Service Manager Status ---"
if command -v rc-status >/dev/null; then
    rc-status
else
    echo "OpenRC rc-status not found."
fi

echo -e "\n--- Network Ports (Listening) ---"
netstat -tulnp

echo -e "\n--- Critical File Permissions ---"
ls -ld /var/ipcop
ls -ld /var/log/ipcop
ls -ld /var/log/traffic
ls -ld /var/cache/lighttpd/uploads
ls -l /etc/lighttpd/lighttpd.conf
ls -l /etc/lighttpd/server.pem
ls -l /etc/rsyslog.conf
ls -l /var/ipcop/openvpn/server.conf
ls -l /usr/bin/readhash

echo -e "\n--- Library & Script Check ---"
ls -l /usr/lib/ipcop/
ls -l /usr/bin/wireguardctrl.pl
ls -l /usr/bin/restartopenvpn

echo -e "\n--- Perl Module Availability ---"
for mod in JSON CGI Net::SSLeay Net::DNS Net::IP IO::Socket::SSL DBI DBD::SQLite RRDs; do
    perl -M$mod -e "print \"$mod: INSTALLED\n\"" 2>/dev/null || echo "$mod: MISSING"
done

echo -e "\n--- CGI Syntax Check ---"
# Check syntax of problematic CGIs to catch compile errors (missing libs)
for cgi in /var/www/ipcop/cgi-bin/index.cgi \
           /var/www/ipcop/cgi-bin/interfacestatus.cgi \
           /var/www/ipcop/cgi-bin/openvpn.cgi \
           /var/www/ipcop/cgi-bin/wireguard.cgi \
           /var/www/ipcop/cgi-bin/traffic.cgi; do
    if [ -f "$cgi" ]; then
        echo "Checking $cgi..."
        perl -c "$cgi" 2>&1 | head -n 3
    else
        echo "MISSING: $cgi"
    fi
done

echo -e "\n--- Log Check (Last 10 lines) ---"
if [ -f /var/log/lighttpd/error.log ]; then
    echo ">> lighttpd/error.log"
    tail -n 10 /var/log/lighttpd/error.log
else
    echo ">> lighttpd/error.log NOT FOUND"
fi

if [ -f /var/log/messages ]; then
    echo ">> messages (Errors)"
    grep -i "error" /var/log/messages | tail -n 5
fi

echo -e "\n=== End Diagnosis ==="
