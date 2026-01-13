#!/usr/bin/perl
#
# IPCop CGIs - logsuricata.cgi: View Suricata alerts
#
# IPCop is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# (c) 2026 The IPCop Team
#
# MENUENTRY logs 055 "IDS/IPS" "view suricata alerts"

use strict;

# enable only the following on debugging purpose
#use warnings;
use CGI::Carp 'fatalsToBrowser';

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

my %logsettings=();
my @alerts=();
my$errormessage='';

# Settings
$logsettings{'LOGVIEW_REVERSE'} = 'off';
$logsettings{'FILTER_SOURCE'} = '';
$logsettings{'FILTER_DEST'} = '';
$logsettings{'FILTER_SIGNATURE'} = '';

&General::getcgihash(\\%logsettings);

&Header::showhttpheaders();
&Header::openpage('Suricata Alert Log', 1, '');
&Header::openbigbox('100%', 'left');

# Filter box
&Header::openbox('100%', 'left', 'Log Filters');

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%'>
<tr>
    <td width='25%' class='base'>Source IP Filter:</td>
    <td width='25%'><input type='text' name='FILTER_SOURCE' value='$logsettings{'FILTER_SOURCE'}' size='20' /></td>
    <td width='25%' class='base'>Destination IP Filter:</td>
    <td width='25%'><input type='text' name='FILTER_DEST' value='$logsettings{'FILTER_DEST'}' size='20' /></td>
</tr>
<tr>
    <td class='base'>Signature Filter:</td>
    <td colspan='3'><input type='text' name='FILTER_SIGNATURE' value='$logsettings{'FILTER_SIGNATURE'}' size='60' /></td>
</tr>
<tr>
    <td align='center' colspan='4'>
        <input type='submit' name='ACTION' value='$Lang::tr{'update'}' />
        <input type='submit' name='ACTION' value='$Lang::tr{'export'}' />
    </td>
</tr>
</table>
</form>
END
;

&Header::closebox();

# Read and parse alerts from fast.log
my $logfile = '/var/log/suricata/fast.log';
my @log_lines=();

if (! -e $logfile) {
    &Header::openbox('100%', 'left', 'Alert Log');
    print "<p>No alert log file found. Suricata may not be running or no alerts have been generated yet.</p>\\n";
    &Header::closebox();
    &Header::closebigbox();
    &Header::closepage();
    exit 0;
}

if (open(LOG, $logfile)) {
    @log_lines = reverse <LOG>;
    close(LOG);
}

# Parse alerts
# Suricata fast.log format:
# 01/07/2026-09:00:00.123456  [**] [1:2100498:7] GPL ATTACK_RESPONSE id check returned root [**] [Classification: Potentially Bad Traffic] [Priority: 2] {TCP} 192.168.1.10:54321 -> 8.8.8.8:80

foreach my $line (@log_lines) {
    next if ($line =~ /^\\s*$/);  # Skip empty lines
    
    my %alert = ();
    
    # Parse timestamp
    if ($line =~ /^(\d{2}\/\d{2}\/\d{4}-\d{2}:\d{2}:\d{2}\.\d+)/) {
        $alert{'timestamp'} = $1;
    }
    
    # Parse signature info [gid:sid:rev]
    if ($line =~ /\[\*\*\] \[(\d+):(\d+):(\d+)\] ([^\[]+) \[\*\*\]/) {
        $alert{'gid'} = $1;
        $alert{'sid'} = $2;
        $alert{'rev'} = $3;
        $alert{'signature'} = $4;
        $alert{'signature'} =~ s/^\s+|\s+$//g;  # Trim whitespace
    }
    
    # Parse classification
    if ($line =~ /\[Classification: ([^\]]+)\]/) {
        $alert{'classification'} = $1;
    }
    
    # Parse priority
    if ($line =~ /\[Priority: (\d+)\]/) {
        $alert{'priority'} = $1;
    }
    
    # Parse protocol and IPs
    if ($line =~ /\{(\w+)\} ([\d\.]+):(\d+) -> ([\d\.]+):(\d+)/) {
        $alert{'protocol'} = $1;
        $alert{'src_ip'} = $2;
        $alert{'src_port'} = $3;
        $alert{'dst_ip'} = $4;
        $alert{'dst_port'} = $5;
    }
    
    # Apply filters
    next if ($logsettings{'FILTER_SOURCE'} && $alert{'src_ip'} !~ /$logsettings{'FILTER_SOURCE'}/);
    next if ($logsettings{'FILTER_DEST'} && $alert{'dst_ip'} !~ /$logsettings{'FILTER_DEST'}/);
    next if ($logsettings{'FILTER_SIGNATURE'} && $alert{'signature'} !~ /$logsettings{'FILTER_SIGNATURE'}/i);
    
    push(@alerts, \%alert);
    
    # Limit to most recent 500 alerts
    last if (scalar(@alerts) >= 500);
}

# Export to CSV if requested
if ($logsettings{'ACTION'} eq $Lang::tr{'export'}) {
    print "Content-type: text/csv\n";
    print "Content-Disposition: attachment; filename=suricata_alerts.csv\n\n";
    
    print "Timestamp,Source IP,Source Port,Destination IP,Destination Port,Protocol,Priority,Classification,Signature\n";
    
    foreach my $alert (@alerts) {
        print "\"$alert->{'timestamp'}\",";
        print "\"$alert->{'src_ip'}\",\"$alert->{'src_port'}\",";
        print "\"$alert->{'dst_ip'}\",\"$alert->{'dst_port'}\",";
        print "\"$alert->{'protocol'}\",\"$alert->{'priority'}\",";
        print "\"$alert->{'classification'}\",\"$alert->{'signature'}\"\n";
    }
    
    exit 0;
}

# Display alerts
&Header::openbox('100%', 'left', "Alert Log (Showing " . scalar(@alerts) . " alerts)");

if (scalar(@alerts) == 0) {
    print "<p>No alerts match the current filters.</p>\n";
} else {
    print <<END
<div class='table'><table width='100%'>
<tr>
    <th class='boldbase' width='15%' align='left'>Timestamp</th>
    <th class='boldbase' width='12%' align='left'>Source</th>
    <th class='boldbase' width='12%' align='left'>Destination</th>
    <th class='boldbase' width='8%' align='center'>Protocol</th>
    <th class='boldbase' width='5%' align='center'>Priority</th>
    <th class='boldbase' width='48%' align='left'>Signature</th>
</tr>
END
;
    
    my $lines = 0;
    foreach my $alert (@alerts) {
        my $tid = ($lines % 2) + 1;
        
        # Color code by priority (1=highest, 3=lowest)
        my $priority_color = '';
        if ($alert->{'priority'} == 1) {
            $priority_color = 'style="background-color: #ffcccc;"';  # Red for high priority
        } elsif ($alert->{'priority'} == 2) {
            $priority_color = 'style="background-color: #ffffcc;"';  # Yellow for medium
        }
        
        print "<tr class='table${tid}colour' $priority_color>\n";
        print "<td>$alert->{'timestamp'}</td>\n";
        print "<td>$alert->{'src_ip'}:$alert->{'src_port'}</td>\n";
        print "<td>$alert->{'dst_ip'}:$alert->{'dst_port'}</td>\n";
        print "<td align='center'>$alert->{'protocol'}</td>\n";
        print "<td align='center'>$alert->{'priority'}</td>\n";
        print "<td><small>$alert->{'signature'}</small></td>\n";
        print "</tr>\n";
        
        $lines++;
    }
    
    print "</table></div>\\n";
}

&Header::closebox();

&Header::closebigbox();
&Header::closepage();
