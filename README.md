# IPCop on Alpine (Modular)

A modern, modular reimplementation of IPCop firewall as Alpine Linux packages.

> **Acknowledgements:** This project builds upon the excellent work of the original [IPCop project](https://www.ipcop.org/) team. We also acknowledge [IPFire](https://www.ipfire.org/), an actively maintained community-driven firewall distribution that evolved from IPCop and continues to be developed with regular updates and security patches.

---

## Project Status

### Current State

✅ **Architectural Migration: Complete**  
The fundamental shift from monolithic ISO to modular APK packages is complete. The build system, package structure, and deployment methodology are operational.

⚠️ **Testing Status: Pre-Alpha**  
Most packages have achieved **deployment and smoke testing** on development systems. Core functionality (firewall rules, web interface, networking) is operational. However:

- **Comprehensive testing is ongoing** - The entire implementation (build process, source organization, and deployment) requires extensive validation
- **Regressions are commonplace** - This is an active porting effort and breaking changes can occur
- **Not recommended for production** - Use in lab/development environments only at this time

### Known Limitations

📦 **Language Packaging**  
The localization system (`ipcop-lang`) remains **monolithic** - all language files are bundled into a single package. The modular packaging approach has not yet been applied to split languages into individual packages (e.g., `ipcop-lang-en`, `ipcop-lang-de`).

🎨 **Web Interface Modernization**  
The web UI remains **primarily CGI-based** to maintain stability during the porting process:
- **JavaScript enhancements** are being explored for specific features (e.g., interactive charts using modern charting libraries)
- **Core CGI framework maintained** - The Perl CGI architecture is preserved to avoid introducing reliability issues and potential vulnerabilities during the architectural transition
- **Incremental improvements** - UI enhancements are introduced carefully and selectively

### Development Philosophy

Our current focus prioritizes:
1. **Stability over features** - Ensure the core port is solid before adding enhancements
2. **Testing and validation** - Identify and fix regressions from the architectural shift
3. **Incremental modernization** - Improve components (like charts) without wholesale rewrites
4. **Security-conscious porting** - Avoid introducing new attack surfaces during migration

> **For Developers:** Expect breaking changes. Test thoroughly. Report issues. This is an active development project.

---

## Project Overview

### Motivation

**IPCop-Alpine** represents a fundamental architectural shift from the original IPCop distribution model. Where IPCop (and its derivative IPFire) were designed as **monolithic, pre-integrated ISO packages** with coupled Linux distributions, IPCop-Alpine adopts a **layered, package-based approach** that separates the firewall functionality from the underlying operating system.

#### From Monolithic to Modular

**Traditional IPCop/IPFire Approach:**
- Complete Linux distribution built from scratch
- Firewall and OS tightly integrated into a single ISO
- Updates require rebuilding and redistributing entire system
- Limited flexibility for adding third-party packages
- Custom kernel and system configuration

**IPCop-Alpine Approach:**
- IPCop functionality packaged as Alpine Linux APK packages
- Leverage Alpine's existing infrastructure and security updates
- Independent upgrade path for OS and firewall components
- Standard package manager integration
- Add additional Alpine packages as needed

This architectural change introduces **integration risks** but provides significant advantages:

✅ **Independent Updates** - OS and firewall components upgrade separately  
✅ **Package Ecosystem** - Full access to Alpine's package repository  
✅ **Reduced Maintenance** - Alpine team handles OS security patches  
✅ **Modern Foundation** - Built on musl libc, BusyBox, and OpenRC  
✅ **Smaller Footprint** - Minimal base system with modular services  

### Key Differences from IPFire

While IPFire continued the ISO approach with enhanced features, IPCop-Alpine diverges by:

- **Package-based distribution** instead of ISO-based installation
- **Alpine Linux foundation** instead of custom Linux build
- **Service modularity** as separate installable packages
- **Modern dependency management** via APK package system
- **Simplified development** with standard Alpine build tools

---

## Architecture

### Source Structure Improvements

The source tree has been **reorganized to mirror the runtime deployment structure and to seperate the core IPCop system from the optional services**:

```
source/
├── core/                    # Core IPCop system
│   ├── etc/                 # System configuration files
│   │   ├── collectd.conf    # Metrics collection
│   │   ├── lighttpd.conf    # Web server
│   │   ├── rsyslog.conf     # System logging
│   │   ├── init.d/          # Init scripts
│   │   └── rc.d/            # Runlevel scripts
│   ├── html/                # Web root
│   │   ├── cgi-bin/         # Core CGI scripts
│   │   ├── images/          # Web assets
│   │   └── include/         # Shared HTML includes
│   ├── var/ipcop/           # Runtime data structure
│   │   ├── backup/          # Backup configuration
│   │   ├── dhcp/            # DHCP settings
│   │   ├── firewall/        # Firewall rules
│   │   ├── red/             # WAN interface config
│   │   └── ...              # Other runtime data
│   ├── lib/                 # Perl libraries
│   │   ├── general-functions.pl
│   │   ├── header.pl
│   │   ├── menu.pl
│   │   └── ...              # Core libraries
│   ├── progs/               # SUID C helpers
│   │   ├── setfwrules.c     # Firewall rule setter
│   │   ├── red.c            # WAN interface control
│   │   └── ...              # Other setuid programs
│   ├── scripts/             # System scripts
│   └── installer/           # Setup wizard
│
└── services/                # Optional service packages
    ├── squid/               # Web proxy
    │   ├── html/cgi-bin/    # Proxy WebUI
    │   ├── var/ipcop/proxy/ # Proxy configuration
    │   ├── progs/           # Proxy helpers
    │   └── scripts/         # Proxy scripts
    ├── e2guardian/          # Content filter
    ├── openvpn/             # OpenVPN service
    ├── wireguard/           # WireGuard VPN
    └── suricata/            # IDS/IPS
```

**Benefits:**
- **Each directory mirrors deployment paths** - `source/core/etc/` → `/etc/`, `source/core/var/ipcop/` → `/var/ipcop/`
- **Services are self-contained** - All files for a service in one directory
- **Build-time simplicity** - APKBUILDs copy entire subtrees to their destinations
- **Clear ownership** - Easy to see what files belong to which package

### Package Architecture

IPCop is distributed as **modular APK packages**:

| Package | Description |
|---------|-------------|
| `ipcop-core` | Base system, web interface framework, networking, firewall rules |
| `ipcop-lang` | Localization files for all supported languages |
| `ipcop-installer` | First-time setup wizard (`setup-ipcop`) |
| `ipcop-squid` | HTTP/HTTPS proxy (Squid) |
| `ipcop-e2guardian` | Content filtering and URL filtering |
| `ipcop-suricata` | Intrusion Detection/Prevention System (IDS/IPS) |
| `ipcop-openvpn` | OpenVPN server and client configuration |
| `ipcop-wireguard` | WireGuard VPN (modern alternative) |

> **Note:** Services are **optional** and can be installed independently. Only `ipcop-core` and `ipcop-lang` are required.

---

## Notable Changes

IPCop-Alpine introduces several significant improvements and modernizations:

### 🔄 Services as Packages
- Each service (Squid, OpenVPN, Suricata) is a separate APK package
- Install only the services you need
- Independent service updates without touching core system

### 🛡️ Suricata IDS/IPS (NEW)
- Modern intrusion detection and prevention system
- Replaces aging Snort infrastructure
- Active rule updates and threat intelligence integration
- WebUI for rule management and alert monitoring

### 🚀 WireGuard VPN (NEW)
- Modern, high-performance VPN protocol
- Simpler configuration than OpenVPN
- Better performance on low-power hardware
- WebUI for peer management

### 🌐 E2Guardian Content Filter
- **Replaces SquidGuard** (no longer maintained)
- Modern content filtering engine
- Active development and security updates
- Compatible with existing filtering requirements
- Phrase filtering, PICS rating support, AV integration

### 📁 Source Structure Simplified
- Flatter directory hierarchy
- Matches runtime environment layout
- Easier navigation and development
- Clear separation of concerns

### 🔧 Modern Build System
- Standard Alpine `abuild` toolchain
- APK package format with dependency management
- Automated signing and repository indexing
- Clean separation of build and deployment environments

### ⚡ Performance Improvements
- Lightweight musl libc instead of glibc
- BusyBox utilities reduce memory footprint
- OpenRC init system (faster boot)
- Smaller overall system size

---

## Setup Instructions

### Prerequisites

You need **two Alpine Linux systems** (can be VMs):

1. **Build Environment** - Where you compile packages
2. **Deployment Environment** - Where IPCop runs as a firewall

> Both environments start with a fresh Alpine Linux installation.

---

## Build Environment Setup

The build environment is where you compile IPCop packages. This should **not** be your production firewall.

### Step 1: Install Alpine Linux

1. Download Alpine Linux (Standard or Virtual ISO)
2. Boot and run the standard Alpine setup:
   ```bash
   setup-alpine
   ```
3. Configure networking, disk, SSH, and basic system settings
4. Reboot into your installed Alpine system

### Step 2: Create Builder User

Create a non-root user for building packages:

```bash
# As root, create a builder user
adduser builder

# Add builder to wheel group (for sudo)
addgroup builder wheel

# Enable sudo for wheel group (edit /etc/sudoers)
apk add sudo
echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers

# Switch to builder user
su - builder
```

> **Important:** Do not build packages as root. Use a dedicated builder user.

### Step 3: Clone Repository

```bash
# As builder user
apk add git
git clone https://github.com/yourusername/IPCop-Alpine.git
cd IPCop-Alpine
```

### Step 4: Run Build Setup

```bash
cd IPCop-Alpine
./alpine/setup-build.sh
```

This script will:
- Install `alpine-sdk`, `abuild`, and build dependencies
- Add user to `abuild` group
- Generate package signing keys (`~/.abuild/*.rsa`)
- Configure `abuild.conf`

**After setup completes, log out and back in** for group changes to take effect.

### Step 5: Build Packages

```bash
cd IPCop-Alpine
./alpine/build.sh
```

This builds all IPCop packages. Artifacts will be in:
```
alpine/packages/x86_64/
├── ipcop-core-2.2.0-r3.apk
├── ipcop-lang-2.2.0-r2.apk
├── ipcop-squid-2.2.0-r2.apk
├── ...
└── APKINDEX.tar.gz
```

**To build a single package:**
```bash
./alpine/build.sh ipcop-core
```

---

## Deployment Environment Setup

The deployment environment is your **production firewall** where IPCop will run.

### Step 1: Install Alpine Linux

Same as build environment:
1. Download Alpine Linux
2. Run `setup-alpine`
3. Configure network interfaces for your firewall zones (RED, GREEN, BLUE, ORANGE)
4. Reboot

### Step 2: Prepare System for IPCop

Run the deployment preparation script:

```bash
./alpine/setup-deploy.sh
```

This script (run as root) will:
- Install system dependencies (Perl, lighttpd, iptables, etc.)
- Install CPAN modules required by IPCop
- Configure system services (fcron, rsyslog, lighttpd)
- Disable conflicting services
- Create iptables compatibility symlinks

### Step 3: Transfer Packages

Copy the built APK packages from your build environment:

```bash
# On build environment
scp alpine/packages/x86_64/*.apk root@firewall:/tmp/

# Or use a USB drive, shared folder, etc.
```

### Step 4: Install IPCop Packages

On the deployment system:

```bash
cd /path/to/packages
./alpine/install-ipcop.sh
```

This will:
- Install all IPCop packages from local directory
- Configure package repositories
- Set up initial file structure under `/var/ipcop/`

### Step 5: Run IPCop Setup

Run the first-time setup wizard:

```bash
setup-ipcop
```

This interactive script will:
- Configure network zones (RED, GREEN, BLUE, ORANGE)
- Set up admin passwords
- Configure firewall rules
- Initialize services
- Generate SSL certificates

### Step 6: Access Web Interface

Once setup completes:

1. Open browser to `https://<GREEN_IP>:8443`
2. Log in with admin credentials set during setup
3. Complete configuration via WebUI

---

## Directory Structure

### Source Tree (Development)

```
IPCop-Alpine/
├── source/
│   ├── core/                # Core IPCop package
│   │   ├── etc/             # System configs (lighttpd, rsyslog, collectd)
│   │   ├── html/            # Web root and CGI scripts
│   │   ├── var/ipcop/       # Runtime data templates
│   │   ├── lib/             # Perl libraries
│   │   ├── progs/           # SUID C helpers
│   │   ├── scripts/         # System scripts
│   │   └── installer/       # Setup wizard
│   └── services/            # Optional service packages
│       ├── squid/           # Web proxy
│       ├── e2guardian/      # Content filter
│       ├── openvpn/         # OpenVPN
│       ├── wireguard/       # WireGuard VPN
│       └── suricata/        # IDS/IPS
├── lang/                    # Localization files (.po)
├── alpine/
│   ├── apkbuilds/           # Package definitions (APKBUILD)
│   ├── build.sh             # Build orchestrator
│   ├── setup-build.sh       # Build environment setup
│   ├── setup-deploy.sh      # Deployment preparation
│   └── install-ipcop.sh     # Package installation
└── README.md
```

### Runtime Structure (Deployed System)

```
/var/ipcop/                  # IPCop runtime data
├── backup/                  # Backup sets
├── dhcp/                    # DHCP leases
├── firewall/                # Firewall rules (settings, input, outgoing)
├── proxy/                   # Proxy configuration
├── red/                     # RED interface state (iface, local, etc.)
├── suricata/                # IDS rules and logs
└── ...

/home/httpd/                 # Web interface root
├── cgi-bin/                 # CGI scripts (core, services)
└── html/                    # Static web assets

/usr/share/ipcop/            # Installed defaults
└── defaults/                # Factory configuration defaults

/var/log/                    # System logs
├── ipcop/                   # IPCop-specific logs
├── squid/                   # Proxy logs
└── suricata/                # IDS logs
```

---

## Development Guidelines

### Adding a New Service

1. **Create service directory structure:**
   ```bash
   mkdir -p source/html/cgi-bin/myservice
   mkdir -p source/config/myservice
   mkdir -p source/src/init/myservice
   ```

2. **Create APKBUILD:**
   ```bash
   cd alpine/apkbuilds
   mkdir ipcop-myservice
   vim ipcop-myservice/APKBUILD
   ```

3. **Define dependencies:**
   ```bash
   depends="ipcop-core mydaemon"
   ```

4. **Add install scripts:**
   - `ipcop-myservice.pre-install` - Pre-installation tasks
   - `ipcop-myservice.post-install` - Post-installation configuration

5. **Build and test:**
   ```bash
   ./alpine/build.sh ipcop-myservice
   ```

### Permission Standards (Critical)

Alpine and Lighttpd enforce strict permissions. Follow these rules:

| File Type | Owner | Group | Mode | Reason |
|-----------|-------|-------|------|--------|
| CGI scripts | `root` | `root` | `0755` | Prevent tampering |
| Web-writable data | `root` | `lighttpd` | `2770` | SGID ensures lighttpd group inheritance |
| Service configs | `root` | `service` | `0640` | Protect sensitive passwords |
| Log directories | `service` | `lighttpd` | `0755` | WebUI read access |

**Why SGID (2770)?**  
Files created by root helpers inherit the `lighttpd` group, allowing WebUI to read/delete them.

### Code Style

- **Shell scripts:** POSIX-compliant, avoid Bash-isms
- **Perl scripts:** Use strict/warnings, `IPCop::Header`
- **Line endings:** LF only (enforced by `.gitattributes`)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following development guidelines
4. Test in a VM environment
5. Submit pull request

---

## License

IPCop is licensed under the GNU General Public License v2.0.  
See `LICENSE` file for details.

---

## Resources

### Related Projects

- **[IPCop Project](https://www.ipcop.org/)** - The original IPCop firewall project that inspired this work. IPCop pioneered the user-friendly Linux firewall distribution concept, providing enterprise-class security features with a simple web interface.

- **[IPFire](https://www.ipfire.org/)** - A community-maintained firewall distribution that forked from IPCop and continues active development. IPFire has evolved significantly with regular security updates, modern features, and an active developer community. If you need a production-ready, actively maintained monolithic firewall distribution, IPFire is an excellent choice.

- **[Alpine Linux](https://www.alpinelinux.org/)** - The lightweight, security-oriented Linux distribution that serves as the foundation for IPCop-Alpine. Alpine's use of musl libc, BusyBox, and apk package manager makes it ideal for embedded and security-focused applications.

### Key Differences

**IPCop-Alpine** vs. **IPFire**:
- IPCop-Alpine: Package-based, layered architecture, independent OS updates
- IPFire: Monolithic ISO, tightly integrated system, comprehensive feature set, active community

**When to use IPCop-Alpine:**
- You want to leverage Alpine's package ecosystem
- You need independent OS and firewall updates
- You prefer modular service installation
- You're comfortable with Alpine Linux

**When to use IPFire:**
- You want a complete, tested, production-ready solution
- You need active community support and regular updates
- You prefer an integrated system with comprehensive documentation
- You want a turnkey firewall appliance

---

**Last Updated:** January 2026  
**Version:** 2.2.0-modular  
**License:** GNU GPL v2.0
