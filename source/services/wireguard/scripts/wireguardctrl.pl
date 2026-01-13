#!/usr/bin/perl
#
# IPCop WireGuard Controller
#
# Generates configuration and controls the WireGuard interface
#

use strict;
use warnings;
require '/usr/lib/ipcop/wireguard-functions.pl';

my $action = shift || "help";
my $conf_file = "/etc/wireguard/wg0.conf";

if ($action eq "start") {
    &start();
} elsif ($action eq "stop") {
    &stop();
} elsif ($action eq "restart") {
    &stop();
    &start();
} else {
    print "Usage: $0 {start|stop|restart}\n";
    exit 1;
}

sub generate_config {
    &WireGuard::read_settings();
    my %peers_hash;
    &WireGuard::read_peers(\%peers_hash);

    # Ensure /etc/wireguard exists
    unless (-d "/etc/wireguard") {
        mkdir "/etc/wireguard", 0700;
    }

    open(CONF, ">$conf_file") or die "Could not open $conf_file: $!";
    
    # Interface Section
    print CONF "[Interface]\n";
    
    # Address
    if ($WireGuard::wgsettings{'VPN_IP'} && $WireGuard::wgsettings{'VPN_MASK'}) {
        my $cidr = &cidr_from_mask($WireGuard::wgsettings{'VPN_MASK'});
        print CONF "Address = $WireGuard::wgsettings{'VPN_IP'}/$cidr\n";
    }
    
    # Private Key
    if ($WireGuard::wgsettings{'SERVER_PRIVATE_KEY'}) {
        print CONF "PrivateKey = $WireGuard::wgsettings{'SERVER_PRIVATE_KEY'}\n";
    }
    
    # Listen Port
    if ($WireGuard::wgsettings{'SERVER_PORT'}) {
        print CONF "ListenPort = $WireGuard::wgsettings{'SERVER_PORT'}\n";
    }
    
    # Peers Section
    foreach my $key (sort keys %peers_hash) {
        # Entry format: enabled, name, public_key, allowed_ips, ...
        # Based on how we structure the CGI. Let's assume standard array.
        # [0]=on/off, [1]=Name, [2]=PublicKey, [3]=AllowedIPs
        
        next unless ($peers_hash{$key}[0] eq 'on');
        
        print CONF "\n[Peer]\n";
        print CONF "# $peers_hash{$key}[1]\n";
        print CONF "PublicKey = $peers_hash{$key}[2]\n";
        print CONF "AllowedIPs = $peers_hash{$key}[3]\n";
    }
    
    close(CONF);
    chmod 0600, $conf_file;
}

sub start {
    &WireGuard::read_settings();
    if ($WireGuard::wgsettings{'ENABLED'} ne 'on') {
        print "WireGuard is disabled.\n";
        return;
    }

    print "Starting WireGuard...\n";
    &generate_config();
    
    # Use wg-quick
    system("/usr/bin/wg-quick up wg0 >> /var/log/ipcop/wireguard.log 2>&1");
}

sub stop {
    print "Stopping WireGuard...\n";
    system("/usr/bin/wg-quick down wg0 >> /var/log/ipcop/wireguard.log 2>&1");
}

sub cidr_from_mask {
    my $mask = shift;
    my $bits = 0;
    my @octets = split(/\./, $mask);
    foreach my $octet (@octets) {
        $bits += unpack("%32b*", pack("C", $octet));
    }
    return $bits;
}
