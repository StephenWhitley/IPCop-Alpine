#!/bin/sh
# setup-alpine.sh - Prepare Alpine Linux for IPCop
# 
# Run this script ONCE on a fresh Alpine installation to prepare it for IPCop.
# This installs system dependencies and configures Alpine-specific settings.
#
# Usage: ./setup-alpine.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

msg() {
	echo -e "${GREEN}==> ${NC}$@"
}

msg_info() {
	echo -e "${BLUE}  -> ${NC}$@"
}

msg_warn() {
	echo -e "${YELLOW}WARNING:${NC} $@"
}

die() {
	echo -e "${RED}ERROR:${NC} $@" >&2
	exit 1
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
	die "This script must be run as root (use sudo)"
fi

echo ""
msg "IPCop Alpine Preparation Script"
msg_info "Preparing Alpine Linux for IPCop installation"
echo ""

# ============================================================================
# Step 1: Install System Dependencies
# ============================================================================

msg "Installing system dependencies from Alpine repositories..."

# Core packages needed by IPCop
msg_info "Installing core packages..."
apk add --quiet \
	perl perl-cgi perl-dbi perl-dbd-sqlite \
	rrdtool \
	lighttpd lighttpd-mod_auth \
	fcron \
	rsyslog \
	conntrack-tools \
	collectd collectd-rrdtool collectd-disk \
	dhcpcd dnsmasq \
	iptables iptables-legacy \
	openssh \
	sudo \
	apache2-utils \
	newt slang pciutils libusb \
	|| die "Failed to install core packages"

# Build tools for CPAN
msg_info "Installing build tools for Perl modules..."
apk add --quiet \
	gcc make perl-dev perl-app-cpanminus \
	|| die "Failed to install build tools"

msg "System dependencies installed ✓"
echo ""

# ============================================================================
# Step 2: Configure System Services
# ============================================================================

msg "Configuring Alpine system services..."

# Disable conflicting services
msg_info "Disabling conflicting services..."
rc-update del crond default 2>/dev/null || true
rc-update del crond boot 2>/dev/null || true
rc-update del dnsmasq default 2>/dev/null || true
rc-update del dnsmasq boot 2>/dev/null || true

# Enable fcron (we need it for %daily syntax in crontab)
msg_info "Enabling fcron..."
rc-update add fcron default 2>/dev/null || true

# Enable rsyslog (for system logging)
msg_info "Enabling rsyslog..."
rc-update add rsyslog default 2>/dev/null || true

# Enable lighttpd (for web service)
msg_info "Enabling lighttpd..."
rc-update add lighttpd default 2>/dev/null || true

msg "System services configured ✓"
echo ""

# ============================================================================
# Step 3: Create iptables Symlinks
# ============================================================================

msg "Creating iptables compatibility symlinks..."

# IPCop expects iptables in /sbin
if [ -x /usr/sbin/iptables ]; then
	ln -sf /usr/sbin/iptables /sbin/iptables 2>/dev/null || true
	ln -sf /usr/sbin/iptables-restore /sbin/iptables-restore 2>/dev/null || true
	ln -sf /usr/sbin/iptables-save /sbin/iptables-save 2>/dev/null || true
	msg_info "/sbin/iptables -> /usr/sbin/iptables"
fi

msg "iptables symlinks created ✓"
echo ""

# ============================================================================
# Final Message
# ============================================================================

cat <<'EOF'

╔════════════════════════════════════════════════════════╗
║         Alpine Preparation Complete!                   ║
╚════════════════════════════════════════════════════════╝

Alpine Linux is now ready for IPCop installation.

Next Steps:

1. Build IPCop packages on your build VM (if not done):
   cd /path/to/ipcop
   ./alpine/build-on-alpine.sh

2. Copy packages to this VM and run install-ipcop.sh:
   ./install-ipcop.sh

EOF
