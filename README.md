# IPCop on Alpine (Modular)

This directory contains the source code for the modular, Alpine Linux-based version of IPCop. Unlike the legacy monolithic build, this structure is designed to be effectively modular, separating the Core system from optional Services.

## Directory Structure

| Path | Description |
| :--- | :--- |
| **`html/cgi-bin/`** | **Web Interface Scripts.** Divided by service (e.g., `core`, `squid`, `openvpn`). |
| **`config/`** | **Configuration Defaults.** Contains both daemon configs (e.g., `squid.conf`) and IPCop defaults (e.g., `settings`). |
| **`src/`** | **Source Code.** |
| &nbsp;&nbsp;`progs/` | Compiled C binaries (legacy helpers). |
| &nbsp;&nbsp;`lib/` | Shared Perl libraries. |
| &nbsp;&nbsp;`scripts/` | Helper scripts (Perl/Shell). |
| &nbsp;&nbsp;`init/` | **Init Scripts.** OpenRC scripts, organized by service. |
| **`lang/`** | **Localization.** standard `.po` files. |
| **`alpine/`** | **Build System.** Contains `APKBUILD` definitions and build scripts. |

## Build Instructions

Building is handled by the scripts in `alpine/`. You must run these on an Alpine Linux system (Standard or **BusyBox** environment).
> **Note:** The scripts are optimized for BusyBox (e.g., avoiding GNU-specific flags like `dos2unix -q` or `find -quit`).

### 1. One-Time Setup
Prepare your environment (install dependencies, generate keys):
```bash
./alpine/setup.sh
```

### 2. Build Packages
Build all packages:
```bash
./alpine/build.sh
```
Or build a specific package:
```bash
./alpine/build.sh ipcop-core
./alpine/build.sh ipcop-squid
```
*Artifacts will be placed in `alpine/packages/`.*

### 3. Install
Install the built packages to the local system:
```bash
./alpine/install.sh
```

## Development Guidelines

### Adding a New Service
1.  **CGI:** Create a directory `html/cgi-bin/[service]`.
2.  **Config:** Create `config/[service]` for defaults.
3.  **Init:** Place OpenRC scripts in `src/init/[service]`.
4.  **Package:** Create `alpine/apkbuilds/ipcop-[service]/APKBUILD`.
    -   Must depend on `ipcop-core`.
    -   Must install files to correct locations (WebUI -> `/var/www/ipcop/...`).

### Permission Standards (Critical)
Alpine and Lighttpd are strict about permissions. Adhere to these rules in your `post-install` scripts:

*   **CGI Scripts:** `root:root` `0755`
*   **Web-Writable Data:** `root:lighttpd` `2770` (SGID is **Required**)
    *   *Why?* Files created by root helpers must inherit the `lighttpd` group so the WebUI can read/delete them.
*   **Service Configs:** `root:[service]` `0640` (e.g., `root:squid` for passwords).
