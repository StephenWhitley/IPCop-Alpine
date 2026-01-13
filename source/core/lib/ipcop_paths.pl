#!/usr/bin/perl
#
# Common path definitions for IPCop scripts
# 
package IPCop::Paths;

use strict;
use warnings;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw($IPCOP_WEB_ROOT $IPCOP_CGI_ROOT);

our $IPCOP_WEB_ROOT = "/var/www/ipcop/html";
our $IPCOP_CGI_ROOT = "/var/www/ipcop/cgi-bin";

1;
