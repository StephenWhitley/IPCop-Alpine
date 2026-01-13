#!/usr/bin/perl
#
# IPCop WireGuard WebUI
#
# MENUENTRY vpn 020 "WireGuard" "WireGuard VPN"
#

use strict;
use warnings;
use CGI::Carp 'fatalsToBrowser';

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';
require '/usr/lib/ipcop/wireguard-functions.pl';

our %cgiparams = ();
our %wgsettings = ();
our %wgpeers = ();
my $errormessage = '';
my $warnmessage = '';

# Get CGI params
&General::getcgihash(\%cgiparams);

# Read Settings
&WireGuard::read_settings();
&WireGuard::read_peers(\%wgpeers);

# Action Processing
if ($cgiparams{'ACTION'} eq 'Start') {
    system('/usr/bin/wireguardctrl.pl start >/dev/null 2>&1');
}
elsif ($cgiparams{'ACTION'} eq 'Restart') {
    system('/usr/bin/wireguardctrl.pl restart >/dev/null 2>&1');
}
elsif ($cgiparams{'ACTION'} eq 'Stop') {
    system('/usr/bin/wireguardctrl.pl stop >/dev/null 2>&1');
}
elsif ($cgiparams{'ACTION'} eq $Lang::tr{'save'}) {
    
    # Save Global Settings
    $WireGuard::wgsettings{'ENABLED'} = $cgiparams{'ENABLED'};
    $WireGuard::wgsettings{'SERVER_PORT'} = $cgiparams{'SERVER_PORT'};
    
    # Validate IP/Mask
    if (&General::validipandmask($cgiparams{'VPN_IP'} . "/" . $cgiparams{'VPN_MASK'})) {
        $WireGuard::wgsettings{'VPN_IP'} = $cgiparams{'VPN_IP'};
        $WireGuard::wgsettings{'VPN_MASK'} = $cgiparams{'VPN_MASK'};
    } else {
        $errormessage = "Invalid VPN IP/Mask";
    }
    
    # Generate Keys if requested (or empty)
    if ($cgiparams{'GENERATE_KEYS'} eq 'on' || !$WireGuard::wgsettings{'SERVER_PRIVATE_KEY'}) {
        my $priv = &WireGuard::generate_private_key();
        if ($priv) {
            $WireGuard::wgsettings{'SERVER_PRIVATE_KEY'} = $priv;
            $WireGuard::wgsettings{'SERVER_PUBLIC_KEY'} = &WireGuard::generate_public_key($priv);
        } else {
            $errormessage = "Could not generate keys";
        }
    }

    if (!$errormessage) {
        &WireGuard::write_settings();
        
        # Apply changes (redirect output to avoid polluting HTTP response)
        if ($WireGuard::wgsettings{'ENABLED'} eq 'on') {
            system('/usr/bin/wireguardctrl.pl restart >/dev/null 2>&1');
        } else {
            system('/usr/bin/wireguardctrl.pl stop >/dev/null 2>&1');
        }
    }
}
elsif ($cgiparams{'ACTION'} eq 'Add Peer') {
    # Basic Add Peer logic (simplified for initial version)
    my $key = &General::findhasharraykey(\%wgpeers);
    $wgpeers{$key} = ['off', $cgiparams{'PEER_NAME'}, $cgiparams{'PEER_PUBKEY'}, $cgiparams{'PEER_ALLOWEDIPS'}];
    &WireGuard::write_peers(\%wgpeers);
    
    if ($WireGuard::wgsettings{'ENABLED'} eq 'on') {
        system('/usr/bin/wireguardctrl.pl restart >/dev/null 2>&1');
    }
}
elsif ($cgiparams{'ACTION'} eq 'Delete') {
    delete $wgpeers{$cgiparams{'KEY'}};
    &WireGuard::write_peers(\%wgpeers);
    if ($WireGuard::wgsettings{'ENABLED'} eq 'on') {
        system('/usr/bin/wireguardctrl.pl restart >/dev/null 2>&1');
    }
}
elsif ($cgiparams{'ACTION'} eq 'Toggle') {
     if ($wgpeers{$cgiparams{'KEY'}}[0] eq 'on') {
         $wgpeers{$cgiparams{'KEY'}}[0] = 'off';
     } else {
         $wgpeers{$cgiparams{'KEY'}}[0] = 'on';
     }
     &WireGuard::write_peers(\%wgpeers);
     if ($WireGuard::wgsettings{'ENABLED'} eq 'on') {
        system('/usr/bin/wireguardctrl.pl restart >/dev/null 2>&1');
    }
}

# Defaults
$cgiparams{'ENABLED'} = $WireGuard::wgsettings{'ENABLED'} || 'off';
$cgiparams{'VPN_IP'} = $WireGuard::wgsettings{'VPN_IP'} || '10.200.0.1';
$cgiparams{'VPN_MASK'} = $WireGuard::wgsettings{'VPN_MASK'} || '255.255.255.0';
$cgiparams{'SERVER_PORT'} = $WireGuard::wgsettings{'SERVER_PORT'} || '51820';

# Page Start
&Header::showhttpheaders();
&Header::openpage('WireGuard', 1, '');
&Header::openbigbox('100%', 'left');

if ($errormessage) {
    &Header::openbox('100%', 'left', $Lang::tr{'error'});
    print "<font color='red'>$errormessage</font>";
    &Header::closebox();
}

# Status Display and Control
my $status = &WireGuard::get_status();
my $status_color = ($status eq 'running') ? 'green' : 'red';
my $status_text = ($status eq 'running') ? 'Running' : 'Stopped';

&Header::openbox('100%', 'left', "WireGuard Status");
print <<END;
<table width='100%'>
<tr>
    <td width='25%'>Status:</td>
    <td width='75%'><font color='$status_color'><b>$status_text</b></font></td>
</tr>
<tr>
    <td></td>
    <td>
        <form method='post' action='$ENV{'SCRIPT_NAME'}' style='display:inline;'>
            <input type='submit' name='ACTION' value='Start' />
        </form>
        <form method='post' action='$ENV{'SCRIPT_NAME'}' style='display:inline;'>
            <input type='submit' name='ACTION' value='Restart' />
        </form>
        <form method='post' action='$ENV{'SCRIPT_NAME'}' style='display:inline;'>
            <input type='submit' name='ACTION' value='Stop' />
        </form>
    </td>
</tr>
</table>
END
&Header::closebox();

# Config Form
&Header::openbox('100%', 'left', "WireGuard Server Settings");
print <<END;
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%'>
<tr>
    <td width='25%'>Enabled:</td>
    <td width='25%'><input type='checkbox' name='ENABLED' value='on' @{[$cgiparams{'ENABLED'} eq 'on' ? 'checked' : '']} /></td>
    <td width='50%'>&nbsp;</td>
</tr>
<tr>
    <td>VPN IP Address:</td>
    <td><input type='text' name='VPN_IP' value='$cgiparams{'VPN_IP'}' /></td>
    <td>Mask: <input type='text' name='VPN_MASK' value='$cgiparams{'VPN_MASK'}' /></td>
</tr>
<tr>
    <td>Listen Port:</td>
    <td><input type='text' name='SERVER_PORT' value='$cgiparams{'SERVER_PORT'}' /></td>
    <td>&nbsp;</td>
</tr>
<tr>
    <td>Public Key:</td>
    <td colspan='2'><b>$WireGuard::wgsettings{'SERVER_PUBLIC_KEY'}</b></td>
</tr>
<tr>
    <td>Regenerate Keys:</td>
    <td><input type='checkbox' name='GENERATE_KEYS' value='on' /></td>
    <td><font size='1'>(Warning: Replaces existing keys!)</font></td>
</tr>
</table>
<hr />
<input type='submit' name='ACTION' value='$Lang::tr{'save'}' />
</form>
END
&Header::closebox();

# Peers List
&Header::openbox('100%', 'left', "WireGuard Peers");
print <<END;
<table width='100%' class='table'>
<tr>
    <th width='5%'>Active</th>
    <th width='20%'>Name</th>
    <th width='40%'>Public Key</th>
    <th width='25%'>Allowed IPs</th>
    <th width='10%'>Action</th>
</tr>
END

foreach my $key (sort keys %wgpeers) {
    my $col = ($wgpeers{$key}[0] eq 'on') ? 'bgcolor="#d4ffce"' : '';
    my $gif = ($wgpeers{$key}[0] eq 'on') ? 'on.gif' : 'off.gif';
    my $gdesc = ($wgpeers{$key}[0] eq 'on') ? $Lang::tr{'click to disable'} : $Lang::tr{'click to enable'};
    print <<END;
<tr $col>
    <td align='center'>
        <form method='post' action='$ENV{'SCRIPT_NAME'}'>
        <input type='hidden' name='KEY' value='$key' />
        <input type='image' name='$Lang::tr{'toggle enable disable'}' src='/images/$gif' alt='$gdesc' title='$gdesc' />
        <input type='hidden' name='ACTION' value='Toggle' />
        </form>
    </td>
    <td>$wgpeers{$key}[1]</td>
    <td><font size='1'>$wgpeers{$key}[2]</font></td>
    <td>$wgpeers{$key}[3]</td>
    <td align='center'>
        <form method='post' action='$ENV{'SCRIPT_NAME'}'>
        <input type='hidden' name='KEY' value='$key' />
        <input type='image' name='ACTION' value='Delete' src='/images/delete.png' />
        </form>
    </td>
</tr>
END
}

print "</table>";

# Add Peer Form
print <<END;
<hr />
<h3>Add New Peer</h3>
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table>
<tr><td>Name:</td><td><input type='text' name='PEER_NAME' /></td></tr>
<tr><td>Public Key:</td><td><input type='text' name='PEER_PUBKEY' size='40' /></td></tr>
<tr><td>Allowed IPs:</td><td><input type='text' name='PEER_ALLOWEDIPS' /></td></tr>
<tr><td colspan='2'><input type='submit' name='ACTION' value='Add Peer' /></td></tr>
</table>
</form>
END

&Header::closebox();
&Header::closebigbox();
&Header::closepage();
