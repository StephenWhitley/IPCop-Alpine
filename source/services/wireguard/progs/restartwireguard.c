/* IPCop helper program - restartwireguard
 *
 * This file is part of the IPCop Firewall.
 *
 * (c) 2026 The IPCop Team
 */

#include "common.h"
#include "setuid.h"
#include <fcntl.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

void usage(char *prg, int exit_code) {
  printf("Usage: %s [OPTION]\n\n", prg);
  printf("Options:\n");
  printf("  --start               start wireguard\n");
  printf("  --stop                stop wireguard\n");
  printf("  --restart             restart wireguard\n");
  printf("  -v, --verbose         be verbose\n");
  printf("      --help            display this help and exit\n");
  exit(exit_code);
}

static int flag_start = 0;
static int flag_stop = 0;
static int flag_restart = 0;

int main(int argc, char **argv) {
  int enabled = 0;
  NODEKV *wg_kv = NULL;

  static struct option long_options[] = {
      {"start", no_argument, &flag_start, 1},
      {"stop", no_argument, &flag_stop, 1},
      {"restart", no_argument, &flag_restart, 1},
      {"verbose", no_argument, 0, 'v'},
      {"help", no_argument, 0, 'h'},
      {0, 0, 0, 0}};
  int c;
  int option_index = 0;

  if (!(initsetuid()))
    exit(1);

  while ((c = getopt_long(argc, argv, "v", long_options, &option_index)) !=
         -1) {
    switch (c) {
    case 'v': /* verbose */
      flag_verbose++;
      break;
    case 'h':
      usage(argv[0], 0);
    default:
      if (c != 0) {
        fprintf(stderr, "unknown option\n");
        usage(argv[0], 1);
      }
    }
  }

  if (!flag_start && !flag_stop && !flag_restart) {
    usage(argv[0], 1);
  }

  // Read settings
  verbose_printf(1, "Reading WireGuard settings...\n");
  if (read_kv_from_file(&wg_kv, "/var/ipcop/wireguard/settings") == SUCCESS) {
    if (test_kv(wg_kv, "ENABLED", "on") == SUCCESS) {
      enabled = 1;
    }
    free_kv(&wg_kv);
  }

  if (!enabled) {
    verbose_printf(1, "WireGuard not enabled...stopping\n");
    safe_system("/sbin/rc-service wireguard stop > /dev/null 2>&1");
    safe_system("/sbin/rc-update del wireguard default 2>/dev/null");
    return 0;
  }

  // Set default run_level, since it's enabled
  safe_system("/sbin/rc-update add wireguard default 2>/dev/null");

  if (flag_start) {
    verbose_printf(1, "Starting WireGuard...\n");
    safe_system("/sbin/rc-service wireguard start > /dev/null 2>&1");
  } else if (flag_stop) {
    verbose_printf(1, "Stopping WireGuard...\n");
    safe_system("/sbin/rc-service wireguard stop > /dev/null 2>&1");
  } else if (flag_restart) {
    verbose_printf(1, "Restarting WireGuard...\n");
    safe_system("/sbin/rc-service wireguard restart > /dev/null 2>&1");
  }

  return 0;
}
