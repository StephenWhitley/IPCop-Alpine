#!/bin/sh
# populate-source-tree.sh
# Automatically populate source tree from deployed system based on snapshot listing
#
# Usage: Run this on the deployed IPCop system with access to the output file
#        ./populate-source-tree.sh /mnt/ipcop/output /mnt/ipcop/ipcop-alpine/newsource

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <output-file> <destination-dir>"
    echo "Example: $0 /mnt/ipcop/output /mnt/ipcop/ipcop-alpine/newsource"
    exit 1
fi

OUTPUT_FILE="$1"
DEST_BASE="$2"
SRC_BASE="$(dirname "$0")/../legacy_src"

# Service identification patterns
SERVICE_SQUID="squid|proxy|restartsquid|makesquidconf"
SERVICE_E2GUARDIAN="e2guardian|urlfilter|redirectwrapper|blacklists|blacklistupdate"
SERVICE_SURICATA="suricata|restartsuricata"
SERVICE_WIREGUARD="wireguard|wireguardctrl"
SERVICE_OPENVPN="openvpn|restartopenvpn"

# Core SUID programs (not service-specific)
CORE_SUID_PROGS="accountingctrl|setfwrules|emailhelper|restartdhcp|restartssh|ipcopreboot"
CORE_SUID_PROGS="$CORE_SUID_PROGS|ipcopbkcfg|ipcopbackup|ipcoprestore|installpackage|installfcdsl"
CORE_SUID_PROGS="$CORE_SUID_PROGS|ipsecctrl|red|setaliases|restartshaping|restartntpd"
CORE_SUID_PROGS="$CORE_SUID_PROGS|setdate|rebuildhosts|rebuildlangtexts|conntrack_helper"
CORE_SUID_PROGS="$CORE_SUID_PROGS|restartsyslogd|sysinfo|iptableswrapper"

echo "=== IPCop Source Tree Population Tool ==="
echo "Output file: $OUTPUT_FILE"
echo "Destination: $DEST_BASE"
echo "Source code: $SRC_BASE"
echo ""

# Clean destination to avoid stale files
echo "Cleaning destination directory..."
rm -rf "$DEST_BASE" 2>/dev/null || sudo rm -rf "$DEST_BASE"

# Create base directories
mkdir -p "$DEST_BASE/core"/{etc,html,installer,lib,progs,scripts,var,defaults}
mkdir -p "$DEST_BASE/services"/{squid,e2guardian,suricata,wireguard,openvpn}/{defaults,var}

# Function to determine service from path/filename
get_service() {
    local path="$1"
    local basename=$(basename "$path")
    
    # Check E2Guardian BEFORE Squid (because E2Guardian files often live in proxy/ paths)
    echo "$path" | grep -qiE "$SERVICE_E2GUARDIAN" && echo "e2guardian" && return
    echo "$path" | grep -qiE "$SERVICE_SQUID" && echo "squid" && return
    echo "$path" | grep -qiE "$SERVICE_SURICATA" && echo "suricata" && return
    echo "$path" | grep -qiE "$SERVICE_WIREGUARD" && echo "wireguard" && return
    echo "$path" | grep -qiE "$SERVICE_OPENVPN" && echo "openvpn" && return
    
    echo "core"
}

# Function to map deployed path to source path
map_to_source() {
    local deployed_path="$1"
    local service="$2"
    local source_path=""
    
    case "$deployed_path" in
        usr/lib/ipcop/*)
            # Perl libraries
            filename=$(basename "$deployed_path")
            if [ "$service" = "core" ]; then
                source_path="core/lib/$filename"
            else
                source_path="services/$service/lib/$filename"
            fi
            ;;
            
        usr/bin/*)
            # Programs and scripts
            filename=$(basename "$deployed_path")
            
            # Check if it's a SUID program or script
            if echo "$filename" | grep -qE "^($CORE_SUID_PROGS)$"; then
                source_path="core/progs/$filename.c"
            elif [ "$service" != "core" ]; then
                # Service-specific program
                if echo "$filename" | grep -q '\.pl$\|\.sh$'; then
                    source_path="services/$service/scripts/$filename"
                elif [ "$filename" = "redirectwrapper" ]; then
                    source_path="services/$service/scripts/$filename"
                else
                    source_path="services/$service/progs/$filename.c"
                fi
            elif echo "$filename" | grep -q '\.pl$\|\.sh$'; then
                source_path="core/scripts/$filename"
            else
                # Other core scripts/programs
                source_path="core/scripts/$filename"
            fi
            ;;
            
        usr/share/ipcop/defaults/*)
            # Default configuration files (flat structure in deployed files)
            filename=$(basename "$deployed_path")
            
            # Map flat defaults to HIERARCHICAL source var/ipcop structure
            # This allows the package to install directly to /var/ipcop (or be copied there)
            case "$filename" in
                # Core Mappings
                main-settings)      source_path="core/var/ipcop/main/settings" ;;
                ethernet-settings)  source_path="core/var/ipcop/ethernet/settings" ;;
                firewall-settings)  source_path="core/var/ipcop/firewall/settings" ;;
                logging-settings)   source_path="core/var/ipcop/logging/settings" ;;
                time-settings)      source_path="core/var/ipcop/time/settings" ;;
                traffic-settings)   source_path="core/var/ipcop/traffic/settings" ;;
                dhcp-settings)      source_path="core/var/ipcop/dhcp/settings" ;;
                ppp-settings)       source_path="core/var/ipcop/ppp/settings" ;;
                modem-settings)     source_path="core/var/ipcop/modem/settings" ;;
                modem-defaults)     source_path="core/var/ipcop/modem/defaults" ;;
                ntp.conf)           source_path="core/var/ipcop/time/ntp.conf" ;;
                defaultservices)    source_path="core/var/ipcop/firewall/defaultservices" ;;
                icmptypes)          source_path="core/var/ipcop/firewall/icmptypes" ;;
                backup-exclude)     source_path="core/var/ipcop/backup/exclude.system" ;;
                backup-include)     source_path="core/var/ipcop/backup/include.system" ;;
                backup-exclude.hardware) source_path="core/var/ipcop/backup/exclude.hardware" ;;
                scheduler)          source_path="core/var/ipcop/main/scheduler" ;;
                menu.lst)           source_path="core/var/ipcop/main/menu.lst" ;;
                dnsmasq.conf)       source_path="core/var/ipcop/dhcp/dnsmasq.conf" ;;
                dnsmasq.local)      source_path="core/var/ipcop/dhcp/dnsmasq.local" ;;
                nic-modules-list)   source_path="core/var/ipcop/ethernet/nic-modules-list" ;;
                isdn-card-list)     source_path="core/var/ipcop/isdn/card-list" ;;
                aggregate.table)    source_path="core/var/ipcop/traffic/aggregate.table" ;;
                ipcop.gpg|ipcop2.gpg) source_path="core/var/ipcop/key/$filename" ;;
                
                # Service Mappings
                squid-settings)     source_path="services/squid/var/ipcop/proxy/settings" ;;
                proxy-settings)     source_path="services/squid/var/ipcop/proxy/proxy-settings" ;;
                e2guardian-settings)source_path="services/e2guardian/var/ipcop/e2guardian/settings" ;;
                suricata-settings)  source_path="services/suricata/var/ipcop/suricata/settings" ;;
                openvpn)            source_path="services/openvpn/var/ipcop/openvpn/settings" ;;
                wireguard)          source_path="services/wireguard/var/ipcop/wireguard/settings" ;;
                
                # E2Guardian Extras
                useragents)         source_path="services/e2guardian/var/ipcop/proxy/useragents" ;;
                redirector-urlfilter) source_path="services/e2guardian/var/ipcop/proxy/redirector/urlfilter" ;;
                blacklistupdate.urls) source_path="services/e2guardian/var/ipcop/proxy/blacklistupdate/blacklistupdate.urls" ;;
                
                # Exclusions
                squidGuard.conf|ufdbGuard.conf) return 1 ;;

                # Fallback for unknown files
                *)
                    source_path="core/var/ipcop/misc/$filename" ;;
            esac
            ;;
            
        etc/rc.d/*)
            # Legacy RC scripts
            filename=$(basename "$deployed_path")
            source_path="core/etc/rc.d/$filename"
            ;;
            
        etc/init.d/*)
            # OpenRC init scripts
            filename=$(basename "$deployed_path")
            if echo "$filename" | grep -q "ipcop-"; then
                source_path="core/etc/init.d/$filename"
            elif [ "$service" != "core" ]; then
                source_path="services/$service/etc/init.d/$filename"
            else
                source_path="core/etc/init.d/$filename"
            fi
            ;;
            
        etc/sysctl.conf|etc/sysctlpostinit.conf|etc/isdn-card-list|etc/nic-modules-list)
            filename=$(basename "$deployed_path")
            source_path="core/etc/$filename"
            ;;

        var/ipcop/*)
            # Runtime Settings from Deployed System - Map directly to source var/ipcop structure
            
            # Remove var/ipcop/ prefix
            rel_path="${deployed_path#var/ipcop/}"
            
            if [ "$service" = "core" ]; then
                 source_path="core/var/ipcop/$rel_path"
            else
                 # Service specific settings go to service dir
                 source_path="services/$service/var/ipcop/$rel_path"
            fi
            ;;
            
        var/www/ipcop/cgi-bin/*)
            # CGI scripts
            filename=$(basename "$deployed_path")
            if [ "$service" = "core" ]; then
                source_path="core/html/cgi-bin/$filename"
            else
                source_path="services/$service/html/cgi-bin/$filename"
            fi
            ;;
            
        var/www/ipcop/html/*)
            # HTML/images/includes
            rel_path="${deployed_path#var/www/ipcop/html/}"
            source_path="core/html/$rel_path"
            ;;
            
        *)
            # Skip - not part of source tree (runtime only)
            return 1
            ;;
    esac
    
    echo "$source_path"
    return 0
}

# Parse output file and copy files
echo "Processing files from $OUTPUT_FILE..."
line_count=0
copied_count=0
skipped_count=0

while IFS= read -r line; do
    line_count=$((line_count + 1))
    
    # Parse the line: perms owner group timestamp path
    # Extract just the path (last field)
    deployed_path=$(echo "$line" | awk '{print $NF}')
    
    # Skip if it's a directory entry
    echo "$line" | grep -q '^d' && continue
    
    # Skip symlinks (we'll handle them separately if needed)
    echo "$line" | grep -q '^l' && continue
    
    # Determine service
    service=$(get_service "$deployed_path")
    
    # Map to source path
    source_path=$(map_to_source "$deployed_path" "$service") || {
        skipped_count=$((skipped_count + 1))
        continue
    }
    
    # Full paths
    full_deployed="/$deployed_path"
    full_source="$DEST_BASE/$source_path"
    
    # Create destination directory
    source_dir=$(dirname "$full_source")
    mkdir -p "$source_dir"
    
    # Determine if we should copy source code instead of binary
    if echo "$source_path" | grep -q '/progs/.*\.c$'; then
        # This is a compiled program - copy source instead
        prog_name=$(basename "$source_path" .c)
        
        # Try to find source in legacy_src/progs
        src_file="$SRC_BASE/progs/${prog_name}.c"
        if [ -f "$src_file" ]; then
            cp "$src_file" "$full_source"
            copied_count=$((copied_count + 1))
            echo "  [SRC] $source_path"
        else
            echo "  [WARN] Source not found for $prog_name"
            skipped_count=$((skipped_count + 1))
        fi
    elif [ -f "$full_deployed" ]; then
        # Regular file - just copy
        cp -p "$full_deployed" "$full_source"
        copied_count=$((copied_count + 1))
        echo "  [COPY] $source_path"
    else
        skipped_count=$((skipped_count + 1))
    fi
    
    # Progress indicator every 50 lines
    if [ $((line_count % 50)) -eq 0 ]; then
        echo "  ... processed $line_count lines"
    fi
done < "$OUTPUT_FILE"

echo ""
echo "=== Summary ==="
echo "Total lines processed: $line_count"
echo "Files copied: $copied_count"
echo "Files skipped: $skipped_count"
echo ""
echo "Source tree created at: $DEST_BASE"
echo ""

# --- 6. Build Isolation & Makefiles ---
echo "Preparing build environments..."

# --- 6. Build Isolation & Makefiles ---
echo "Preparing build environments..."

# Define locations of common source files (relative to SRC_BASE)
# We use legacy_src (SRC_BASE) as the source of truth for dependencies.

# Assuming script is in alpine/, legacy_src is in root
SRC_BASE="$(dirname "$0")/../legacy_src"
SRC_PROGS="$SRC_BASE/progs"
SRC_INSTALLER="$SRC_BASE/installer"

# Copy installer sources to core (needed for headers and setup binary)
echo "  [COPY] Copying installer sources..."
mkdir -p "$DEST_BASE/core/installer"
cp -r "$SRC_INSTALLER/"* "$DEST_BASE/core/installer/" 2>/dev/null || true

# Function to setup progs directory
setup_progs_dir() {
    target_dir="$1"
    if [ -d "$target_dir" ]; then
        echo "  Configuring $target_dir..."
        # Copy common files
        cp "$SRC_PROGS/setuid.c" "$target_dir/" 2>/dev/null || echo "WARN: setuid.c missing"
        cp "$SRC_PROGS/setuid.h" "$target_dir/" 2>/dev/null || echo "WARN: setuid.h missing"
        cp "$SRC_INSTALLER/helper.c" "$target_dir/" 2>/dev/null || echo "WARN: helper.c missing"
        cp "$SRC_INSTALLER/helper_backup.c" "$target_dir/" 2>/dev/null || echo "WARN: helper_backup.c missing"
        cp "$SRC_INSTALLER/common.h" "$target_dir/" 2>/dev/null || echo "WARN: common.h missing"
        cp "$SRC_INSTALLER/common_backup.h" "$target_dir/" 2>/dev/null || echo "WARN: common_backup.h missing"
        
        # Generate Makefile
cat > "$target_dir/Makefile" <<EOF
CC=gcc
CFLAGS=-D_GNU_SOURCE -I. -Wall -Wno-format-truncation -Wno-main -Wno-address -Wno-unused-but-set-variable -Wformat-overflow=0 -Wno-logical-not-parentheses -DNAME='"IPCop"' -DSNAME='"ipcop"' -DVERSION='"2.2.0"' -DKVER='"2.2.0"'
OBJLIBS=setuid.o helper.o helper_backup.o

# Find all .c files that are NOT the helpers (and avoid overwriting helper.c/setuid.c logic)
# We want to build specific binaries.
# List of standard progs that might be here (dynamically found)
SRCS=\$(filter-out setuid.c helper.c helper_backup.c, \$(wildcard *.c))
PROGS=\$(SRCS:.c=)

all: \$(PROGS)

# Compile helpers
setuid.o: setuid.c setuid.h
	\$(CC) \$(CFLAGS) -c setuid.c -o setuid.o

helper.o: helper.c common.h
	\$(CC) \$(CFLAGS) -c helper.c -o helper.o

helper_backup.o: helper_backup.c common_backup.h
	\$(CC) \$(CFLAGS) -c helper_backup.c -o helper_backup.o

# Compile each program
%: %.c \$(OBJLIBS)
	\$(CC) \$(CFLAGS) \$< \$(OBJLIBS) -o \$@ -lcrypt

clean:
	rm -f \$(PROGS) *.o
EOF
    fi
}

# Setup Core Progs
setup_progs_dir "$DEST_BASE/core/progs"


# Setup Service Progs
for svc_dir in "$DEST_BASE"/services/*; do
    if [ -d "$svc_dir/progs" ]; then
        setup_progs_dir "$svc_dir/progs"
    fi
done

echo ""
echo "=== Summary ==="
echo "Total lines processed: $line_count"
echo "Files copied: $copied_count"
echo "Files skipped: $skipped_count"
echo "Source tree created at: $DEST_BASE"

