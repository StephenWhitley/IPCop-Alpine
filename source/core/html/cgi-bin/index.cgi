#!/usr/bin/perl
#
# indexjs.cgi - Modern JavaScript home page
# This file is part of the IPCop Firewall.
#
# Modern, card-based home page with real-time interface status.
#
# MENUENTRY system 011 "Home" "modern home"

use strict;
use warnings;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';
require '/usr/lib/ipcop/traffic-lib.pl';

my %mainsettings = ();
my %pppsettings = ();
my %netsettings = ();

&General::readhash('/var/ipcop/main/settings', \%mainsettings);
&General::readhash('/var/ipcop/ppp/settings', \%pppsettings);
&General::readhash('/var/ipcop/ethernet/settings', \%netsettings);

my $connstate = &General::connectionstatus();
my $refresh = '';

# Auto-refresh logic
if ($connstate =~ /$Lang::tr{'dod waiting'}/) {
    $refresh = "<meta http-equiv='refresh' content='30;' />";
} elsif ($connstate =~ /$Lang::tr{'connecting'}|$Lang::tr{'disconnecting'}/) {
    $refresh = "<meta http-equiv='refresh' content='5;' />";
} elsif ($mainsettings{'REFRESHINDEX'} eq 'on') {
    $refresh = "<meta http-equiv='refresh' content='60;' />";
}

&Header::showhttpheaders();
&Header::openpage($Lang::tr{'main page'}, 1, $refresh);
&Header::openbigbox('100%', 'left');

print <<'HTML';
<style>
    .home-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
    }
    .section {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
        border-bottom: 2px solid #4a90d9;
        padding-bottom: 8px;
    }
    
    /* Interface Status Cards */
    .interfaces-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    .interface-card {
        border-radius: 6px;
        padding: 15px;
        border: 2px solid #e0e0e0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .interface-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .interface-card.red { border-color: #dc3545; background: linear-gradient(135deg, #fff 0%, #ffe5e8 100%); }
    .interface-card.green { border-color: #28a745; background: linear-gradient(135deg, #fff 0%, #e8f5ea 100%); }
    .interface-card.blue { border-color: #007bff; background: linear-gradient(135deg, #fff 0%, #e7f1ff 100%); }
    .interface-card.orange { border-color: #fd7e14; background: linear-gradient(135deg, #fff 0%, #fff3e6 100%); }
    
    .interface-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .interface-name {
        font-size: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
    }
    .interface-name .color-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .color-dot.red { background: #dc3545; }
    .color-dot.green { background: #28a745; }
    .color-dot.blue { background: #007bff; }
    .color-dot.orange { background: #fd7e14; }
    
    .interface-status {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 500;
    }
    .interface-status.up {
        background: #28a745;
        color: white;
    }
    .interface-status.down {
        background: #6c757d;
        color: white;
    }
    
    .interface-details {
        font-size: 14px;
        color: #555;
    }
    .interface-details div {
        margin: 5px 0;
    }
    .interface-details strong {
        font-weight: 500;
        color: #333;
    }
    
    /* Connection Controls */
    .connection-buttons {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }
    .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    .btn-success {
        background: #28a745;
        color: white;
    }
    .btn-success:hover {
        background: #218838;
    }
    .btn-danger {
        background: #dc3545;
        color: white;
    }
    .btn-danger:hover {
        background: #c82333;
    }
    .btn-primary {
        background: #4a90d9;
        color: white;
    }
    .btn-primary:hover {
        background: #357abd;
    }
    
    /* System Status */
    .status-text {
        font-size: 16px;
        margin: 10px 0;
        line-height: 1.6;
    }
    .status-text strong {
        color: #333;
    }
    
    .warnings {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        border-radius: 4px;
        margin: 15px 0;
    }
    .warnings ul {
        margin: 0;
        padding-left: 20px;
    }
    .warnings li {
        margin: 5px 0;
        color: #856404;
    }
    
    /* Traffic Stats */
    .traffic-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .traffic-table th,
    .traffic-table td {
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }
    .traffic-table th {
        background: #f8f9fa;
        font-weight: 600;
        color: #333;
    }
    .traffic-table td {
        font-size: 14px;
    }
    
    .loading {
        text-align: center;
        padding: 20px;
        color: #666;
    }
</style>

<div class="home-container">
    <!-- Connection Status Section -->
    <div class="section">
        <div class="section-title">Connection Status</div>
HTML

# Connection status text
my $hostname = &Header::cleanhtml(`/bin/uname -n`, "y");
print "<div class='status-text'>\n";
print "<strong>Hostname:</strong> $hostname<br>\n";

if (($pppsettings{'VALID'} eq 'yes' && $pppsettings{'VALID'} eq 'yes') ||
    (($netsettings{'RED_COUNT'} >= 1) && $netsettings{'RED_1_TYPE'} =~ /^(DHCP|STATIC)$/)) {
    
    print "<strong>Status:</strong> $connstate<br>\n";
    
    if ($connstate =~ /$Lang::tr{'connected'}/) {
        # Display public IP
        my $fetch_ip = &General::GetDyndnsRedIP;
        my $host_name = 'unavailable';
        if (defined($fetch_ip) && $fetch_ip) {
            $host_name = (gethostbyaddr(pack("C4", split(/\./, $fetch_ip)), 2))[0] || $fetch_ip;
           print "<strong>Public IP:</strong> $fetch_ip<br>\n";
            print "<strong>Hostname:</strong> $host_name<br>\n";
        }
        
        # Show real RED IP if different
        if (open(my $fh, '<', "/var/ipcop/red/local-ipaddress")) {
            my $ipaddr = <$fh>;
            close $fh;
            chomp($ipaddr) if $ipaddr;
            if ($ipaddr && $ipaddr ne $fetch_ip) {
                print "<strong>RED IP:</strong> $ipaddr<br>\n";
            }
        }
    }
}

print "</div>\n";

# Connection buttons
if (($pppsettings{'VALID'} eq 'yes') ||
    (($netsettings{'RED_COUNT'} >= 1) && $netsettings{'RED_1_TYPE'} =~ /^(DHCP|STATIC)$/)) {
    print <<'HTML';
        <div class="connection-buttons">
            <form method="post" action="/cgi-bin/dial.cgi" style="display:inline;">
                <button type="submit" name="ACTION" value="Connect" class="btn btn-success">Connect</button>
            </form>
            <form method="post" action="/cgi-bin/dial.cgi" style="display:inline;">
                <button type="submit" name="ACTION" value="Disconnect" class="btn btn-danger">Disconnect</button>
            </form>
            <form method="post" action="/cgi-bin/indexjs.cgi" style="display:inline;">
                <button type="submit" class="btn btn-primary">Refresh</button>
            </form>
        </div>
HTML
}

print "    </div>\n"; # End connection status section

# Interface Status Section
print <<'HTML';
    <!-- Interface Status Section -->
    <div class="section">
        <div class="section-title">Network Interfaces</div>
        <div id="interfaces-container" class="interfaces-grid">
            <div class="loading">Loading interface status...</div>
        </div>
    </div>
HTML

# System Warnings Section
my $warnmessage = '';

# Reboot required
if (-e '/rebootrequired') {
    $warnmessage .= "<li><strong>$Lang::tr{'reboot required'}</strong></li>\n";
}

# Memory usage
my @free = `/usr/bin/free`;
my $mem = 0;
my $used = 0;
foreach my $line (@free) {
    if ($line =~ /^Mem:\s+(\d+)\s+(\d+)/) {
        $mem = $1;
        $used = $2;
        last;
    }
}

if ($mem > 0) {
    # Calculate percentage
    if ($used / $mem > 0.9) {
        my $pct = int(100 * $used / $mem);
        $warnmessage .= "<li>$Lang::tr{'high memory usage'}: $pct%</li>\n";
    }
}

# Disk space
my $free = &General::getavailabledisk('/root');
if ($free < 15) {
    $warnmessage .= "<li>$Lang::tr{'filesystem full'}: /root <strong>$Lang::tr{'free'}=${free}M</strong></li>\n";
}
my $percent = &General::getavailabledisk('/var/log', 'use');
if ($percent > 90) {
    my $freepercent = int(100 - $percent);
    $warnmessage .= "<li>$Lang::tr{'filesystem full'}: /var/log <strong>$Lang::tr{'free'}=${freepercent}%</strong></li>\n";
}

# Patches
my $patchmessage = &General::ispatchavailable();
if ($patchmessage ne "") {
    $warnmessage .= "<li><strong>$patchmessage</strong></li>\n";
}

if ($warnmessage) {
    print "    <div class='section'>\n";
    print "        <div class='section-title'>System Warnings</div>\n";
    print "        <div class='warnings'>\n";
    print "            <ul>$warnmessage</ul>\n";
    print "        </div>\n";
    print "    </div>\n";
}

# Traffic Statistics (if enabled)
if ($TRAFFIC::settings{'SHOW_AT_HOME'} eq 'on') {
    my %calc = ();
    &TRAFFIC::calcTrafficCounts(\%calc);
    
    print <<'HTML';
    <div class="section">
        <div class="section-title">Traffic Statistics</div>
        <table class="traffic-table">
            <tr>
                <th>Period</th>
                <th>Incoming (MB)</th>
                <th>Outgoing (MB)</th>
                <th>Total (MB)</th>
            </tr>
HTML
    
    print "<tr>\n";
    print "    <td>This Week</td>\n";
    print "    <td>$calc{'CALC_WEEK_IN'}</td>\n";
    print "    <td>$calc{'CALC_WEEK_OUT'}</td>\n";
    print "    <td>$calc{'CALC_WEEK_TOTAL'}</td>\n";
    print "</tr>\n";
    
    print "<tr>\n";
    print "    <td>This Month</td>\n";
    print "    <td>$calc{'CALC_VOLUME_IN'}</td>\n";
    print "    <td>$calc{'CALC_VOLUME_OUT'}</td>\n";
    print "    <td>$calc{'CALC_VOLUME_TOTAL'}</td>\n";
    print "</tr>\n";
    
    print "        </table>\n";
    print "    </div>\n";
}

print <<'HTML';
</div>

<script>
async function loadInterfaceStatus() {
    try {
        const response = await fetch('/cgi-bin/interfacestatus.cgi');
        const data = await response.json();
        
        const container = document.getElementById('interfaces-container');
        const interfaces = data.interfaces;
        
        if (Object.keys(interfaces).length === 0) {
            container.innerHTML = '<div class="loading">No interfaces configured</div>';
            return;
        }
        
        let html = '';
        for (const [key, iface] of Object.entries(interfaces)) {
            const statusClass = iface.status === 'up' ? 'up' : 'down';
            const statusText = iface.status.toUpperCase();
            
            html += `
                <div class="interface-card ${iface.color}">
                    <div class="interface-header">
                        <div class="interface-name">
                            <span class="color-dot ${iface.color}"></span>
                            ${iface.color.toUpperCase()}
                        </div>
                        <span class="interface-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="interface-details">
                        <div><strong>Interface:</strong> ${iface.iface}</div>
                        ${iface.ip ? `<div><strong>IP:</strong> ${iface.ip}</div>` : ''}
                        ${iface.type ? `<div><strong>Type:</strong> ${iface.type}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    } catch (e) {
        console.error('Failed to load interface status:', e);
        document.getElementById('interfaces-container').innerHTML = 
            '<div class="loading">Error loading interface status</div>';
    }
}

// Initial load
loadInterfaceStatus();

// Auto-refresh every 30 seconds
setInterval(loadInterfaceStatus, 30000);
</script>
HTML

&Header::closebigbox();
&Header::closepage();
