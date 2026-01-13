/*
 * helper_openrc.h: OpenRC service configuration helper functions header
 *
 * Copyright (C) 2024 IPCop Development Team
 * Licensed under GPL v2
 *
 * $Id: helper_openrc.h $
 */

#ifndef __HELPER_OPENRC_H__
#define __HELPER_OPENRC_H__

/*
 * Enable an OpenRC service in a specific runlevel
 * 
 * @param root_path Path to target system root
 * @param service Service name (e.g., "ipcop-init", "apache2")
 * @param runlevel Runlevel name (e.g., "boot", "default", "shutdown")
 * @return SUCCESS or FAILURE
 */
int openrc_enable_service(const char *root_path, const char *service, const char *runlevel);

/*
 * Configure all IPCop OpenRC services for first boot
 * Enables critical services in appropriate runlevels
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int openrc_configure_services(const char *root_path);

/*
 * Clean up SysVinit configuration for OpenRC compatibility
 * Backs up and simplifies /etc/inittab
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int openrc_cleanup_sysvinit(const char *root_path);

#endif /* __HELPER_OPENRC_H__ */
