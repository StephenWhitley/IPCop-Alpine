#!/usr/bin/perl
#
# graphsjs.cgi - Interactive JavaScript graphs using Chart.js
# This file is part of the IPCop Firewall.
#
# Alternative to RRDtool PNG graphs with modern, interactive charts.
#
# MENUENTRY status 045 "Graphs" "interactive graphs"

use strict;
use warnings;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

my %netsettings;
&General::readhash('/var/ipcop/ethernet/settings', \%netsettings);

# Check if proxy is enabled
my %proxysettings;
my $proxy_enabled = 0;
if (-e '/var/ipcop/proxy/settings') {
    &General::readhash('/var/ipcop/proxy/settings', \%proxysettings);
    $proxy_enabled = (exists $proxysettings{'ENABLED_GREEN_1'} && $proxysettings{'ENABLED_GREEN_1'} eq 'on') ||
                     (exists $proxysettings{'ENABLED_BLUE_1'} && $proxysettings{'ENABLED_BLUE_1'} eq 'on');
}

# Build list of network interfaces
my @interfaces;
for my $color ('GREEN', 'ORANGE', 'BLUE', 'RED') {
    my $count = $netsettings{"${color}_COUNT"} || 0;
    for my $i (1 .. $count) {
        push @interfaces, "${color}_$i";
    }
}
# Always include RED_1 for modem/ISDN
push @interfaces, 'RED_1' unless grep { $_ eq 'RED_1' } @interfaces;

&Header::showhttpheaders();
&Header::openpage('Interactive Graphs', 1, '');
&Header::openbigbox('100%', 'left');

print <<'HTML';
<style>
    .graph-container {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .graph-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 15px;
        color: #333;
    }
    .graph-canvas {
        width: 100% !important;
        height: 250px !important;
    }
    .period-selector {
        margin-bottom: 20px;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 4px;
    }
    .period-selector button {
        padding: 8px 16px;
        margin-right: 8px;
        border: 1px solid #ccc;
        background: #fff;
        border-radius: 4px;
        cursor: pointer;
    }
    .period-selector button.active {
        background: #4a90d9;
        color: #fff;
        border-color: #4a90d9;
    }
    .legend-table {
        width: 100%;
        margin-top: 10px;
        font-size: 12px;
        border-collapse: collapse;
    }
    .legend-table th, .legend-table td {
        padding: 4px 12px;
        text-align: right;
    }
    .legend-table th:first-child, .legend-table td:first-child {
        text-align: left;
    }
    .legend-color {
        display: inline-block;
        width: 12px;
        height: 12px;
        margin-right: 6px;
        vertical-align: middle;
    }
    .loading {
        text-align: center;
        padding: 40px;
        color: #666;
    }
</style>

<!-- Chart.js from CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>

<div class="period-selector">
    <strong>Period:</strong>
    <button onclick="setPeriod('hour')">Hour</button>
    <button onclick="setPeriod('day')" class="active">Day</button>
    <button onclick="setPeriod('week')">Week</button>
    <button onclick="setPeriod('month')">Month</button>
    <button onclick="setPeriod('year')">Year</button>
</div>

<div id="graphs-container">
    <div class="loading">Loading graphs...</div>
</div>

<script>
let currentPeriod = 'day';
const charts = {};

// Color palettes
const colors = {
    cpu: ['#3366cc', '#dc3912', '#109618'],
    memory: ['#3366cc', '#dc3912', '#ff9900', '#990099', '#109618'],
    disk: ['#3366cc', '#109618'],
    diskuse: ['#3366cc', '#109618'],
    network: ['#109618', '#3366cc'],
    proxy: ['#109618']
};

function setPeriod(period) {
    currentPeriod = period;
    document.querySelectorAll('.period-selector button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase() === period) btn.classList.add('active');
    });
    loadAllGraphs();
}

async function fetchGraphData(type, iface = null) {
    let url = `/cgi-bin/graphdata.cgi?type=${type}&period=${currentPeriod}`;
    if (iface) url += `&iface=${iface}`;
    
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (e) {
        console.error('Failed to fetch graph data:', e);
        return null;
    }
}

function formatValue(value, type) {
    if (value === null || value === undefined) return 'N/A';
    
    if (type === 'bytes') {
        // Convert bits to human readable
        if (value >= 1e9) return (value / 1e9).toFixed(2) + ' Gbps';
        if (value >= 1e6) return (value / 1e6).toFixed(2) + ' Mbps';
        if (value >= 1e3) return (value / 1e3).toFixed(2) + ' Kbps';
        return value.toFixed(2) + ' bps';
    }
    if (type === 'percent') {
        return value.toFixed(2) + ' %';
    }
    return value.toFixed(2);
}

function calculateStats(data) {
    const valid = data.filter(v => v !== null && v !== undefined);
    if (valid.length === 0) return { max: null, avg: null, current: null };
    
    return {
        max: Math.max(...valid),
        avg: valid.reduce((a, b) => a + b, 0) / valid.length,
        current: valid[valid.length - 1]
    };
}

function createChart(containerId, title, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Build datasets
    const isStacked = data.type === 'cpu' || data.type === 'memory' || data.type === 'diskuse';
    const datasets = data.labels.map((label, i) => ({
        label: label,
        data: data.series[label],
        borderColor: colors[data.type]?.[i] || '#333',
        backgroundColor: isStacked ? (colors[data.type]?.[i] + '80') : (colors[data.type]?.[i] + '40'),
        fill: isStacked ? 'origin' : false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: isStacked ? 1 : 2
    }));
    
    // Create canvas
    const canvasId = containerId + '-canvas';
    let html = `<div class="graph-title">${title}</div>`;
    html += `<canvas id="${canvasId}" class="graph-canvas"></canvas>`;
    
    // Build legend table
    html += `<table class="legend-table">
        <tr><th>Series</th><th>Maximum</th><th>Average</th><th>Current</th></tr>`;
    
    data.labels.forEach((label, i) => {
        const stats = calculateStats(data.series[label]);
        const color = colors[data.type]?.[i] || '#333';
        html += `<tr>
            <td><span class="legend-color" style="background:${color}"></span>${label}</td>
            <td>${formatValue(stats.max, data.valueType)}</td>
            <td>${formatValue(stats.avg, data.valueType)}</td>
            <td>${formatValue(stats.current, data.valueType)}</td>
        </tr>`;
    });
    html += '</table>';
    
    container.innerHTML = html;
    
    // Create chart
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    if (charts[containerId]) {
        charts[containerId].destroy();
    }
    
    charts[containerId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            hour: 'HH:mm',
                            day: 'MMM d HH:mm',
                            week: 'MMM d',
                            month: 'MMM d'
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    stacked: data.type === 'cpu' || data.type === 'memory' || data.type === 'diskuse',
                    max: data.type === 'cpu' || data.type === 'memory' || data.type === 'diskuse' ? 100 : undefined
                }
            },
            plugins: {
                legend: {
                    display: false  // We use custom table legend
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatValue(context.raw, data.valueType);
                        }
                    }
                }
            }
        }
    });
}

async function loadAllGraphs() {
    const container = document.getElementById('graphs-container');
    
HTML

# Inject interface list and proxy status from Perl
print "    const interfaces = ['" . join("', '", @interfaces) . "'];\n";
print "    const proxyEnabled = " . ($proxy_enabled ? 'true' : 'false') . ";\n";

print <<'HTML';
    
    // Build container HTML
    let html = '';
    html += '<div id="cpu-graph" class="graph-container"><div class="loading">Loading CPU...</div></div>';
    html += '<div id="memory-graph" class="graph-container"><div class="loading">Loading Memory...</div></div>';
    html += '<div id="diskuse-graph" class="graph-container"><div class="loading">Loading Disk Usage...</div></div>';
    html += '<div id="disk-graph" class="graph-container"><div class="loading">Loading Disk I/O...</div></div>';
    
    interfaces.forEach(iface => {
        html += `<div id="network-${iface}-graph" class="graph-container"><div class="loading">Loading ${iface}...</div></div>`;
    });
    
    // Add proxy graphs if enabled
    if (proxyEnabled) {
        html += '<div id="proxy-requests-graph" class="graph-container"><div class="loading">Loading Proxy Requests...</div></div>';
        html += '<div id="proxy-hits-graph" class="graph-container"><div class="loading">Loading Proxy Hits...</div></div>';
    }
    
    container.innerHTML = html;
    
    // Load each graph
    const cpuData = await fetchGraphData('cpu');
    if (cpuData && !cpuData.error) {
        createChart('cpu-graph', `CPU Usage (${currentPeriod})`, cpuData);
    }
    
    const memData = await fetchGraphData('memory');
    if (memData && !memData.error) {
        createChart('memory-graph', `Memory Usage (${currentPeriod})`, memData);
    }
    
    const diskuseData = await fetchGraphData('diskuse');
    if (diskuseData && !diskuseData.error) {
        createChart('diskuse-graph', `Disk Usage (${currentPeriod})`, diskuseData);
    }
    
    const diskData = await fetchGraphData('disk');
    if (diskData && !diskData.error) {
        createChart('disk-graph', `Disk I/O (${currentPeriod})`, diskData);
    }
    
    for (const iface of interfaces) {
        const netData = await fetchGraphData('network', iface);
        if (netData && !netData.error) {
            createChart(`network-${iface}-graph`, `Traffic on ${iface} (${currentPeriod})`, netData);
        }
    }
    
    // Proxy graphs (if enabled)
    if (proxyEnabled) {
        const proxyReqData = await fetchGraphData('squid-requests');
        if (proxyReqData && !proxyReqData.error) {
            createChart('proxy-requests-graph', `Proxy Requests (${currentPeriod})`, proxyReqData);
        }
        
        const proxyHitsData = await fetchGraphData('squid-hits');
        if (proxyHitsData && !proxyHitsData.error) {
            createChart('proxy-hits-graph', `Proxy Hit Percentage (${currentPeriod})`, proxyHitsData);
        }
    }
}

// Initial load
loadAllGraphs();
</script>
HTML

&Header::closebigbox();
&Header::closepage();
