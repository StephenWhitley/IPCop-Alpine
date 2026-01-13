#!/bin/sh
# setup.sh - Setup Alpine Build Environment for IPCop
set -e

echo "Setting up Alpine Build Environment..."

# Install basic build tools
sudo apk add alpine-sdk abuild git dos2unix

# Add user to abuild group
if ! groups | grep -q abuild; then
    sudo addgroup $(whoami) abuild
    echo "Added user to abuild group. You may need to logout/login."
fi

# Generate keys
if [ ! -f "$HOME/.abuild/abuild.conf" ]; then
    mkdir -p "$HOME/.abuild"
    echo "PACKAGER=\"IPCop Dev <dev@ipcop.org>\"" > "$HOME/.abuild/abuild.conf"
    echo "REPODEST=\"$HOME/packages\"" >> "$HOME/.abuild/abuild.conf"
fi

if [ ! -f "$HOME/.abuild/"*.rsa ]; then
    abuild-keygen -a -i -n
fi

echo "Setup complete."
