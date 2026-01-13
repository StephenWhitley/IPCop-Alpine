/*
 * helper_apk.h: APK package management helper functions header
 *
 * Copyright (C) 2024 IPCop Development Team
 * Licensed under GPL v2
 *
 * $Id: helper_apk.h $
 */

#ifndef __HELPER_APK_H__
#define __HELPER_APK_H__

/*
 * Initialize APK database in the target system
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int apk_init_db(const char *root_path);

/*
 * Mount bundled APK repository from installation media
 * 
 * @return SUCCESS or FAILURE
 */
int apk_mount_bundled_repo(void);

/*
 * Configure APK repositories in target system
 * Sets up both online Alpine repos and bundled IPCop repo
 * 
 * @param root_path Path to target system root
 * @param include_online Whether to include online Alpine repositories
 * @return SUCCESS or FAILURE
 */
int apk_configure_repos(const char *root_path, int include_online);

/*
 * Update APK package indexes
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int apk_update_indexes(const char *root_path);

/*
 * Install a single package or list of packages
 * 
 * @param root_path Path to target system root
 * @param package Package name or space-separated list
 * @return SUCCESS or FAILURE
 */
int apk_install_package(const char *root_path, const char *package);

/*
 * Install packages from a list file
 * Format: one package name per line, # for comments
 * 
 * @param root_path Path to target system root
 * @param list_file Path to package list file
 * @param progress_callback Optional callback for progress updates
 * @return SUCCESS or FAILURE
 */
int apk_install_from_list(const char *root_path, const char *list_file,
                          void (*progress_callback)(int current, int total));

/*
 * Install IPCop custom packages (bundled with installer)
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int apk_install_ipcop_packages(const char *root_path);

/*
 * Check if network is available for online package installation
 * 
 * @return SUCCESS if network available, FAILURE otherwise
 */
int apk_check_network(void);

/*
 * Verify APK package installation
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int apk_verify_installation(const char *root_path);

/*
 * Clean up APK cache
 * 
 * @param root_path Path to target system root
 * @return SUCCESS or FAILURE
 */
int apk_cleanup(const char *root_path);

#endif /* __HELPER_APK_H__ */
