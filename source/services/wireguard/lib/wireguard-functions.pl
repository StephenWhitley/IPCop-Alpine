#!/usr/bin/perl
#
# This file is part of the IPCop Firewall.
#
# IPCop is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

package WireGuard;

use strict;
use warnings;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';

our %wgsettings = ();
our %wgpeers = ();

# Constants
our $wg_config_dir = "/var/ipcop/wireguard";
our $wg_settings_file = "$wg_config_dir/settings";
our $wg_peers_file = "$wg_config_dir/peers";

# Initialise
if (! -d $wg_config_dir) {
    mkdir $wg_config_dir, 0770;
    chown((getpwnam('root'))[0], (getgrnam('lighttpd'))[0], $wg_config_dir) if ($> == 0);
}

sub read_settings {
    if (-f $wg_settings_file) {
        &General::readhash($wg_settings_file, \%wgsettings);
    } else {
        # Defaults
        $wgsettings{'SERVER_PORT'} = '51820';
        $wgsettings{'VPN_IP'} = '10.200.0.1';
        $wgsettings{'VPN_MASK'} = '255.255.255.0';
    }
}

sub write_settings {
    &General::writehash($wg_settings_file, \%wgsettings);
}

sub read_peers {
    my $peers_ref = shift;
    if (-f $wg_peers_file) {
        &General::readhasharray($wg_peers_file, $peers_ref);
    }
}

sub write_peers {
    my $peers_ref = shift;
    &General::writehasharray($wg_peers_file, $peers_ref);
}

sub generate_private_key {
    my $key = `wg genkey`;
    chomp($key);
    return $key;
}

sub generate_public_key {
    my $private_key = shift;
    return "" unless $private_key;
    
    # Needs to pipe into wg pubkey
    open(my $fh, "-|", "echo '$private_key' | wg pubkey") or return "";
    my $public_key = <$fh>;
    close($fh);
    chomp($public_key);
    return $public_key;
}

sub is_running {
    my $output = `ip link show wg0 2>&1`;
    if ($? == 0 && $output !~ /does not exist/) {
        return 1;
    }
    return 0;
}

sub get_status {
    # Check if wg0 interface exists and has UP flag (state can be UNKNOWN)
    my $check = `ip link show wg0 2>/dev/null | grep -q 'UP' && echo 1 || echo 0`;
    chomp($check);
    return ($check eq '1') ? 'running' : 'stopped';
}

1;
