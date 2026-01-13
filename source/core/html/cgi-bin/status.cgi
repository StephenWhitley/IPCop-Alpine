#!/usr/bin/perl
#
# SmoothWall CGIs
#
# This code is distributed under the terms of the GPL
#
# (c) The SmoothWall Team
#
# $Id: status.cgi 4825 2010-11-21 17:16:59Z gespinasse $
#
# MENUENTRY status 010 "System Status" "System Status"

use strict;

# enable only the following on debugging purpose
#use warnings;
#use CGI::Carp 'fatalsToBrowser';

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

# These are the processes that we check the status of
# We look for the process name in the output of ps
my %servicenames = (
    $Lang::tr{'cron server'} => 'fcron',
    $Lang::tr{'dhcp server'} => 'dnsmasq',
    $Lang::tr{'dns proxy server'} => 'dnsmasq',
    $Lang::tr{'logging server'} => 'rsyslogd',
    $Lang::tr{'ntp server'} => 'ntpd',
    $Lang::tr{'openvpn server'}  => 'openvpn',
    $Lang::tr{'secure shell server'} => 'sshd',
    'Suricata IDS/IPS' => 'suricata',
    $Lang::tr{'url filter'} => 'e2guardian',
    $Lang::tr{'web proxy'} => 'squid',
    'WireGuard VPN' => 'wg0-interface'
);

&Header::showhttpheaders();

&Header::openpage($Lang::tr{'status information'}, 1, '');

&Header::openbigbox('100%', 'left');

my $araid = '';
$araid = "<a href='#raid'>$Lang::tr{'RAID status'}</a> |" if (-e "/proc/mdstat");

print <<END
<table width='100%' cellspacing='0' cellpadding='5' border='0'>
<tr><td style="background-color: #FFFFFF;" align='left'>
    <a href='#services'>$Lang::tr{'services'}</a> |
    <a href='#memory'>$Lang::tr{'memory'}</a> |
    <a href='#disk'>$Lang::tr{'disk usage'}</a> |
    ${araid}
    <a href='#uptime'>$Lang::tr{'uptime and users'}</a> |
    <a href='#kernel'>$Lang::tr{'kernel version'}</a>
</td></tr>
</table>
END
;

print "<a name='services'/>\n";
&Header::openbox('100%', 'left', "$Lang::tr{'services'}:");

print "<div class='table'><table width='100%'>\n";
print "<tr><th class='boldbase' align='left'><b>$Lang::tr{'services'}</b></th>\n";
print "<th class='boldbase' align='center'><b>$Lang::tr{'memory'}</b></th>\n";
print "<th class='boldbase' align='center'><b>$Lang::tr{'status'}</b></th></tr>\n";

my $lines = 0;
my $key = '';
foreach $key (sort keys %servicenames)
{
    my $tid = ($lines % 2) + 1;
    print "<tr class='table${tid}colour'>\n"; 
    print "<td align='left'>$key</td>\n";
    my $shortname = $servicenames{$key};
    my $status;
    
    # Special handling for WireGuard - check interface not process
    if ($key eq 'WireGuard VPN') {
        # Check if wg0 interface exists with UP flag (state can be UNKNOWN for WireGuard)
        my $wg_check = `ip link show wg0 2>/dev/null | grep -q 'UP' && echo 1 || echo 0`;
        chomp($wg_check);
        if ($wg_check eq '1') {
            print "<td align='center'>-</td>\n";  # Kernel module, no memory stats
            print "<td align='center' class='ipcop_running'>RUNNING</td>\n";
        } else {
            print "<td>&nbsp;</td>\n";
            print "<td align='center' class='ipcop_stopped'>STOPPED</td>\n";
        }
    } else {
        $status = &General::isrunning($shortname);
        print "$status\n";
    }
    print "</tr>\n";
    $lines++;
}


print "</table></div>\n";

&Header::closebox();

print "<a name='memory'/>\n";
&Header::openbox('100%', 'left', "$Lang::tr{'memory'}:");
print "<table>";
my $mem_size=0;
my $mem_used=0;
my $mem_free=0;
my $mem_shared=0;
my $mem_buffers=0;
my $mem_cached=0;
my $buffers_used=0;
my $buffers_free=0;
my $swap_size=0;
my $swap_used=0;
my $swap_free=0;

my $percent=0;

open(FREE,'/usr/bin/free |');
while (<FREE>) {
    if ($_ =~ m/^Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$/) {
        ($mem_size,$mem_used,$mem_free,$mem_shared,$mem_buffers,$mem_cached) = ($1,$2,$3,$4,$5,$6);
    }
    elsif ($_ =~ m/^Swap:\s+(\d+)\s+(\d+)\s+(\d+)$/) {
        ($swap_size,$swap_used,$swap_free) = ($1,$2,$3);
    }
    elsif ($_ =~ m/^-\/\+ buffers\/cache:\s+(\d+)\s+(\d+)$/ ) {
        ($buffers_used,$buffers_free) = ($1,$2);
    }
}
close FREE;

print <<END
<tr>
    <td>&nbsp;</td>
    <td align='center' class='boldbase'>$Lang::tr{'size'}</td>
    <td align='center' class='boldbase'>$Lang::tr{'used'}</td>
    <td align='center' class='boldbase'>$Lang::tr{'free'}</td>
    <td align='left' class='boldbase'>$Lang::tr{'percentage'}</td>
</tr>
END
;

if ($mem_size != 0)
{
    if ($buffers_used != 0)
    {
        my $buffers_kb = int $buffers_used / 1024;
        my $buffers_percent = int 100 * $buffers_used / $mem_size;
        print <<END
<tr>
    <td class='boldbase'>$Lang::tr{'memory'}</td>
    <td align='center'>$buffers_kb MB</td>
    <td>&nbsp;</td>
    <td>&nbsp;</td>
    <td>
END
;
        &Header::percentbar($buffers_percent);
        print <<END
    </td>
</tr>
END
;
    }
    else
    {
        my $mem_kb = int $mem_size / 1024;
        my $mem_usedkb = int $mem_used / 1024;
        my $mem_freekb = int $mem_free / 1024;
        my $mem_percent = int 100 * $mem_used / $mem_size;
        print <<END
<tr>
    <td class='boldbase'>$Lang::tr{'memory'}</td>
    <td align='center'>$mem_kb MB</td>
    <td align='center'>$mem_usedkb MB</td>
    <td align='center'>$mem_freekb MB</td>
    <td>
END
;
        &Header::percentbar($mem_percent);
        print <<END
    </td>
</tr>
END
;
    }
}

if ($swap_size != 0)
{
    my $swap_kb = int $swap_size / 1024;
    my $swap_usedkb = int $swap_used / 1024;
    my $swap_freekb = int $swap_free / 1024;
    my $swap_percent = int 100 * $swap_used / $swap_size;
    print <<END
<tr>
    <td class='boldbase'>$Lang::tr{'swap'}</td>
    <td align='center'>$swap_kb MB</td>
    <td align='center'>$swap_usedkb MB</td>
    <td align='center'>$swap_freekb MB</td>
    <td>
END
;
    &Header::percentbar($swap_percent);
    print <<END
    </td>
</tr>
END
;
}
else
{
    print <<END
<tr>
    <td colspan='5' class='boldbase'>$Lang::tr{'no swap'}</td>
</tr>
END
;
}

print "</table>\n";

&Header::closebox();

print "<a name='disk'/>\n";
&Header::openbox('100%', 'left', "$Lang::tr{'disk usage'}:");

print "<table width='95%'>\n";

open(DF,'/bin/df -B M -x tmpfs -x devtmpfs|');
while(<DF>) {
    my $line = $_;
    $line =~ s/\s+/ /g;
    my @line_arr = split(/\s/, $line);

    if ($line_arr[0] =~ m:^/dev/:) 
    {
        my $percent = $line_arr[4];
        $percent =~ s/%//;
        my $dev = $line_arr[0];
        $dev =~ s:/dev/::;
        print <<END
<tr>
    <td align='left' class='boldbase'>$dev</td>
    <td align='center'>$line_arr[1]</td>
    <td align='center'>$line_arr[2]</td>
    <td align='center'>$line_arr[3]</td>
    <td>
END
;
        &Header::percentbar($percent);
        print <<END
    </td>
</tr>
END
;
    }
}
close DF;

print "</table>\n";
&Header::closebox();

if (-e "/proc/mdstat")
{
    print "<a name='raid'/>\n";
    &Header::openbox('100%', 'left', "$Lang::tr{'RAID status'}:");
    my $output = `/bin/cat /proc/mdstat`;
    $output = &Header::cleanhtml($output,"y");
    print "<pre>$output</pre>\n";
    &Header::closebox();
}

print "<a name='uptime'/>\n";
&Header::openbox('100%', 'left', "$Lang::tr{'uptime and users'}:");
my $uptime = `/usr/bin/uptime`;
$uptime =~ s/\s+/ /g;
print "$uptime\n";
&Header::closebox();

print "<a name='kernel'/>\n";
&Header::openbox('100%', 'left', "$Lang::tr{'kernel version'}:");
my $kernel = `/bin/uname -r`;
print "$kernel\n";
&Header::closebox();

&Header::closebigbox();

&Header::closepage();
