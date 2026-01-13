#!/usr/bin/perl

use strict;
use warnings;
use CGI::Carp 'fatalsToBrowser';

print "Content-type: text/plain\n\n";

print "=== 1. Package Versions (Check r22) ===\n";
print "ipcop-progs: " . (`apk info -v ipcop-progs` || "Not found\n");
print "ipcop-core:  " . (`apk info -v ipcop-core` || "Not found\n");

print "\n=== 2. SUID Permissions (WireGuard Critical) ===\n";
# Should be -rwsr-x--- root:lighttpd
print "wireguardctrl.pl: " . (`ls -la /usr/bin/wireguardctrl.pl` || "MISSING\n");
if (-e "/usr/bin/wireguardctrl.pl") {
    print "  Test Execution (should verify SUID):\n";
    # Try running help command
    print ` /usr/bin/wireguardctrl.pl help 2>&1`;
}

print "\n=== 3. WireGuard System Status ===\n";
print "Module: " . (`lsmod | grep wireguard` || "Module not loaded\n");
print "wg tool: " . (`which wg` || "wg not found\n");
print "wg-quick: " . (`which wg-quick` || "wg-quick not found\n");
print "wg show:\n" . (`wg show 2>&1` || "failed\n");
print "Config file:\n" . (`ls -la /etc/wireguard/wg0.conf 2>&1` || "Missing\n");

print "\n=== 4. Logging System (Syslog) ===\n";
print "Process check:\n";
print `ps aux | grep syslog | grep -v grep`;
print "Log file (/var/log/messages):\n";
print `ls -la /var/log/messages 2>&1`;
print "Tail /var/log/messages (Last 10 lines):\n";
print `tail -n 10 /var/log/messages 2>&1`;

print "\n=== 5. Graphs (Collectd/RRD) ===\n";
print "Process check:\n";
print `ps aux | grep collectd | grep -v grep`;
print "RRD Directory (/var/log/rrd):\n";
print `ls -ld /var/log/rrd 2>&1`;
print "Content (recursive):\n";
print `find /var/log/rrd -ls 2>&1 | head -n 20`; 
print "Collectd Log Check (grep collectd /var/log/messages):\n";
print `grep collectd /var/log/messages | tail -n 5 2>&1`;

print "\n=== 6. Proxy Logs ===\n";
print "Squid access.log:\n";
print `ls -la /var/log/squid/access.log 2>&1`;
print "E2Guardian access.log:\n";
print `ls -la /var/log/e2guardian/access.log 2>&1`;

print "\n=== End of Diagnostic ===\n";
