#!/usr/bin/perl
#
# This file is part of the IPCop Firewall.
#
# DO NOT MODIFY ANY CONTENT HERE.
# Use updatemenu.pl to (re)generate this file from the information contained in 
# the CGI files.
#

package Menu;
%Menu::menu = ();

sub buildmenu()
{
    my $menuconfig = shift;

    %{$Menu::menu{"010"}} = (
        'contents'   => $Lang::tr{'alt system'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"020"}} = (
        'contents'   => $Lang::tr{'status'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"030"}} = (
        'contents'   => $Lang::tr{'network'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"040"}} = (
        'contents'   => $Lang::tr{'services'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"050"}} = (
        'contents'   => $Lang::tr{'firewall'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"060"}} = (
        'contents'   => $Lang::tr{'alt vpn'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );
    %{$Menu::menu{"070"}} = (
        'contents'   => $Lang::tr{'alt logs'},
        'uri'        => '',
        'statusText' => '',
        'subMenu'    => []
    );

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ 'Home', '/cgi-bin/index.cgi', 'modern home' ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'scheduler'}, '/cgi-bin/scheduler.cgi', $Lang::tr{'scheduler'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'updates'}, '/cgi-bin/updates.cgi', $Lang::tr{'updates'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'sspasswords'}, '/cgi-bin/changepw.cgi', $Lang::tr{'sspasswords'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'ssh access'}, '/cgi-bin/remote.cgi', $Lang::tr{'ssh access'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'gui settings'}, '/cgi-bin/gui.cgi', $Lang::tr{'gui settings'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'email settings'}, '/cgi-bin/email.cgi', $Lang::tr{'email settings'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ 'BackupJS', '/cgi-bin/backupjs.cgi', 'modern backup' ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'shutdown'}, '/cgi-bin/shutdown.cgi', $Lang::tr{'shutdown'} ]);

    push(@{$Menu::menu{"010"}{'subMenu'}}, [ $Lang::tr{'credits'}, '/cgi-bin/credits.cgi', $Lang::tr{'credits'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ 'System Status', '/cgi-bin/status.cgi', 'System Status' ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ $Lang::tr{'system info'}, '/cgi-bin/sysinfo.cgi', $Lang::tr{'system info'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ $Lang::tr{'ssnetwork status'}, '/cgi-bin/netstatus.cgi', $Lang::tr{'network status information'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ $Lang::tr{'proxy'}, '/cgi-bin/proxystatus.cgi', $Lang::tr{'proxy'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ 'Graphs', '/cgi-bin/graphsjs.cgi', 'interactive graphs' ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ $Lang::tr{'sstraffic'}, '/cgi-bin/traffic.cgi', $Lang::tr{'sstraffic'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ $Lang::tr{'connections'}, '/cgi-bin/connections.cgi', $Lang::tr{'connections'} ]);

    push(@{$Menu::menu{"020"}{'subMenu'}}, [ 'IPtables', '/cgi-bin/iptablesgui.cgi', 'IPTables' ]);

    push(@{$Menu::menu{"030"}{'subMenu'}}, [ $Lang::tr{'alt dialup'}, '/cgi-bin/pppsetup.cgi', $Lang::tr{'dialup settings'} ]);

    push(@{$Menu::menu{"030"}{'subMenu'}}, [ $Lang::tr{'upload'}, '/cgi-bin/upload.cgi', $Lang::tr{'firmware upload'} ]);

    push(@{$Menu::menu{"030"}{'subMenu'}}, [ $Lang::tr{'modem'}, '/cgi-bin/modem.cgi', $Lang::tr{'modem configuration'} ]);

    push(@{$Menu::menu{"030"}{'subMenu'}}, [ $Lang::tr{'aliases'}, '/cgi-bin/aliases.cgi', $Lang::tr{'dialup settings'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'proxy'}, '/cgi-bin/proxy.cgi', $Lang::tr{'web proxy configuration'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'url filter'}, '/cgi-bin/urlfilter.cgi', $Lang::tr{'urlfilter configuration'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'dhcp server'}, '/cgi-bin/dhcp.cgi', $Lang::tr{'dhcp configuration'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'dynamic dns'}, '/cgi-bin/ddns.cgi', $Lang::tr{'dynamic dns client'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'edit hosts'}, '/cgi-bin/hosts.cgi', $Lang::tr{'host configuration'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ 'IDS/IPS', '/cgi-bin/suricata.cgi', 'suricata ids/ips configuration' ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'time server'}, '/cgi-bin/time.cgi', $Lang::tr{'time server'} ]);

    push(@{$Menu::menu{"040"}{'subMenu'}}, [ $Lang::tr{'traffic shaping'}, '/cgi-bin/shaping.cgi', $Lang::tr{'traffic shaping settings'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'firewall settings'}, '/cgi-bin/fwrulesadm.cgi', $Lang::tr{'firewall settings'} ]);

    if ($menuconfig->{'haveBlue'}) {
    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'addressfilter'}, '/cgi-bin/wireless.cgi', $Lang::tr{'addressfilter'} ]);
    }

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'alt services'}, '/cgi-bin/services.cgi', $Lang::tr{'alt services'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'service groups'}, '/cgi-bin/servicegrps.cgi', $Lang::tr{'service groups'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'addresses'}, '/cgi-bin/addresses.cgi', $Lang::tr{'addresses'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'address groups'}, '/cgi-bin/addressgrps.cgi', $Lang::tr{'address groups'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'interfaces'}, '/cgi-bin/ifaces.cgi', $Lang::tr{'interfaces'} ]);

    push(@{$Menu::menu{"050"}{'subMenu'}}, [ $Lang::tr{'firewall rules'}, '/cgi-bin/fwrules.cgi', $Lang::tr{'firewall rules'} ]);

    push(@{$Menu::menu{"060"}{'subMenu'}}, [ 'OpenVPN', '/cgi-bin/openvpn.cgi', $Lang::tr{'virtual private networking'} ]);

    push(@{$Menu::menu{"060"}{'subMenu'}}, [ 'WireGuard', '/cgi-bin/wireguard.cgi', 'WireGuard VPN' ]);

    push(@{$Menu::menu{"060"}{'subMenu'}}, [ 'CA', '/cgi-bin/vpnca.cgi', $Lang::tr{'virtual private networking'} ]);

    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'log settings'}, '/cgi-bin/logconfig.cgi', $Lang::tr{'log settings'} ]);

    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'log summary'}, '/cgi-bin/logsummary.cgi', $Lang::tr{'log summary'} ]);

    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'firewall logs'}, '/cgi-bin/logfirewall.cgi', $Lang::tr{'firewall log viewer'} ]);

    if ($menuconfig->{'haveProxy'}) {
    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'proxy logs'}, '/cgi-bin/logproxy.cgi', $Lang::tr{'proxy log viewer'} ]);
    }

    if ($menuconfig->{'haveProxy'}) {
    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'urlfilter logs'}, '/cgi-bin/logurlfilter.cgi', $Lang::tr{'urlfilter log viewer'} ]);
    }

    push(@{$Menu::menu{"070"}{'subMenu'}}, [ 'IDS/IPS', '/cgi-bin/logsuricata.cgi', 'view suricata alerts' ]);

    push(@{$Menu::menu{"070"}{'subMenu'}}, [ $Lang::tr{'system logs'}, '/cgi-bin/logsystem.cgi', $Lang::tr{'system log viewer'} ]);

}

1;
