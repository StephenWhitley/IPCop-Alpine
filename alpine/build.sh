#!/bin/sh
# vim: set tabstop=4 shiftwidth=4 noexpandtab:
#
# build.sh - Build script for IPCop Modular (Alpine)
#
# This script builds the new modular IPCop packages from the ipcop-alpine source tree.
#

set -e  # Exit on any error

# ============================================================================
# CONFIGURATION
# ============================================================================

# Project information
NAME="IPCop"
SNAME="ipcop"
VERSION="2.2.0-modular1"
MACHINE="x86_64"

# Directories
# Script is in ipcop-alpine/alpine/
BASEDIR="$(cd "$(dirname "$0")/.." && pwd)"
ALPINE_DIR="${BASEDIR}/alpine"
BUILD_DIR="${ALPINE_DIR}/build"
PACKAGES_DIR="${ALPINE_DIR}/packages"
APKBUILDS_DIR="${ALPINE_DIR}/apkbuilds"
SRC_DIR="${BASEDIR}/source"

CACHE_DIR="${BASEDIR}/cache"

# APK build settings
PACKAGER="IPCop Development Team"
MAINTAINER="ipcop-dev@lists.sourceforge.net"

# Output
LOG_DIR="${ALPINE_DIR}/log"
LOGFILE="${LOG_DIR}/build_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
BOLD="\033[1;39m"
DONE="\033[0;32m"
FAIL="\033[0;31m"
WARN="\033[0;35m"
INFO="\033[0;36m"
NORMAL="\033[0;39m"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

msg() {
	local color="$1"
	shift
	echo -e "${color}*** $@${NORMAL}"
}

msg_info() { msg "${INFO}" "$@"; }
msg_done() { msg "${DONE}" "$@"; }
msg_warn() { msg "${WARN}" "$@"; }
msg_fail() { msg "${FAIL}" "$@"; }

log_msg() {
	echo "[$(date +'%Y-%m-%d %H:%M:%S')] $@" | tee -a "${LOGFILE}"
}

die() {
	msg_fail "$@"
	log_msg "ERROR: $@"
	exit 1
}

check_alpine() {
	if [ ! -f /etc/alpine-release ]; then
		die "This script must be run on Alpine Linux"
	fi
	msg_info "Running on Alpine Linux $(cat /etc/alpine-release)"
}

check_prerequisites() {
	msg_info "Checking prerequisites..."
	local missing=""
	for pkg in abuild alpine-sdk git; do
		if ! apk info -e "$pkg" >/dev/null 2>&1; then
			missing="$missing $pkg"
		fi
	done
	
	if [ -n "$missing" ]; then
		msg_warn "Missing packages:$missing"
		die "Please run ./setup.sh to install build dependencies"
	fi
	
	if ! groups | grep -q abuild; then
		msg_warn "User not in 'abuild' group"
		die "Please add your user to 'abuild' group (run setup.sh)"
	fi
	
	msg_done "Prerequisites OK"
}

setup_directories() {
	msg_info "Setting up build directories..."
	mkdir -p "${BUILD_DIR}"
	mkdir -p "${PACKAGES_DIR}"
	mkdir -p "${LOG_DIR}"
	mkdir -p "${CACHE_DIR}"
	msg_done "Directories created"
}

cleanup_old_packages() {
	msg_info "Cleaning old packages..."
	
	# Clean output directory
	local pkg_dir="${PACKAGES_DIR}/x86_64"
	if [ -d "$pkg_dir" ]; then
		rm -f "$pkg_dir"/*.apk
		rm -f "$pkg_dir"/APKINDEX.tar.gz
	fi
	
	# Clean abuild cache directory (where stale packages may persist)
	local abuild_cache="$HOME/packages/apkbuilds/x86_64"
	if [ -d "$abuild_cache" ]; then
		msg_info "Cleaning abuild cache: $abuild_cache"
		rm -f "$abuild_cache"/ipcop-*.apk
		rm -f "$abuild_cache"/APKINDEX.tar.gz
	fi
	
	# Update repo index after cleanup
	sudo apk update --allow-untrusted 2>/dev/null || true
	msg_done "Old packages cleaned"
}

sanitize_line_endings() {
	msg_info "Sanitizing line endings (CRLF -> LF)..."
	if ! command -v dos2unix >/dev/null 2>&1; then
		msg_warn "dos2unix not found, skipping sanitation (ensure files are LF)"
		return
	fi
	
	find "${APKBUILDS_DIR}" -name "APKBUILD" -exec dos2unix {} +
	find "${APKBUILDS_DIR}" -name "*.pre-install" -exec dos2unix {} +
	find "${APKBUILDS_DIR}" -name "*.post-install" -exec dos2unix {} +
	
    # Sanitize source tree
    find "${SRC_DIR}" -type f \( -name "*.pl" -o -name "*.sh" -o -name "*.cgi" \) -exec dos2unix {} +
	msg_done "Sanitized"
}

init_local_repo() {
	msg_info "Initializing local IPCop repository..."
	local repo_dir="$HOME/packages/ipcop-modular/x86_64"
	mkdir -p "$repo_dir"
	
	if ! grep -q "$HOME/packages/ipcop-modular" /etc/apk/repositories 2>/dev/null; then
		msg_info "Adding local repository to /etc/apk/repositories"
		echo "$HOME/packages/ipcop-modular" | sudo tee -a /etc/apk/repositories >/dev/null
	fi
    
    # Trust keys if needed matches setup.sh logic
    if [ -d "$HOME/.abuild" ] && [ -n "$(find "$HOME/.abuild" -name "*.rsa.pub" | head -n 1)" ]; then
         sudo cp "$HOME/.abuild/"*.rsa.pub /etc/apk/keys/ 2>/dev/null || true
    fi
	
	sudo apk update --allow-untrusted
	msg_done "Local repository initialized"
}

build_package() {
	local pkg_name="$1"
	local apkbuild_dir="${APKBUILDS_DIR}/${pkg_name}"
	
	if [ ! -d "$apkbuild_dir" ]; then
		msg_warn "APKBUILD for ${pkg_name} not found, skipping..."
		return 1
	fi

	if [ -d "$apkbuild_dir/src" ]; then
		msg_warn "APKBUILD for ${pkg_name} has src directory, skipping..."
		return 1
	fi

	if [ -d "$apkbuild_dir/tmp" ]; then
		msg_warn "APKBUILD for ${pkg_name} has tmp directory, skipping..."
		return 1
	fi
	
	msg_info "Building package: ${pkg_name}"
	cd "$apkbuild_dir"
	
    # Clean and Build
	abuild -F clean || true
	if ! abuild -F -f -r; then
		msg_fail "Failed to build ${pkg_name}"
		cd "${BASEDIR}"
		return 1
	fi
	
	# Copy to output
	local src_dir=~/packages/ipcop-alpine/x86_64
    # Note: abuild might use different path depending on conf. 
    # Usually ~/packages/[dirname]/x86_64 or similar. 
    # With default abuild.conf it is ~/packages/[pkgname]?? No, usually [repo]/[arch].
    # We will assume standard ~/packages/alpine/x86_64 (since ipcop-alpine/alpine is the path?)
    # CHECK: APKBUILD usually doesn't define repo name. It defaults to 'apkbuilds' folder name or similar?
    # Actually abuild uses REPODEST from abuild.conf.
    # We will assume the user has REPODEST set appropriately or we find it.
    
    # We will try to find where it went.
    local found_dir=$(find ~/packages -name "${pkg_name}-*.apk" -exec dirname {} \; | head -n 1)
    if [ -z "$found_dir" ]; then
         # Fallback search
         found_dir=~/packages/apkbuilds/x86_64
    fi
    
	local dest_dir="${PACKAGES_DIR}/x86_64"
	mkdir -p "${dest_dir}"
    
    if [ -n "$found_dir" ] && [ -d "$found_dir" ]; then
        cp -v "$found_dir"/${pkg_name}-*.apk "${dest_dir}/"
    else
        msg_fail "Could not locate built apk for ${pkg_name}"
        return 1
    fi

	msg_done "Built: ${pkg_name}"
	cd "${BASEDIR}"
}

build_all_packages() {
	msg_info "Building all IPCop Modular packages..."
    
    # Order matters
    # ipcop-lang (depended by core? No, core depends on lang usually or vice versa. core has 'ipcop-lang' in depends)
    # ipcop-core (base)
    # services...
    
	local packages="ipcop-lang ipcop-core ipcop-installer ipcop-squid ipcop-e2guardian ipcop-suricata ipcop-wireguard ipcop-openvpn"
    
    # Temporary disable suricata update if needed (omitted for brevity)
    
	for pkg in $packages; do
		build_package "$pkg" || die "Failed to build $pkg"
	done
	
	# Generate APKINDEX for the output directory
	msg_info "Generating APKINDEX for distribution..."
	local dest_dir="${PACKAGES_DIR}/x86_64"
	if command -v apk >/dev/null 2>&1; then
		cd "$dest_dir"
		# Generate index from within x86_64 directory so APK can find the files
		# Use -x to include checksums in standard format (C: before P:)
		apk index --allow-untrusted --rewrite-arch noarch -o APKINDEX.tar.gz *.apk 2>/dev/null || \
			apk index --allow-untrusted -o APKINDEX.tar.gz *.apk 2>/dev/null || true
		# Sign if key available
		if [ -f "$HOME/.abuild/"*.rsa ]; then
			abuild-sign -k "$HOME/.abuild/"*.rsa APKINDEX.tar.gz 2>/dev/null || true
		fi
		cd "${BASEDIR}"
	fi
	
	msg_done "All packages built successfully"
	msg_info "Packages ready in: ${dest_dir}"
}

# MAIN
main() {
	mkdir -p "${LOG_DIR}"
	check_alpine
	
    case "$1" in
        clean)
            cleanup_old_packages
            ;;
        all|"")
            check_prerequisites
            setup_directories
            sanitize_line_endings
            cleanup_old_packages
            build_all_packages
            ;;
        *)
            # Specific package build
            check_prerequisites
            setup_directories
            sanitize_line_endings
            # Ensure repo is init so deps work
            init_local_repo
            build_package "$1"
            ;;
    esac
}

main "$@"

build_package ipcop-progs
