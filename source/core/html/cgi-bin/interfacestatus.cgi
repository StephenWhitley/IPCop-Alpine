#!/usr/bin/perl
#
# interfacestatus.cgi - JSON API for network interface status
# This file is part of the IPCop Firewall.
#
# Returns JSON with interface status for use by modern home screen.
#

use strict;
use warnings;
use CGI qw(:standard);
use JSON;

require '/usr/lib/ipcop/general-functions.pl';

# Output JSON header
print header('application/json');

my %netsettings;
&General::readhash('/var/ipcop/ethernet/settings', \%netsettings);

my %interfaces;

# Check each color interface
for my $color ('RED', 'GREEN', 'BLUE', 'ORANGE') {
    my $count = $netsettings{"${color}_COUNT"} || 0;
    
    for my $i (1 .. $count) {
        my $key = "${color}_$i";
        my $iface = $netsettings{"${color}_${i}_DEV"} || '';
        
        next unless $iface;
        
        # Determine IP address
        my $ip = '';
        if ($color eq 'RED') {
            # RED interface IP from /var/ipcop/red/local-ipaddress
            if (open(my $fh, '<', '/var/ipcop/red/local-ipaddress')) {
                $ip = <$fh>;
                close($fh);
                chomp($ip) if $ip;
            }
        } else {
            $ip = $netsettings{"${color}_${i}_ADDRESS"} || '';
        }
        
        # Check if interface is up using ip command
        my $status = 'down';
        if (open(my $fh, '-|', "/sbin/ip link show $iface 2>/dev/null")) {
            while (my $line = <$fh>) {
                if ($line =~ /state UP/) {
                    $status = 'up';
                    last;
                }
            }
            close($fh);
        }
        
        $interfaces{$key} = {
            color => lc($color),
            iface => $iface,
            status => $status,
            ip => $ip || undef,
            netmask => $netsettings{"${color}_${i}_NETMASK"} || '',
            type => $netsettings{"${color}_${i}_TYPE"} || ''
        };
    }
}

# Build response
my $response = {
    interfaces => \%interfaces,
    timestamp => time()
};

print encode_json($response);
