/*
 * helper_openrc.c: OpenRC service configuration helper functions
 *
 * Copyright (C) 2024 IPCop Development Team
 * Licensed under GPL v2
 *
 * $Id: helper_openrc.c $
 */

#include "common.h"
#include "helper_openrc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/*
 * Enable an OpenRC service in a specific runlevel
 */
int openrc_enable_service(const char *root_path, const char *service, const char *runlevel)
{
    char command[STRING_SIZE];
    
    if (!root_path || !service || !runlevel) {
        fprintf(flog, "ERROR: Invalid parameters to openrc_enable_service\n");
        return FAILURE;
    }
    
    fprintf(flog, "Enabling %s service in %s runlevel...\n", service, runlevel);
    
    snprintf(command, STRING_SIZE, "chroot %s rc-update add %s %s 2>/dev/null", 
             root_path, service, runlevel);
    
    if (mysystem(command)) {
        fprintf(flog, "WARNING: Failed to enable %s in %s runlevel\n", service, runlevel);
        return FAILURE;
    }
    
    fprintf(flog, "Successfully enabled %s in %s runlevel\n", service, runlevel);
    return SUCCESS;
}


/*
 * Configure all IPCop OpenRC services for first boot
 */
int openrc_configure_services(const char *root_path)
{
    if (!root_path) {
        fprintf(flog, "ERROR: Invalid root path\n");
        return FAILURE;
    }
    
    fprintf(flog, "Configuring OpenRC services for first boot...\n");
    
    /* Boot runlevel services - critical for system startup */
    fprintf(flog, "Configuring boot runlevel services...\n");
    
    if (openrc_enable_service(root_path, "ipcop-init", "boot") == FAILURE) {
        fprintf(flog, "ERROR: Failed to enable ipcop-init - system may not boot properly!\n");
    }
    
    if (openrc_enable_service(root_path, "ipcop-network", "boot") == FAILURE) {
        fprintf(flog, "ERROR: Failed to enable ipcop-network - network may not start!\n");
    }
    
    /* Also enable standard networking service if available */
    openrc_enable_service(root_path, "networking", "boot");
    
    /* Default runlevel services - user services */
    fprintf(flog, "Configuring default runlevel services...\n");
    
    if (openrc_enable_service(root_path, "ipcop-firewall", "default") == FAILURE) {
        fprintf(flog, "WARNING: Failed to enable ipcop-firewall\n");
    }
    
    if (openrc_enable_service(root_path, "lighttpd", "default") == FAILURE) {
        fprintf(flog, "WARNING: Failed to enable lighttpd - web interface may not start\n");
    }
    
    /* Enable local service for shutdown hooks */
    openrc_enable_service(root_path, "local", "shutdown");
    
    /* SSH is optional - will be enabled/disabled by setup */
    /* RED interface is started manually/on-demand, not enabled by default */
    
    fprintf(flog, "OpenRC service configuration complete\n");
    return SUCCESS;
}


/*
 * Disable SysVinit inittab if it exists (for clean OpenRC operation)
 */
int openrc_cleanup_sysvinit(const char *root_path)
{
    char command[STRING_SIZE];
    char filepath[STRING_SIZE];
    
    if (!root_path) {
        return FAILURE;
    }
    
    fprintf(flog, "Cleaning up SysVinit configuration...\n");
    
    /* Backup and simplify inittab for OpenRC */
    snprintf(filepath, STRING_SIZE, "%s/etc/inittab", root_path);
    snprintf(command, STRING_SIZE, "[ -f %s ] && cp %s %s.sysvinit", 
             filepath, filepath, filepath);
    mysystem(command);
    
    /* Create minimal OpenRC-compatible inittab */
    snprintf(command, STRING_SIZE, 
             "echo '# Minimal inittab for OpenRC' > %s/etc/inittab", root_path);
    mysystem(command);
    
    snprintf(command, STRING_SIZE, 
             "echo 'ca::ctrlaltdel:/sbin/reboot' >> %s/etc/inittab", root_path);
    mysystem(command);
    
    fprintf(flog, "SysVinit cleanup complete\n");
    return SUCCESS;
}
