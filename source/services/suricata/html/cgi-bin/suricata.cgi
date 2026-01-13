#!/usr/bin/perl
#
# IPCop CGIs - suricata.cgi: Suricata IDS/IPS configuration
#
# IPCop is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# (c) 2026 The IPCop Team
#
# MENUENTRY services 055 "IDS/IPS" "suricata ids/ips configuration"
#
# Make sure translation exists $Lang::tr{'IDS/IPS'}

use strict;

# enable only the following on debugging purpose
#use warnings;
use CGI::Carp 'fatalsToBrowser';

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

my %suricatasettings=();
my %netsettings=();
my %checked=();
my %selected=();

my $errormessage='';

# In case suricata is still restarting, show box and refresh
if (! system("/bin/ps ax | /bin/grep -q [r]estartsuricata") ) {
    &Header::page_show($Lang::tr{'intrusion detection'}, 'warning', 'Suricata is restarting...', "<meta http-equiv='refresh' content='5; URL=/cgi-bin/suricata.cgi' />");
    exit(0);
}

&Header::showhttpheaders();

$suricatasettings{'ACTION'} = '';
$suricatasettings{'VALID'} = '';

# Defaults
$suricatasettings{'ENABLED'} = 'off';
$suricatasettings{'MODE'} = 'ids';
$suricatasettings{'MONITOR_GREEN'} = 'off';
$suricatasettings{'MONITOR_BLUE'} = 'off';
$suricatasettings{'MONITOR_RED'} = 'on';
$suricatasettings{'HOME_NET'} = 'auto';
$suricatasettings{'RULE_ACTION'} = 'alert';
$suricatasettings{'UPDATE_RULES'} = 'manual';

# Read existing settings first (before getcgihash overwrites them)
if (-e "/var/ipcop/suricata/settings") {
    &General::readhash("/var/ipcop/suricata/settings", \%suricatasettings);
}

# Read network settings
&General::readhash("/var/ipcop/ethernet/settings", \%netsettings);

# Get CGI parameters (this will overwrite settings with form values)
&General::getcgihash(\%suricatasettings);

if ($suricatasettings{'ACTION'} eq $Lang::tr{'save'}) {
    # Validation
    if ($suricatasettings{'ENABLED'} !~ /^(on|off)$/) {
        $errormessage = $Lang::tr{'invalid input'};
    }
    if ($suricatasettings{'MODE'} !~ /^(ids|ips)$/) {
        $errormessage = $Lang::tr{'invalid input'};
    }
    if (($suricatasettings{'MONITOR_GREEN'} eq 'off') &&
        ($suricatasettings{'MONITOR_BLUE'} eq 'off') &&
        ($suricatasettings{'MONITOR_RED'} eq 'off') &&
        ($suricatasettings{'ENABLED'} eq 'on')) {
        $errormessage = "At least one interface must be monitored when Suricata is enabled";
    }

    if (!$errormessage) {
        $suricatasettings{'VALID'} = 'yes';
        
        # Ensure directory exists before writing settings
        if (! -d "/var/ipcop/suricata") {
            system("mkdir -p /var/ipcop/suricata");
            system("chown root:lighttpd /var/ipcop/suricata");
            system("chmod 2775 /var/ipcop/suricata");
        }
        
        &General::writehash("/var/ipcop/suricata/settings", \%suricatasettings);
        
        # Restart Suricata via SUID helper
        system('/usr/bin/restartsuricata >/dev/null 2>&1 &');
        
        &Header::page_show($Lang::tr{'intrusion detection'}, 'warning', 'Suricata will now restart', "<meta http-equiv='refresh' content='5; URL=/cgi-bin/suricata.cgi' />");
        exit 0;
    }
}

# Setup checkboxes
$checked{'ENABLED'}{'off'} = '';
$checked{'ENABLED'}{'on'} = '';
$checked{'ENABLED'}{$suricatasettings{'ENABLED'}} = "checked='checked'";

$checked{'MONITOR_GREEN'}{'off'} = '';
$checked{'MONITOR_GREEN'}{'on'} = '';
$checked{'MONITOR_GREEN'}{$suricatasettings{'MONITOR_GREEN'}} = "checked='checked'";

$checked{'MONITOR_BLUE'}{'off'} = '';
$checked{'MONITOR_BLUE'}{'on'} = '';
$checked{'MONITOR_BLUE'}{$suricatasettings{'MONITOR_BLUE'}} = "checked='checked'";

$checked{'MONITOR_RED'}{'off'} = '';
$checked{'MONITOR_RED'}{'on'} = '';
$checked{'MONITOR_RED'}{$suricatasettings{'MONITOR_RED'}} = "checked='checked'";

$selected{'MODE'}{'ids'} = '';
$selected{'MODE'}{'ips'} = '';
$selected{'MODE'}{$suricatasettings{'MODE'}} = "selected='selected'";

$selected{'RULE_ACTION'}{'alert'} = '';
$selected{'RULE_ACTION'}{'drop'} = '';
$selected{'RULE_ACTION'}{$suricatasettings{'RULE_ACTION'}} = "selected='selected'";

# Get Suricata status
my $suricata_status = &General::isrunning('suricata');
my $status_text = '';
if ($suricata_status =~ /RUNNING/) {
    $status_text = "<span class='ipcop_running'><b>RUNNING</b></span>";
} else {
    $status_text = "<span class='ipcop_stopped'><b>STOPPED</b></span>";
}

# Check Suricata version
my $suricata_version = '';
if (open(VERSION, '/usr/bin/suricata --build-info 2>&1 |')) {
    while (<VERSION>) {
        if (/Suricata (\\S+)/) {
            $suricata_version = $1;
            last;
        }
    }
    close(VERSION);
}

&Header::openpage($Lang::tr{'intrusion detection'}, 1, '');
&Header::openbigbox('100%', 'left');

# Show error if any
if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error messages'});
    print "<font color='red'><b>$errormessage</b></font>\\n";
    &Header::closebox();
}

# Main configuration box
&Header::openbox('100%', 'left', 'Suricata Configuration');

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%'>
<tr>
    <td width='25%' class='base'>Suricata Status:</td>
    <td width='25%'>$status_text</td>
    <td width='25%' class='base'>Version:</td>
    <td width='25%'>$suricata_version</td>
</tr>
<tr><td colspan='4'><hr /></td></tr>
<tr>
    <td class='base'>Enable Suricata:</td>
    <td colspan='3'>
        <input type='checkbox' name='ENABLED' $checked{'ENABLED'}{'on'} />
    </td>
</tr>
<tr>
    <td class='base'>Operating Mode:</td>
    <td colspan='3'>
        <select name='MODE'>
            <option value='ids' $selected{'MODE'}{'ids'}>IDS (Intrusion Detection - passive monitoring)</option>
            <option value='ips' $selected{'MODE'}{'ips'}>IPS (Intrusion Prevention - active blocking)</option>
        </select>
    </td>
</tr>
<tr><td colspan='4'><hr /></td></tr>
<tr>
    <td class='base'>Monitored Interfaces:</td>
    <td colspan='3'>
END
;

# Show GREEN interface option
if ($netsettings{'GREEN_COUNT'} >= 1) {
    print "<input type='checkbox' name='MONITOR_GREEN' $checked{'MONITOR_GREEN'}{'on'} /> GREEN (LAN)<br />\n";
}

# Show BLUE interface option
if ($netsettings{'BLUE_COUNT'} >= 1) {
    print "<input type='checkbox' name='MONITOR_BLUE' $checked{'MONITOR_BLUE'}{'on'} /> BLUE (DMZ/Guest)<br />\n";
}

# RED always available
print "<input type='checkbox' name='MONITOR_RED' $checked{'MONITOR_RED'}{'on'} /> RED (WAN/Internet)\n";

print <<END
    </td>
</tr>
<tr><td colspan='4'><hr /></td></tr>
</table>

<div style='background-color: #ffffcc; border: 1px solid #cccc00; padding: 10px; margin: 10px 0;'>
<b>Performance Warning:</b><br />
Suricata is a CPU-intensive application. Monitoring multiple interfaces or using IPS mode may significantly impact system performance on lower-end hardware.
In IPS mode, all traffic through monitored interfaces will be inspected, which may introduce latency.
</div>

<div style='background-color: #ffcccc; border: 1px solid #cc0000; padding: 10px; margin: 10px 0;'>
<b>IPS Mode Warning:</b><br />
IPS (Intrusion Prevention) mode will actively block traffic that matches threat signatures.
This may result in false positives blocking legitimate traffic. It is recommended to start with IDS mode and monitor alerts before enabling IPS mode.
</div>

<table width='100%'>
<tr>
    <td width='25%'>&nbsp;</td>
    <td width='25%'>
        <input type='hidden' name='ACTION' value='$Lang::tr{'save'}' />
        <input type='submit' name='SUBMIT' value='$Lang::tr{'save'}' />
    </td>
    <td width='25%'>&nbsp;</td>
    <td width='25%'>&nbsp;</td>
</tr>
</table>
</form>
END
;

&Header::closebox();

# Alert Statistics Box
&Header::openbox('100%', 'left', 'Alert Statistics (Last 24 Hours)');

my $alert_count = 0;
if (-e '/var/log/suricata/fast.log') {
    my $yesterday = time() - 86400;
    if (open(LOG, '/var/log/suricata/fast.log')) {
        while (<LOG>) {
            $alert_count++;
        }
        close(LOG);
    }
}

print <<END
<table width='100%'>
<tr>
    <td width='50%' class='base'>Total Alerts:</td>
    <td width='50%'><b>$alert_count</b></td>
</tr>
<tr>
    <td class='base'>View Alerts:</td>
    <td><a href='/cgi-bin/logsuricata.cgi'>Suricata Alert Log</a></td>
</tr>
</table>
END
;

&Header::closebox();

# Rules Information Box
&Header::openbox('100%', 'left', 'Suricata Rules');

my $rule_count = 0;
if (-e '/var/lib/suricata/rules/suricata.rules') {
    if (open(RULES, '/var/lib/suricata/rules/suricata.rules')) {
        while (<RULES>) {
            next if /^\\s*#/;
            next if /^\\s*$/;
            $rule_count++;
        }
        close(RULES);
    }
}

print <<END
<table width='100%'>
<tr>
    <td width='50%' class='base'>Active Rules:</td>
    <td width='50%'><b>$rule_count</b></td>
</tr>
<tr>
    <td class='base'>Ruleset:</td>
    <td>Emerging Threats Open</td>
</tr>
<tr>
    <td class='base'>Rule Updates:</td>
    <td>
        Manual updates only<br />
        <small>(Automatic updates can be configured via cron)</small>
    </td>
</tr>
</table>
END
;

&Header::closebox();

&Header::closebigbox();
&Header::closepage();
