#!/usr/bin/perl
#
# graphdata.cgi - JSON API for RRD graph data (Collectd Backend)
# This file is part of the IPCop Firewall.
#
# Returns JSON data from Collectd RRD files for use with JavaScript charting libraries.
#
# Query parameters:
#   type   = cpu|memory|disk|diskuse|network|squid-requests|squid-hits
#   iface  = interface name (e.g., GREEN_1, BLUE_1) - required for network
#   period = hour|day|week|month|year (default: day)
#

use strict;
use warnings;
use CGI qw(:standard);
use JSON;
use RRDs;
use File::Glob ':glob';

# Configuration
my $rrdpath = "/var/log/rrd";
my $collectd_host = "localhost";
my $host_dir = "$rrdpath/$collectd_host";

# Get parameters
my $type = param('type') || 'cpu';
my $iface = param('iface') || 'green0';
my $period = param('period') || 'day';

# Period to seconds mapping
my %period_seconds = (
    'hour'  => 3600,
    'day'   => 86400,
    'week'  => 604800,
    'month' => 2592000,
    'year'  => 31536000,
);

my $seconds = $period_seconds{$period} || 86400;

# Output JSON header
print header('application/json');

# Check if Collectd directory exists
unless (-d $host_dir) {
    print encode_json({ error => "Collectd directory not found: $host_dir. Is collectd running?" });
    exit;
}

# Define data structure
my (@ds_labels, %series_map, $value_type, $calculate_percent);

# Load IPCop settings for Interface Mapping
require '/usr/lib/ipcop/general-functions.pl';
my %netsettings;
&General::readhash('/var/ipcop/ethernet/settings', \%netsettings);

# Helper to resolve logical interface (GREEN_1) to physical (eth0)
sub get_physical_iface {
    my $logical = shift;
    
    # Check settings first
    if ($netsettings{"${logical}_DEV"}) {
        return $netsettings{"${logical}_DEV"};
    }
    # Fallback to simple lowercase
    return lc($logical);
}

if ($type eq 'cpu') {
    @ds_labels = ('User CPU', 'System CPU', 'Idle CPU');
    $value_type = 'percent';
    $calculate_percent = 0; # Already percent
    
    # Structure from user: localhost/cpu/percent-user.rrd
    
    my $cpu_dir = "cpu";
    # Collectd might use 'cpu-0' if multiple cores or older version
    if (!-d "$host_dir/cpu" && -d "$host_dir/cpu-0") { $cpu_dir = "cpu-0"; }
    
    # Aggregate specific states into main categories
    # Note: Using array ref for aggregation
    %series_map = (
        'User CPU'   => [
            { file => "$cpu_dir/percent-user.rrd", ds => 'value' },
            { file => "$cpu_dir/percent-nice.rrd", ds => 'value' }
        ],
        'System CPU' => [
            { file => "$cpu_dir/percent-system.rrd", ds => 'value' },
            { file => "$cpu_dir/percent-interrupt.rrd", ds => 'value' },
            { file => "$cpu_dir/percent-softirq.rrd", ds => 'value' },
            { file => "$cpu_dir/percent-steal.rrd", ds => 'value' }
        ],
        'Idle CPU'   => [
            { file => "$cpu_dir/percent-idle.rrd", ds => 'value' },
            { file => "$cpu_dir/percent-wait.rrd", ds => 'value' }
        ]
    );
}
elsif ($type eq 'memory') {
    $value_type = 'percent';
    $calculate_percent = 1; # Enable normalization
    @ds_labels = ('Used', 'Buffered', 'Cached', 'Free');
    
    %series_map = (
        'Used'     => { file => "memory/memory-used.rrd", ds => 'value' },
        'Buffered' => { file => "memory/memory-buffered.rrd", ds => 'value' },
        'Cached'   => { file => "memory/memory-cached.rrd", ds => 'value' },
        'Free'     => { file => "memory/memory-free.rrd", ds => 'value' }
    );
}
elsif ($type eq 'disk') {
    $value_type = 'sectors';
    @ds_labels = ('Read', 'Write');
    
    # Find the main disk (sda, vda, hda)
    my @disk_dirs = bsd_glob("$host_dir/disk-*");
    my $disk_sub = "";
    
    foreach my $d (@disk_dirs) {
        if ($d =~ /\/disk-([a-z]+d[a-z])$/) {
            $disk_sub = "disk-$1";
            last; 
        }
    }
    unless ($disk_sub) {
        if (@disk_dirs) {
             $disk_dirs[0] =~ /\/(disk-.*)$/;
             $disk_sub = $1;
        }
    }
    
    unless ($disk_sub) {
         print encode_json({ 
             type => $type, period => $period, valueType => $value_type,
             timestamps => [], series => {}, labels => \@ds_labels 
         });
         exit;
    }
    
    %series_map = (
        'Read'  => { file => "$disk_sub/disk_ops.rrd", ds => 'read' },
        'Write' => { file => "$disk_sub/disk_ops.rrd", ds => 'write' }
    );
}
elsif ($type eq 'diskuse') {
    $value_type = 'percent';
    $calculate_percent = 0; 
    
    # Check present filesystems
    my $has_varlog = -d "$host_dir/df-var-log";
    
    if ($has_varlog) {
        @ds_labels = ('/ (root)', '/var/log');
        %series_map = (
            '/ (root)' => { 
                used_file => "df-root/df_complex-used.rrd", 
                free_file => "df-root/df_complex-free.rrd",
                ds => 'value'
            },
            '/var/log' => { 
                used_file => "df-var-log/df_complex-used.rrd", 
                free_file => "df-var-log/df_complex-free.rrd",
                ds => 'value'
            }
        );
    } else {
        @ds_labels = ('/ (root)');
        %series_map = (
            '/ (root)' => { 
                used_file => "df-root/df_complex-used.rrd", 
                free_file => "df-root/df_complex-free.rrd",
                ds => 'value'
            }
        );
    }
}
elsif ($type eq 'network') {
    $value_type = 'bits'; 
    @ds_labels = ('Incoming', 'Outgoing');
    
    # 1. Resolve Logical -> Physical (GREEN_1 -> eth0)
    my $phys_iface = get_physical_iface($iface);
    
    # 2. Check existence
    my $target_dir = "";
    if (-d "$host_dir/interface-$phys_iface") {
        $target_dir = "interface-$phys_iface";
    } elsif (-d "$host_dir/interface-" . lc($phys_iface)) {
        $target_dir = "interface-" . lc($phys_iface);
    }
    
    if ($target_dir) {
        %series_map = (
            'Incoming' => { file => "$target_dir/if_octets.rrd", ds => 'rx', factor => 8 },
            'Outgoing' => { file => "$target_dir/if_octets.rrd", ds => 'tx', factor => 8 }
        );
    } else {
        # Interface not found
       # Return empty data
       %series_map = ();
    }
}
elsif ($type eq 'squid-requests') {
    $value_type = 'requests';
    @ds_labels = ('Proxy Requests');
    
    %series_map = (
        'Proxy Requests' => { file => "squid/squid_requests.rrd", ds => 'requests' }
    );
}
elsif ($type eq 'squid-hits') {
    $value_type = 'percent';
    @ds_labels = ('Hit Percentage');
    
    %series_map = (
        'Hit Percentage' => { file => "squid/squid_requests.rrd", ds => 'hits_per' }
    );
}
else {
    print encode_json({ error => "Unknown type: $type" });
    exit;
}

# Fetch data
my $end = time();
my $start = $end - $seconds;
my @timestamps;
my %series_data;  # Final data
my %raw_data;     # Raw fetched data

# Initialize series arrays
for my $label (@ds_labels) { $series_data{$label} = []; }

# FETCH PHASE
my $master_timeline_set = 0;

# Helper to fetch and extract single DS
sub fetch_rrd_data {
    my ($file, $ds_name) = @_;
    my $rrd_file = "$host_dir/$file";
    
    unless (-f $rrd_file) { return undef; }
    
    my ($start_t, $step, $names, $data) = RRDs::fetch($rrd_file, 'AVERAGE', '-s', $start, '-e', $end);
    
    if (RRDs::error) { return undef; }
    
    # Set timeline if first
    unless ($master_timeline_set) {
        my $current = $start_t;
        for (1 .. scalar(@$data)) {
            push @timestamps, $current * 1000;
            $current += $step;
        }
        $master_timeline_set = 1;
    }
    
    # Find DS index
    my $ds_idx = 0;
    if (scalar(@$names) > 1) {
        for my $k (0 .. $#$names) {
            if ($names->[$k] eq $ds_name) {
                $ds_idx = $k;
                last;
            }
        }
    }
    
    my @values;
    foreach my $row (@$data) {
        push @values, $row->[$ds_idx];
    }
    return \@values;
}

# Fetch logic
if ($type eq 'diskuse') {
    # Special handling for diskuse (requires calculation from two files)
    foreach my $label (@ds_labels) {
        my $conf = $series_map{$label};
        my $used_vals = fetch_rrd_data($conf->{used_file}, $conf->{ds});
        my $free_vals = fetch_rrd_data($conf->{free_file}, $conf->{ds});
        
        if ($used_vals && $free_vals) {
            for my $i (0 .. $#$used_vals) {
                my $u = $used_vals->[$i];
                my $f = $free_vals->[$i];
                
                if (defined $u && defined $f && ($u + $f) > 0) {
                    my $pct = ($u / ($u + $f)) * 100;
                    push @{$series_data{$label}}, sprintf("%.2f", $pct) + 0;
                } else {
                    push @{$series_data{$label}}, undef;
                }
            }
        } else {
             # Fill undef
             # Need length ...
             push @{$series_data{$label}}, undef; # Lazy fill
        }
    }
}
else {
    # Standard Handling
    foreach my $label (@ds_labels) {
        my $conf = $series_map{$label};
        
        # Check if conf is array (aggregation) or single hashref
        my @sources = ();
        if (ref($conf) eq 'ARRAY') { @sources = @$conf; }
        else { @sources = ($conf); }
        
        my $aggregated_vals = undef;
        
        foreach my $src (@sources) {
            next unless $src->{file}; # Skip if no file struct
            my $vals = fetch_rrd_data($src->{file}, $src->{ds});
            
            if ($vals) {
                # Initialize aggregate if needed
                if (!$aggregated_vals) {
                    $aggregated_vals = [];
                    # Pre-fill with zeros logic? No, just copy first.
                }
                
                for my $i (0 .. scalar(@$vals)-1) {
                    my $v = $vals->[$i];
                    if (defined $v) {
                         if ($src->{factor}) { $v *= $src->{factor}; }
                         
                         $aggregated_vals->[$i] = 0 unless defined $aggregated_vals->[$i];
                         $aggregated_vals->[$i] += $v;
                    }
                }
            }
        }
        
        $raw_data{$label} = $aggregated_vals;
        
        unless ($calculate_percent) {
            if ($aggregated_vals) {
                for my $v (@$aggregated_vals) {
                    if (defined $v) {
                        $v = sprintf("%.2f", $v) + 0;
                    }
                    push @{$series_data{$label}}, $v;
                }
            } else {
                 # Fill with nulls?
                 # push @{$series_data{$label}}, undef; 
            }
        }
    }
    
    # If percent calculation needed (Memory)
    if ($calculate_percent && $type eq 'memory') {
        # Sum all components to get Total
        # Then divide each by Total
        
        my $count = 0;
        # Determine number of data points
        foreach my $k (keys %raw_data) {
            if ($raw_data{$k}) { $count = scalar(@{$raw_data{$k}}); last; }
        }
        
        for my $i (0 .. $count-1) {
            my $total = 0;
            # 1. Calculate Total
            for my $label (@ds_labels) {
                my $v = $raw_data{$label}->[$i];
                $total += $v if defined $v;
            }
            
            # 2. Calculate Percentages
            for my $label (@ds_labels) {
                my $v = $raw_data{$label}->[$i];
                if (defined $v && $total > 0) {
                    my $pct = ($v / $total) * 100;
                    push @{$series_data{$label}}, sprintf("%.2f", $pct) + 0;
                } else {
                    push @{$series_data{$label}}, undef;
                }
            }
        }
    }
}


my $response = {
    type => $type,
    period => $period,
    valueType => $value_type,
    timestamps => \@timestamps,
    series => \%series_data,
    labels => \@ds_labels,
    interface => ($type eq 'network') ? $iface : undef,
    source => 'collectd'
};

print encode_json($response);

