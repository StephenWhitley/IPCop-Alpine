#!/usr/bin/perl
#
# backupapi.cgi - JSON API for backup operations
# This file is part of the IPCop Firewall.
#
# Provides JSON endpoints for:
#   - Listing backup sets
#   - Creating backups
#   - Deleting backups
#   - Triggering restore
#

use strict;
use warnings;
use CGI qw(:standard);
use JSON;
use File::Copy;
use Sys::Hostname;
use Scalar::Util qw(blessed);

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/ipcop_paths.pl';

my $web_root = $IPCop::Paths::IPCOP_WEB_ROOT || '/var/www/ipcop/html';
my $setdir = "$web_root/backup";
my $hostfilter = '[\\w.-]+';

# Get parameters
my %params;
&General::getcgihash(\%params, {'wantfile' => 1, 'filevar' => 'FH'});

my $action = $params{'action'} || 'list';

# Output JSON header
print header('application/json');

# Check if backup key exists
my $cryptkeymissing = system('/usr/bin/ipcopbkcfg', '--keyexist') >> 8;

# Action handlers
if ($action eq 'list') {
    # List all backup sets
    my @backups;
    
    foreach my $set (`/bin/ls -t1 $setdir/*.dat 2>/dev/null`) {
        chomp($set);
        my $hostname = hostname();
        
        # Filter files matching expected format (hostname-timestamp.dat)
        if ($set =~ m!^$setdir/$hostfilter-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.dat$!) {
            my $name = substr($set, length($setdir) + 1);
            my $datetime = '';
            my $description = '';
            
            # Read the .time file for date and description
            if (open(my $fh, '<', "$set.time")) {
                my $line = <$fh>;
                chomp($line) if $line;
                close($fh);
                
                # Format: 2024-01-01_12-30-45 Description here
                if ($line =~ /^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})\s*(.*)$/) {
                    $datetime = "$1 $2:$3:$4";
                    $description = $5 || '';
                }
            }
            
            # Get file size
            my $size = -s $set || 0;
            
            push @backups, {
                filename => $name,
                fullpath => $set,
                datetime => $datetime,
                description => $description,
                size => $size,
                downloadUrl => "/backup/$name"
            };
        }
    }
    
    print encode_json({
        success => JSON::true,
        keyExists => $cryptkeymissing ? JSON::false : JSON::true,
        backups => \@backups
    });
}
elsif ($action eq 'create') {
    # Create a new backup
    if ($cryptkeymissing) {
        print encode_json({ success => JSON::false, error => 'Backup key not found' });
        exit;
    }
    
    my $description = $params{'description'} || '';
    $description =~ s/[^ \w'_-]//g;  # Remove bad characters
    
    if (length($description) > 80) {
        print encode_json({ success => JSON::false, error => 'Description too long (80 char max)' });
        exit;
    }
    
    # Capture both stdout and stderr from ipcopbkcfg
    my $output = `/usr/bin/ipcopbkcfg --write '$description' 2>&1`;
    my $result = $? >> 8;
    
    if ($result == 0) {
        print encode_json({ success => JSON::true, message => 'Backup created successfully' });
    }
    else {
        # Show all output (especially [DEBUG] and ERROR lines)
        my $error_msg = "Backup failed with code $result";
        if ($output) {
            # Clean up but preserve all useful lines
            $output =~ s/^\s+|\s+$//g;  # Trim whitespace
            if ($output) {
                $error_msg = $output;
            }
        }
        print encode_json({ success => JSON::false, error => $error_msg });
    }
}
elsif ($action eq 'delete') {
    # Delete a backup set
    my $filename = $params{'filename'} || '';
    my $fullpath = "$setdir/$filename";
    
    # Validate filename format - allow hostname-YYYY-MM-DD_HH-MM-SS.dat
    if ($fullpath !~ m!^$setdir/[\w.-]+-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.dat$!) {
        print encode_json({ success => JSON::false, error => "Invalid filename: $filename" });
        exit;
    }
    
    if (-e $fullpath) {
        unlink $fullpath;
        unlink "$fullpath.time";
        print encode_json({ success => JSON::true, message => 'Backup deleted' });
    }
    else {
        print encode_json({ success => JSON::false, error => 'Backup not found' });
    }
}
elsif ($action eq 'restore') {
    # Restore from a backup set
    if ($cryptkeymissing) {
        print encode_json({ success => JSON::false, error => 'Backup key not found' });
        exit;
    }
    
    my $filename = $params{'filename'} || '';
    my $fullpath = "$setdir/$filename";
    my $restoreHardware = $params{'restoreHardware'} eq 'true' ? 1 : 0;
    
    # Validate filename format
    if ($fullpath !~ m!^$setdir/$hostfilter-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.dat$!) {
        print encode_json({ success => JSON::false, error => 'Invalid filename' });
        exit;
    }
    
    if (!-e $fullpath) {
        print encode_json({ success => JSON::false, error => 'Backup file not found' });
        exit;
    }
    
    my $result;
    if ($restoreHardware) {
        $result = system('/usr/bin/ipcoprestore', '--restore', $fullpath, '--hardware') >> 8;
    }
    else {
        $result = system('/usr/bin/ipcoprestore', '--restore', $fullpath) >> 8;
    }
    
    if ($result == 0) {
        print encode_json({ 
            success => JSON::true, 
            message => 'Restore completed. Please reboot the system for changes to take effect.',
            requiresReboot => JSON::true
        });
    }
    else {
        my $errorMsg = "Restore failed with code $result";
        if ($result == 6) { $errorMsg = "Decryption failed"; }
        elsif ($result == 7) { $errorMsg = "Archive test failed"; }
        elsif ($result == 8) { $errorMsg = "Extraction failed"; }
        elsif ($result == 12) { $errorMsg = "Version mismatch"; }
        
        print encode_json({ success => JSON::false, error => $errorMsg });
    }
}
elsif ($action eq 'upload') {
    # Upload/import a backup file
    if (blessed($params{'FH'}) ne 'CGI::File::Temp') {
        print encode_json({ success => JSON::false, error => 'No file uploaded' });
        exit;
    }
    
    my $datafile = hostname() . '.dat';
    
    if (!copy($params{'FH'}, "$setdir/$datafile")) {
        print encode_json({ success => JSON::false, error => 'Failed to save uploaded file' });
        exit;
    }
    
    my $result = system('/usr/bin/ipcoprestore', '--import') >> 8;
    
    if ($result == 0) {
        print encode_json({ success => JSON::true, message => 'Backup imported successfully' });
    }
    else {
        print encode_json({ success => JSON::false, error => "Import failed with code $result" });
    }
}
elsif ($action eq 'exportkey') {
    # Export backup key (requires password)
    my $password = $params{'password'} || '';
    
    if (length($password) < 6) {
        print encode_json({ success => JSON::false, error => 'Password must be at least 6 characters' });
        exit;
    }
    
    if ($password =~ m/[\s\"']/) {
        print encode_json({ success => JSON::false, error => 'Password contains invalid characters' });
        exit;
    }
    
    # For key export, we return a download URL instead of JSON
    # The actual download is handled by the original backup.cgi logic
    print encode_json({ 
        success => JSON::true, 
        message => 'Use the download form to export the key'
    });
}
elsif ($action eq 'generatekey') {
    # Generate a new backup key using the setuid helper
    if (!$cryptkeymissing) {
        print encode_json({ success => JSON::false, error => 'Backup key already exists' });
        exit;
    }
    
    # Use the setuid helper to generate the key
    my $result = system('/usr/bin/ipcopbkcfg', '--keygen') >> 8;
    
    if ($result == 0) {
        print encode_json({ success => JSON::true, message => 'Backup key created successfully' });
    }
    else {
        print encode_json({ success => JSON::false, error => 'Failed to generate backup key' });
    }
}
else {
    print encode_json({ success => JSON::false, error => "Unknown action: $action" });
}
