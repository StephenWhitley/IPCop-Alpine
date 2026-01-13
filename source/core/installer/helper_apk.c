/*
 * helper_apk.c: APK package management helper functions
 *
 * This file contains helper functions for managing APK packages during
 * IPCop installation on Alpine Linux.
 *
 * Functions include:
 * - APK repository configuration
 * - Package installation from bundled and online sources
 * - Dependency resolution
 * - Error handling
 *
 * Copyright (C) 2024 IPCop Development Team
 * Licensed under GPL v2
 *
 * $Id: helper_apk.c $
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <errno.h>
#include "common.h"
#include "common_newt.h"
#include "helper_apk.h"

/* APK database location */
#define APK_DB_PATH "/lib/apk/db"
#define APK_INSTALLED_PATH "/var/ipcop/installer/apk-installed"

/* Repository paths */
#define BUNDLED_REPO_MOUNT "/mnt/ipcop-repo"
#define BUNDLED_REPO_PATH "/cdrom/alpine/packages"
#define APK_REPOS_FILE "/etc/apk/repositories"
#define APK_WORLD_FILE "/etc/apk/world"

/* APK command path */
#define APK_CMD "/sbin/apk"

/*
 * Initialize APK database in the target system
 */
int apk_init_db(const char *root_path)
{
    char command[STRING_SIZE];
    
    fprintf(flog, "Initializing APK database at %s\n", root_path);
    
    /* Create necessary directories */
    snprintf(command, STRING_SIZE, "mkdir -p %s/etc/apk", root_path);
    if (mysystem(command)) {
        fprintf(flog, "Failed to create /etc/apk directory\n");
        return FAILURE;
    }
    
    snprintf(command, STRING_SIZE, "mkdir -p %s/var/cache/apk", root_path);
    if (mysystem(command)) {
        fprintf(flog, "Failed to create APK cache directory\n");
        return FAILURE;
    }
    
    /* Initialize APK database */
    snprintf(command, STRING_SIZE, "%s --root %s --initdb add", APK_CMD, root_path);
    if (mysystem(command)) {
        fprintf(flog, "Failed to initialize APK database\n");
        return FAILURE;
    }
    
    fprintf(flog, "APK database initialized successfully\n");
    return SUCCESS;
}

/*
 * Mount bundled APK repository from installation media
 */
int apk_mount_bundled_repo(void)
{
    char command[STRING_SIZE];
    struct stat st;
    
    fprintf(flog, "Mounting bundled IPCop repository\n");
    
    /* Create mount point */
    snprintf(command, STRING_SIZE, "mkdir -p %s", BUNDLED_REPO_MOUNT);
    if (mysystem(command)) {
        fprintf(flog, "Failed to create bundled repo mount point\n");
        return FAILURE;
    }
    
    /* Check if bundled repo exists on installation media */
    if (stat(BUNDLED_REPO_PATH, &st) != 0) {
        fprintf(flog, "Bundled repository not found at %s\n", BUNDLED_REPO_PATH);
        return FAILURE;
    }
    
    /* Bind mount the repository directory */
    snprintf(command, STRING_SIZE, "mount --bind %s %s", BUNDLED_REPO_PATH, BUNDLED_REPO_MOUNT);
    if (mysystem(command)) {
        fprintf(flog, "Failed to mount bundled repository\n");
        return FAILURE;
    }
    
    fprintf(flog, "Bundled repository mounted at %s\n", BUNDLED_REPO_MOUNT);
    return SUCCESS;
}

/*
 * Configure APK repositories in target system
 * Sets up both online Alpine repos and bundled IPCop repo
 */
int apk_configure_repos(const char *root_path, int include_online)
{
    char repos_file[STRING_SIZE];
    FILE *fp;
    
    fprintf(flog, "Configuring APK repositories\n");
    
    snprintf(repos_file, STRING_SIZE, "%s%s", root_path, APK_REPOS_FILE);
    
    fp = fopen(repos_file, "w");
    if (!fp) {
        fprintf(flog, "Failed to create repositories file: %s\n", strerror(errno));
        return FAILURE;
    }
    
    /* Add bundled IPCop repository (always include) */
    fprintf(fp, "# IPCop bundled packages\n");
    fprintf(fp, "%s\n\n", BUNDLED_REPO_MOUNT);
    
    /* Add online Alpine repositories if network available */
    if (include_online) {
        fprintf(fp, "# Alpine Linux official repositories\n");
        fprintf(fp, "https://dl-cdn.alpinelinux.org/alpine/v3.18/main\n");
        fprintf(fp, "https://dl-cdn.alpinelinux.org/alpine/v3.18/community\n");
        fprintf(flog, "Added online Alpine repositories\n");
    } else {
        fprintf(flog, "Skipping online repositories (offline mode)\n");
    }
    
    fclose(fp);
    
    fprintf(flog, "Repository configuration complete\n");
    return SUCCESS;
}

/*
 * Update APK package indexes
 */
int apk_update_indexes(const char *root_path)
{
    char command[STRING_SIZE];
    
    fprintf(flog, "Updating APK package indexes\n");
    
    snprintf(command, STRING_SIZE, "%s --root %s update", APK_CMD, root_path);
    if (mysystem(command)) {
        fprintf(flog, "Failed to update APK indexes\n");
        return FAILURE;
    }
    
    fprintf(flog, "APK indexes updated successfully\n");
    return SUCCESS;
}

/*
 * Install a single package or list of packages
 */
int apk_install_package(const char *root_path, const char *package)
{
    char command[STRING_SIZE_LARGE];
    
    fprintf(flog, "Installing package(s): %s\n", package);
    
    snprintf(command, STRING_SIZE_LARGE, 
             "%s --root %s --no-interactive add %s", 
             APK_CMD, root_path, package);
    
    if (mysystem(command)) {
        fprintf(flog, "Failed to install package: %s\n", package);
        return FAILURE;
    }
    
    fprintf(flog, "Package installed successfully: %s\n", package);
    return SUCCESS;
}

/*
 * Install packages from a list file
 * Format: one package name per line, # for comments
 */
int apk_install_from_list(const char *root_path, const char *list_file, 
                          void (*progress_callback)(int current, int total))
{
    FILE *fp;
    char line[STRING_SIZE];
    char package[STRING_SIZE];
    int total_packages = 0;
    int installed = 0;
    int failed = 0;
    
    fprintf(flog, "Installing packages from list: %s\n", list_file);
    
    /* Count total packages first */
    fp = fopen(list_file, "r");
    if (!fp) {
        fprintf(flog, "Failed to open package list: %s\n", list_file);
        return FAILURE;
    }
    
    while (fgets(line, sizeof(line), fp)) {
        /* Skip comments and empty lines */
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r')
            continue;
        total_packages++;
    }
    fclose(fp);
    
    fprintf(flog, "Found %d packages to install\n", total_packages);
    
    /* Now install packages */
    fp = fopen(list_file, "r");
    if (!fp) {
        return FAILURE;
    }
    
    while (fgets(line, sizeof(line), fp)) {
        /* Skip comments and empty lines */
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r')
            continue;
        
        /* Remove newline */
        line[strcspn(line, "\r\n")] = 0;
        
        /* Trim whitespace */
        sscanf(line, "%s", package);
        
        if (strlen(package) == 0)
            continue;
        
        /* Update progress if callback provided */
        if (progress_callback) {
            progress_callback(installed + 1, total_packages);
        }
        
        /* Install package */
        if (apk_install_package(root_path, package) == SUCCESS) {
            installed++;
        } else {
            fprintf(flog, "Warning: Failed to install %s, continuing...\n", package);
            failed++;
        }
    }
    
    fclose(fp);
    
    fprintf(flog, "Package installation complete: %d/%d successful, %d failed\n", 
            installed, total_packages, failed);
    
    /* Consider it success if at least 80% installed */
    return (installed >= (total_packages * 0.8)) ? SUCCESS : FAILURE;
}

/*
 * Install IPCop custom packages (bundled with installer)
 */
int apk_install_ipcop_packages(const char *root_path)
{
    fprintf(flog, "Installing IPCop custom packages\n");
    
    /* Install core IPCop packages in order */
    const char *ipcop_packages[] = {
        "ipcop-core",
        "ipcop-progs",
        "ipcop-gui",
        "ipcop-lang",
        NULL
    };
    
    int i;
    for (i = 0; ipcop_packages[i] != NULL; i++) {
        if (apk_install_package(root_path, ipcop_packages[i]) != SUCCESS) {
            fprintf(flog, "Critical: Failed to install %s\n", ipcop_packages[i]);
            return FAILURE;
        }
    }
    
    fprintf(flog, "IPCop packages installed successfully\n");
    return SUCCESS;
}

/*
 * Check if network is available for online package installation
 */
int apk_check_network(void)
{
    char command[STRING_SIZE];
    
    fprintf(flog, "Checking network connectivity\n");
    
    /* Try to ping Alpine CDN */
    snprintf(command, STRING_SIZE, "ping -c 1 -W 2 dl-cdn.alpinelinux.org > /dev/null 2>&1");
    
    if (mysystem(command) == 0) {
        fprintf(flog, "Network is available\n");
        return SUCCESS;
    }
    
    fprintf(flog, "Network is not available\n");
    return FAILURE;
}

/*
 * Verify APK package installation
 */
int apk_verify_installation(const char *root_path)
{
    char command[STRING_SIZE];
    
    fprintf(flog, "Verifying APK installation\n");
    
    snprintf(command, STRING_SIZE, "%s --root %s audit", APK_CMD, root_path);
    
    if (mysystem(command)) {
        fprintf(flog, "APK audit found issues\n");
        return FAILURE;
    }
    
    fprintf(flog, "APK installation verified\n");
    return SUCCESS;
}

/*
 * Clean up APK cache
 */
int apk_cleanup(const char *root_path)
{
    char command[STRING_SIZE];
    
    fprintf(flog, "Cleaning up APK cache\n");
    
    snprintf(command, STRING_SIZE, "%s --root %s cache clean", APK_CMD, root_path);
    mysystem(command);  /* Don't fail on cleanup errors */
    
    return SUCCESS;
}
