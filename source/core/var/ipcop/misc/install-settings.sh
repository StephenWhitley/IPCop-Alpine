#!/bin/bash
# Script to install IPCop settings files
# Run with: sudo bash install-settings.sh

SETTINGS_DIR="/var/ipcop"

echo "Installing IPCop settings files..."

# Create settings file with proper owners
install_setting() {
    local subdir=$1
    local file=$2
    local owner=${3:-nobody:nobody}
    
    mkdir -p "$SETTINGS_DIR/$subdir"
    cp "$file" "$SETTINGS_DIR/$subdir/settings"
    chown $owner "$SETTINGS_DIR/$subdir/settings"
    chmod 644 "$SETTINGS_DIR/$subdir/settings"
    echo "  Installed $subdir/settings"
}

# Install all settings
install_setting "ethernet" "ethernet-settings"
install_setting "main" "main-settings"
install_setting "ppp" "ppp-settings"
install_setting "proxy" "proxy-settings"  
install_setting "logging" "logging-settings" "root:root"
install_setting "dhcp" "dhcp-settings"
install_setting "time" "time-settings"
install_setting "traffic" "traffic-settings"
install_setting "modem" "modem-settings"

echo "All settings files installed successfully!"
echo ""
echo "Settings installed in:"
ls -la $SETTINGS_DIR/*/settings
