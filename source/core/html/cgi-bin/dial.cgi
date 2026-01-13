#!/usr/bin/perl
#
# SmoothWall CGIs
#
# This code is distributed under the terms of the GPL
#
# (c) The SmoothWall Team
#
# $Id: dial.cgi 4273 2010-02-21 21:38:20Z owes $
#

use strict;

# enable only the following on debugging purpose
#use warnings;
#use CGI::Carp 'fatalsToBrowser';

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

my %cgiparams = ();

$cgiparams{'ACTION'} = '';
&General::getcgihash(\%cgiparams);

if ($cgiparams{'ACTION'} eq $Lang::tr{'dial'}) {
    &General::log('red', 'GUI dial');
    # Redirect output to /dev/null to prevent header corruption
    system('/usr/bin/red --start >/dev/null 2>&1') == 0
        or &General::log("Dial failed: $?");
}
elsif ($cgiparams{'ACTION'} eq $Lang::tr{'hangup'}) {
    &General::log('red', 'GUI hangup');
    # Redirect output to /dev/null to prevent header corruption
    system('/usr/bin/red --stop >/dev/null 2>&1') == 0
        or &General::log("Hangup failed: $?");
}
sleep 1;

print "Status: 302 Moved\nLocation: /cgi-bin/index.cgi\n\n";
