#!/bin/sh
# install.sh - Install IPCop Modular Packages
#
# Uses direct file installation for reliability
#
set -e

# Auto-logging: Re-execute script with tee if not already logging
if [ -z "$INSTALL_LOGGING" ]; then
    export INSTALL_LOGGING=1
    exec "$0" "$@" 2>&1 | tee "install.log"
fi
# If we get here, we're already logging via tee

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

msg() {
	echo -e "${GREEN}==>${NC} $@"
}

msg_info() {
	echo -e "${BLUE}  ->${NC} $@"
}

msg_warn() {
	echo -e "${YELLOW}WARNING:${NC} $@"
}

msg_error() {
	echo -e "${RED}ERROR:${NC} $@"
}

die() {
	echo -e "${RED}ERROR:${NC} $@" >&2
	exit 1
}

# Determine script location and package path
# Detect architecture dynamically
MACHINE="$(uname -m)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="${SCRIPT_DIR}/packages/${MACHINE}"

# Verify packages exist
if [ ! -d "$PKG_DIR" ] || [ -z "$(ls -A "$PKG_DIR"/*.apk 2>/dev/null)" ]; then
    die "No packages found in $PKG_DIR. Please run build.sh first to build the packages."
fi

# Trust the signing key if present
KEY_DIR="${SCRIPT_DIR}/../keys"
if [ -d "$KEY_DIR" ] && [ -n "$(ls -A "$KEY_DIR"/*.rsa.pub 2>/dev/null)" ]; then
    msg_info "Installing signing keys from repo..."
    sudo cp "$KEY_DIR"/*.rsa.pub /etc/apk/keys/
elif [ -d "$HOME/.abuild" ]; then
    msg_info "Installing signing keys from ~/.abuild..."
    sudo cp "$HOME/.abuild/"*.rsa.pub /etc/apk/keys/ 2>/dev/null || true
fi

msg "Installing IPCop Core..."
# Use find or globs carefully. apk add works with specific files.
# We assume only one version exists in PKG_DIR due to clean build.
sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-core-*.apk "$PKG_DIR"/ipcop-lang-*.apk "$PKG_DIR"/ipcop-installer-*.apk "$PKG_DIR"/perl-apache-htpasswd-*.apk "$PKG_DIR"/perl-net-ipv4addr-*.apk

echo ""
msg "Select optional packages to install:"
echo "  1. ipcop-squid     - Web Proxy (Squid)"
echo "  2. ipcop-e2guardian - Content Filter (E2Guardian)"
echo "  3. ipcop-suricata  - IDS/IPS (Suricata)"
echo "  4. ipcop-wireguard - VPN (WireGuard)"
echo "  5. ipcop-openvpn   - VPN (OpenVPN)"
echo "  a. All optional packages"
echo "  n. None (core only)"
echo ""
read -p "Enter selection [a/1-5/n]: " choice

case "$choice" in
    a|A)
        sudo apk add --allow-untrusted --force-overwrite \
            "$PKG_DIR"/ipcop-squid-*.apk \
            "$PKG_DIR"/ipcop-e2guardian-*.apk \
            "$PKG_DIR"/ipcop-suricata-*.apk \
            "$PKG_DIR"/ipcop-wireguard-*.apk \
            "$PKG_DIR"/ipcop-openvpn-*.apk
        ;;
    1) sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-squid-*.apk ;;
    2) sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-e2guardian-*.apk ;;
    3) sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-suricata-*.apk ;;
    4) sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-wireguard-*.apk ;;
    5) sudo apk add --allow-untrusted --force-overwrite "$PKG_DIR"/ipcop-openvpn-*.apk ;;
    n|N) msg_info "Skipping optional packages." ;;
    *)
        msg_info "Installing all optional packages..."
        sudo apk add --allow-untrusted --force-overwrite \
            "$PKG_DIR"/ipcop-squid-*.apk \
            "$PKG_DIR"/ipcop-e2guardian-*.apk \
            "$PKG_DIR"/ipcop-suricata-*.apk \
            "$PKG_DIR"/ipcop-wireguard-*.apk \
            "$PKG_DIR"/ipcop-openvpn-*.apk
        ;;
esac

# ============================================================================
# Step 3: Post-Installation Configuration
# ============================================================================

msg "Running post-installation configuration..."

# Install CPAN modules
msg_info "Installing CPAN Perl modules..."
for module in Apache::Htpasswd Net::IPv4Addr Locale::Maketext::Gettext::Functions; do
	if perl -M"$module" -e 1 2>/dev/null; then
		msg_info "  ✓ $module already installed"
	else
		msg_info "  Installing $module..."
		cpanm --quiet --notest "$module" || msg_warn "Failed to install $module"
	fi
done

# Create missing configuration files
msg_info "Creating missing configuration files..."

# dnsmasq.conf
if [ ! -f "/var/ipcop/dhcp/dnsmasq.conf" ]; then
	cat > /var/ipcop/dhcp/dnsmasq.conf <<'EOF'
# IPCop dnsmasq configuration
domain-needed
bogus-priv
filterwin2k
expand-hosts
domain=localdomain
local=/localdomain/
EOF
	chown root:lighttpd /var/ipcop/dhcp/dnsmasq.conf
	chmod 0640 /var/ipcop/dhcp/dnsmasq.conf
	msg_info "  ✓ dnsmasq.conf created"
fi


# Ensure Busybox syslog is stopped/disabled
if rc-service syslog status >/dev/null 2>&1; then
    msg_info "Stopping/Disabling conflicting syslog service..."
    rc-service syslog stop >/dev/null 2>&1 || true
    rc-update del syslog default >/dev/null 2>&1 || true
    rc-update del syslog boot >/dev/null 2>&1 || true
fi

# Disable stock Alpine openvpn service (prevents "config not readable" errors)
if rc-service -e openvpn; then
    msg_info "Disabling stock openvpn service (using ipcop-openvpn instead)..."
    rc-service openvpn stop >/dev/null 2>&1 || true
    rc-update del openvpn default >/dev/null 2>&1 || true
    rc-update del openvpn boot >/dev/null 2>&1 || true
fi

# SSL certificate for lighttpd
if [ ! -f "/etc/lighttpd/server.pem" ]; then
	msg_info "Generating self-signed SSL certificate..."
	openssl req -new -x509 -keyout /etc/lighttpd/server.pem -out /etc/lighttpd/server.pem \
		-days 3650 -nodes -subj "/C=US/ST=State/L=City/O=IPCop/CN=ipcop" >/dev/null 2>&1
	chmod 600 /etc/lighttpd/server.pem
	msg_info "  ✓ SSL certificate created"
fi

# Traffic database directory
if [ ! -d "/var/log/traffic" ]; then
	mkdir -p /var/log/traffic
	chown root:lighttpd /var/log/traffic
	chmod 0750 /var/log/traffic
	msg_info "  ✓ /var/log/traffic created"
fi

# Firewall configuration files (critical - CGI fails without these)
for fwfile in config input outgoing; do
	if [ ! -f "/var/ipcop/firewall/$fwfile" ]; then
		touch "/var/ipcop/firewall/$fwfile"
		chown root:lighttpd "/var/ipcop/firewall/$fwfile"
		chmod 0660 "/var/ipcop/firewall/$fwfile"
		msg_info "  ✓ /var/ipcop/firewall/$fwfile created"
	fi
done

# Backup encryption key
if [ ! -f "/var/ipcop/backup/backup.key" ]; then
	msg_info "Generating backup encryption key..."
	mkdir -p /var/ipcop/backup
	openssl rand -base64 32 > /var/ipcop/backup/backup.key
	chmod 400 /var/ipcop/backup/backup.key
	chown root:root /var/ipcop/backup/backup.key
	msg_info "  ✓ Backup encryption key created"
fi

# RRD Database directory (Graphs)
if [ -d "/var/log/rrd" ]; then
    owner="root"
    if getent passwd collectd >/dev/null 2>&1; then
        owner="collectd"
    fi
	chown -R "${owner}:lighttpd" /var/log/rrd
	chown -R "${owner}:lighttpd" /var/log/rrd
	chmod -R 0775 /var/log/rrd
	msg_info "  ✓ /var/log/rrd permissions fixed (${owner}:lighttpd)"
fi

# Fix /var/log/messages permissions (Critical for WebUI)
if [ -f "/var/log/messages" ]; then
    chown root:lighttpd /var/log/messages
    chmod 0640 /var/log/messages
    msg_info "  ✓ /var/log/messages permissions fixed (root:lighttpd)"
fi

# Final permission fix - some packages may have installed files as root:root
msg_info "Applying final permissions to /var/ipcop..."
chown -R root:lighttpd /var/ipcop 2>/dev/null || true
chmod -R u=rwX,g=rwX,o= /var/ipcop 2>/dev/null || true
find /var/ipcop -type d -exec chmod g+s {} + 2>/dev/null || true

# Fix Proxy permissions (Squid runs as 'squid', needs read access)
if [ -d "/var/ipcop/proxy" ]; then
    chmod -R o+rX /var/ipcop/proxy
fi

# Start services
msg_info "Starting services..."
for service in rsyslog lighttpd collectd fcron; do
	if [ -f "/etc/init.d/$service" ]; then
		rc-service "$service" status >/dev/null 2>&1 || rc-service "$service" start 2>/dev/null || true
	fi
done

# Enable e2guardian if installed
if [ -f "/etc/init.d/e2guardian" ]; then
    rc-update add e2guardian default >/dev/null 2>&1 || true
    rc-service e2guardian status >/dev/null 2>&1 || rc-service e2guardian start 2>/dev/null || true
fi

# Enable ipcop-openvpn (Legacy wrapper)
if [ -f "/etc/init.d/ipcop-openvpn" ]; then
    rc-update add ipcop-openvpn default >/dev/null 2>&1 || true
    # Attempt start (it checks for config internally)
    rc-service ipcop-openvpn status >/dev/null 2>&1 || rc-service ipcop-openvpn start 2>/dev/null || true
fi

msg "Post-installation configuration complete ✓"
echo ""


# ============================================================================
# Comprehensive System Integrity Verification
# ============================================================================

msg "Verifying installation integrity..."
echo ""

ISSUES=0
WARNINGS=0

# --- Check Critical Services ---
msg_info "Checking services..."
for service in lighttpd collectd fcron rsyslog; do
	if rc-service "$service" status >/dev/null 2>&1; then
		echo "  ✓ $service running"
	else
		echo "  ✗ $service NOT running"
		ISSUES=$((ISSUES + 1))
	fi
done

# --- Check Critical Directories ---
msg_info "Checking directories..."
for dir in /var/ipcop /var/www/ipcop /var/log/rrd /var/log/traffic; do
	if [ -d "$dir" ]; then
		echo "  ✓ $dir exists"
	else
		echo "  ✗ $dir MISSING"
		ISSUES=$((ISSUES + 1))
	fi
done

# --- Check Critical File Permissions ---
msg_info "Checking critical file permissions..."

# /var/log/rrd (should be collectd:lighttpd or root:lighttpd with 0775)
if [ -d "/var/log/rrd" ]; then
    perms=$(stat -c "%a" /var/log/rrd 2>/dev/null || stat -f "%Lp" /var/log/rrd 2>/dev/null)
    group=$(stat -c "%G" /var/log/rrd 2>/dev/null || stat -f "%Sg" /var/log/rrd 2>/dev/null)
    if [ "$group" = "lighttpd" ] && [ "$perms" = "2775" -o "$perms" = "775" ]; then
        echo "  ✓ /var/log/rrd permissions correct ($perms, group=$group)"
    else
        echo "  ⚠ /var/log/rrd permissions may be wrong ($perms, group=$group)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# /var/log/messages (should be root:lighttpd 0640)
if [ -f "/var/log/messages" ]; then
    group=$(stat -c "%G" /var/log/messages 2>/dev/null || stat -f "%Sg" /var/log/messages 2>/dev/null)
    perms=$(stat -c "%a" /var/log/messages 2>/dev/null || stat -f "%Lp" /var/log/messages 2>/dev/null)
    if [ "$group" = "lighttpd" ] && [ "$perms" = "640" ]; then
        echo "  ✓ /var/log/messages readable by WebUI"
    else
        echo "  ⚠ /var/log/messages permissions may prevent WebUI access ($perms, group=$group)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# /var/ipcop (should have SETGID on directories)
if [ -d "/var/ipcop" ]; then
    # Check if at least main directory has SETGID
    perms=$(stat -c "%a" /var/ipcop 2>/dev/null || stat -f "%Lp" /var/ipcop 2>/dev/null)
    if [ "${perms:0:1}" = "2" ] || [ "${perms:0:1}" = "3" ]; then
        echo "  ✓ /var/ipcop has SETGID (prevents permission issues)"
    else
        echo "  ⚠ /var/ipcop missing SETGID (may cause permission issues)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# --- Check Required Perl Modules ---
msg_info "Checking Perl modules..."
for module in JSON CGI Net::SSLeay Apache::Htpasswd Net::IPv4Addr; do
	if perl -M"$module" -e 1 2>/dev/null; then
		echo "  ✓ $module available"
	else
		echo "  ✗ $module MISSING"
		ISSUES=$((ISSUES + 1))
	fi
done

# --- Check SUID Helper Programs ---
msg_info "Checking SUID helper programs..."
for prog in setfwrules ipcopbackup red restartdhcp; do
    if [ -f "/usr/bin/$prog" ]; then
        # Check if SUID bit is set
        if [ -u "/usr/bin/$prog" ]; then
            echo "  ✓ $prog (SUID)"
        else
            echo "  ⚠ $prog exists but missing SUID bit"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "  ✗ $prog MISSING"
        ISSUES=$((ISSUES + 1))
    fi
done

# --- Check Critical Configuration Files ---
msg_info "Checking configuration files..."

# Lighttpd config
if [ -f "/etc/lighttpd/lighttpd.conf" ]; then
    if grep -q "server.document-root.*ipcop" /etc/lighttpd/lighttpd.conf 2>/dev/null; then
        echo "  ✓ lighttpd.conf (IPCop configuration)"
    else
        echo "  ⚠ lighttpd.conf may not be IPCop version"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ✗ lighttpd.conf MISSING"
    ISSUES=$((ISSUES + 1))
fi

# SSL certificate
if [ -f "/etc/lighttpd/server.pem" ]; then
    echo "  ✓ server.pem (SSL certificate)"
else
    echo "  ✗ server.pem MISSING (HTTPS won't work)"
    ISSUES=$((ISSUES + 1))
fi

# Collectd config
if [ -f "/etc/collectd/collectd.conf" ]; then
    if grep -q "LoadPlugin rrdtool" /etc/collectd/collectd.conf 2>/dev/null; then
        echo "  ✓ collectd.conf (RRD plugin enabled)"
    else
        echo "  ⚠ collectd.conf missing RRD plugin (no graphs)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Traffic database schemas
if [ -f "/var/ipcop/traffic/sqlite3.table" ]; then
    echo "  ✓ traffic database schema installed"
else
    echo "  ⚠ traffic database schema MISSING (traffic accounting may fail)"
    WARNINGS=$((WARNINGS + 1))
fi

# Crontab
if [ -f "/var/spool/cron/crontabs/root" ]; then
    if grep -q "makegraphs" /var/spool/cron/crontabs/root 2>/dev/null; then
        echo "  ✓ crontab (periodic tasks configured)"
    else
        echo "  ⚠ crontab exists but may be incomplete"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ⚠ crontab MISSING (no periodic tasks)"
    WARNINGS=$((WARNINGS + 1))
fi

# --- Check Email Templates ---
if [ -d "/var/ipcop/email/templates" ] && [ -n "$(ls -A /var/ipcop/email/templates 2>/dev/null)" ]; then
    template_count=$(ls -1 /var/ipcop/email/templates 2>/dev/null | wc -l)
    echo "  ✓ Email templates ($template_count files)"
else
    echo "  ⚠ Email templates MISSING (notifications won't work)"
    WARNINGS=$((WARNINGS + 1))
fi

# --- Summary ---
echo ""
if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
	msg "Verification PASSED ✓ - System appears healthy"
elif [ $ISSUES -eq 0 ]; then
	msg_warn "Verification found $WARNINGS warning(s) - System should work but review above"
else
	msg_error "Verification found $ISSUES issue(s) and $WARNINGS warning(s)"
	echo ""
	echo "Please review the issues above before proceeding."
	echo "Some functionality may not work correctly."
fi
echo ""

# ============================================================================
# Final Message
# ============================================================================

cat <<'EOF'

╔════════════════════════════════════════════════════════╗
║         IPCop Installation Complete!                   ║
╚════════════════════════════════════════════════════════╝

Next Steps:

1. Access the WebUI:
   https://<this-ip>:8443
   
   Default credentials:
   User: admin
   Pass: ipcop (change immediately!)

2. Graphs will appear in ~10 minutes after collectd gathers data

3. To update packages:
   - Rebuild packages on build VM
   - Re-run this script: ./install-ipcop.sh

4. Troubleshooting:
   - Check services: rc-status
   - View logs: tail -f /var/log/lighttpd/error.log
   - View system logs: tail -f /var/log/messages
   - Installation log: ./install.log

EOF