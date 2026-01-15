/* IPCop helper program - restartsuricata
 *
 * This file is part of the IPCop Firewall.
 *
 * IPCop is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * IPCop is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with IPCop.  If not, see <http://www.gnu.org/licenses/>.
 *
 * (c) 2026 The IPCop Team
 *
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
  printf("  -t, --test            test first, do not start if not running\n");
  printf("  -v, --verbose         be verbose\n");
  printf("      --help            display this help and exit\n");
  exit(exit_code);
}

/*
 * Generate suricata.yaml configuration from IPCop settings
 */
void generate_config(NODEKV *suricata_kv) {
  FILE *file;
  char mode[STRING_SIZE] = "ids";
  char home_net[STRING_SIZE] = "";
  int monitor_green = 0;
  int monitor_blue = 0;
  int monitor_red = 0;

  // Read settings
  find_kv_default(suricata_kv, "MODE", mode);
  find_kv_default(suricata_kv, "HOME_NET", home_net);

  if (test_kv(suricata_kv, "MONITOR_GREEN", "on") == SUCCESS) {
    monitor_green = 1;
  }
  if (test_kv(suricata_kv, "MONITOR_BLUE", "on") == SUCCESS) {
    monitor_blue = 1;
  }
  if (test_kv(suricata_kv, "MONITOR_RED", "on") == SUCCESS) {
    monitor_red = 1;
  }

  verbose_printf(1, "Generating Suricata configuration (mode: %s)...\n", mode);

  // Build HOME_NET if auto
  if (strcmp(home_net, "auto") == 0 || strlen(home_net) == 0) {
    char nets[STRING_SIZE_LARGE] = "[";
    int first = 1;

    if (ipcop_ethernet.count[GREEN] && ipcop_ethernet.address[GREEN][1][0]) {
      if (!first)
        strcat(nets, ",");
      strcat(nets, ipcop_ethernet.address[GREEN][1]);
      strcat(nets, "/");
      strcat(nets, ipcop_ethernet.netmask[GREEN][1]);
      first = 0;
    }
    if (ipcop_ethernet.count[BLUE] && ipcop_ethernet.address[BLUE][1][0]) {
      if (!first)
        strcat(nets, ",");
      strcat(nets, ipcop_ethernet.address[BLUE][1]);
      strcat(nets, "/");
      strcat(nets, ipcop_ethernet.netmask[BLUE][1]);
      first = 0;
    }
    strcat(nets, "]");
    strncpy(home_net, nets, STRING_SIZE - 1);
  }

  // Generate minimal suricata.yaml
  if (!(file = fopen("/var/ipcop/suricata/suricata.yaml", "w"))) {
    fprintf(stderr, "Unable to create /var/ipcop/suricata/suricata.yaml\n");
    exit(1);
  }

  // YAML header (required by Suricata)
  fprintf(file, "%%YAML 1.1\n");
  fprintf(file, "---\n");
  fprintf(file, "# IPCop-generated Suricata configuration\n");
  fprintf(file, "# Do not edit manually - changes will be overwritten\n\n");

  fprintf(file, "vars:\n");
  fprintf(file, "  address-groups:\n");
  fprintf(file, "    HOME_NET: \"%s\"\n", home_net);
  fprintf(file, "    EXTERNAL_NET: \"!$HOME_NET\"\n");
  fprintf(file, "    HTTP_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    SMTP_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    SQL_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    DNS_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    TELNET_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    AIM_SERVERS: \"$EXTERNAL_NET\"\n");
  fprintf(file, "    DC_SERVERS: \"$HOME_NET\"\n");
  fprintf(file, "    DNP3_SERVER: \"$HOME_NET\"\n");
  fprintf(file, "    DNP3_CLIENT: \"$HOME_NET\"\n");
  fprintf(file, "    MODBUS_CLIENT: \"$HOME_NET\"\n");
  fprintf(file, "    MODBUS_SERVER: \"$HOME_NET\"\n");
  fprintf(file, "    ENIP_CLIENT: \"$HOME_NET\"\n");
  fprintf(file, "    ENIP_SERVER: \"$HOME_NET\"\n");
  fprintf(file, "  port-groups:\n");
  fprintf(file, "    HTTP_PORTS: \"80\"\n");
  fprintf(file, "    SHELLCODE_PORTS: \"!80\"\n");
  fprintf(file, "    ORACLE_PORTS: \"1521\"\n");
  fprintf(file, "    SSH_PORTS: \"22\"\n");
  fprintf(file, "    DNP3_PORTS: \"20000\"\n");
  fprintf(file, "    MODBUS_PORTS: \"502\"\n");
  fprintf(file, "    FILE_DATA_PORTS: \"[$HTTP_PORTS,110,143]\"\n");
  fprintf(file, "    FTP_PORTS: \"21\"\n");
  fprintf(file, "    GENEVE_PORTS: \"6081\"\n");
  fprintf(file, "    VXLAN_PORTS: \"4789\"\n");
  fprintf(file, "    TEREDO_PORTS: \"3544\"\n\n");

  fprintf(file, "default-log-dir: /var/log/suricata\n\n");

  // af-packet (IDS) or nfqueue (IPS) configuration
  if (strcmp(mode, "ips") == 0) {
    fprintf(file, "# Inline IPS mode (nfqueue)\n");
    fprintf(file, "nfq:\n");

    if (monitor_green && ipcop_ethernet.count[GREEN]) {
      fprintf(file, "  - mode: accept\n");
      fprintf(file, "    fail-open: yes\n");
    }
    if (monitor_blue && ipcop_ethernet.count[BLUE]) {
      fprintf(file, "  - mode: accept\n");
      fprintf(file, "    fail-open: yes\n");
    }
    if (monitor_red && ipcop_ethernet.count[RED]) {
      fprintf(file, "  - mode: accept\n");
      fprintf(file, "    fail-open: yes\n");
    }
  } else {
    fprintf(file, "# IDS mode (af-packet)\n");
    fprintf(file, "af-packet:\n");

    if (monitor_green && ipcop_ethernet.count[GREEN]) {
      fprintf(file, "  - interface: %s\n", ipcop_ethernet.device[GREEN][1]);
      fprintf(file, "    threads: auto\n");
      fprintf(file, "    cluster-type: cluster_flow\n");
      fprintf(file, "    defrag: yes\n");
    }
    if (monitor_blue && ipcop_ethernet.count[BLUE]) {
      fprintf(file, "  - interface: %s\n", ipcop_ethernet.device[BLUE][1]);
      fprintf(file, "    threads: auto\n");
      fprintf(file, "    cluster-type: cluster_flow\n");
      fprintf(file, "    defrag: yes\n");
    }
    if (monitor_red && ipcop_ethernet.count[RED]) {
      fprintf(file, "  - interface: %s\n", ipcop_ethernet.device[RED][1]);
      fprintf(file, "    threads: auto\n");
      fprintf(file, "    cluster-type: cluster_flow\n");
      fprintf(file, "    defrag: yes\n");
    }
  }

  fprintf(file, "\noutputs:\n");
  fprintf(file, "  - fast:\n");
  fprintf(file, "      enabled: yes\n");
  fprintf(file, "      filename: fast.log\n");
  fprintf(file, "  - eve-log:\n");
  fprintf(file, "      enabled: yes\n");
  fprintf(file, "      filetype: regular\n");
  fprintf(file, "      filename: eve.json\n");
  fprintf(file, "      types:\n");
  fprintf(file, "        - alert\n");
  fprintf(file, "        - http\n");
  fprintf(file, "        - dns\n");
  fprintf(file, "        - tls\n\n");

  fprintf(file, "rule-files:\n");
  fprintf(file, "  - suricata.rules\n\n");

  fprintf(file, "# Use emerging threats open ruleset\n");
  fprintf(file, "default-rule-path: /var/lib/suricata/rules\n");

  fclose(file);
  verbose_printf(1, "Configuration generated successfully\n");
}

/*
 * Set up iptables rules for IPS mode
 */
void setup_iptables(NODEKV *suricata_kv) {
  char mode[STRING_SIZE] = "ids";
  char buffer[STRING_SIZE];
  int monitor_green = 0;
  int monitor_blue = 0;
  int monitor_red = 0;

  find_kv_default(suricata_kv, "MODE", mode);

  if (strcmp(mode, "ips") != 0) {
    verbose_printf(1, "IDS mode - no iptables rules needed\n");
    return;
  }

  if (test_kv(suricata_kv, "MONITOR_GREEN", "on") == SUCCESS) {
    monitor_green = 1;
  }
  if (test_kv(suricata_kv, "MONITOR_BLUE", "on") == SUCCESS) {
    monitor_blue = 1;
  }
  if (test_kv(suricata_kv, "MONITOR_RED", "on") == SUCCESS) {
    monitor_red = 1;
  }

  verbose_printf(1, "Setting up iptables rules for IPS mode...\n");

  // Flush SURICATA chain
  safe_system("/usr/sbin/iptables -F SURICATA");

  // Add NFQUEUE rules for monitored interfaces
  int queue = 0;

  if (monitor_green && ipcop_ethernet.count[GREEN]) {
    snprintf(buffer, STRING_SIZE,
             "/usr/sbin/iptables -A SURICATA -i %s -j NFQUEUE --queue-num %d",
             ipcop_ethernet.device[GREEN][1], queue);
    safe_system(buffer);
    verbose_printf(1, "  Added NFQUEUE rule for GREEN (%s) -> queue %d\n",
                   ipcop_ethernet.device[GREEN][1], queue);
    queue++;
  }

  if (monitor_blue && ipcop_ethernet.count[BLUE]) {
    snprintf(buffer, STRING_SIZE,
             "/usr/sbin/iptables -A SURICATA -i %s -j NFQUEUE --queue-num %d",
             ipcop_ethernet.device[BLUE][1], queue);
    safe_system(buffer);
    verbose_printf(1, "  Added NFQUEUE rule for BLUE (%s) -> queue %d\n",
                   ipcop_ethernet.device[BLUE][1], queue);
    queue++;
  }

  if (monitor_red && ipcop_ethernet.count[RED]) {
    snprintf(buffer, STRING_SIZE,
             "/usr/sbin/iptables -A SURICATA -i %s -j NFQUEUE --queue-num %d",
             ipcop_ethernet.device[RED][1], queue);
    safe_system(buffer);
    verbose_printf(1, "  Added NFQUEUE rule for RED (%s) -> queue %d\n",
                   ipcop_ethernet.device[RED][1], queue);
  }
}

int main(int argc, char **argv) {
  int flag_test = 0;
  int enabled = 0;
  NODEKV *suricata_kv = NULL;

  static struct option long_options[] = {{"test", no_argument, 0, 't'},
                                         {"verbose", no_argument, 0, 'v'},
                                         {"help", no_argument, 0, 'h'},
                                         {0, 0, 0, 0}};
  int c;
  int option_index = 0;

  if (!(initsetuid()))
    exit(1);

  while ((c = getopt_long(argc, argv, "tv", long_options, &option_index)) !=
         -1) {
    switch (c) {
    case 't': /* test first */
      flag_test = 1;
      break;
    case 'v': /* verbose */
      flag_verbose++;
      break;
    case 'h':
      usage(argv[0], 0);
    default:
      fprintf(stderr, "unknown option\n");
      usage(argv[0], 1);
    }
  }

  // Check if suricata is running
  if ((access("/var/run/suricata.pid", F_OK) == -1) && flag_test) {
    verbose_printf(1, "Suricata not running, no need to start\n");
    exit(0);
  }

  // Read settings
  verbose_printf(1, "Reading Suricata settings...\n");
  if (read_kv_from_file(&suricata_kv, "/var/ipcop/suricata/settings") !=
      SUCCESS) {
    fprintf(stderr, "Cannot read suricata settings\n");
    exit(1);
  }

  // Check if enabled
  if (test_kv(suricata_kv, "ENABLED", "on") == SUCCESS) {
    enabled = 1;
  }

  if (!enabled) {
    verbose_printf(1, "Suricata not enabled...stopping\n");
    safe_system("/sbin/rc-service suricata stop");
    safe_system("/sbin/rc-update del suricata default 2>/dev/null");
    free_kv(&suricata_kv);
    return 0;
  }

  // Fetch ethernet settings
  read_ethernet_settings(1);

  // Generate configuration
  generate_config(suricata_kv);

  // Set up iptables (IPS mode only)
  setup_iptables(suricata_kv);

  // Reload firewall rules to apply SURICATA chain
  verbose_printf(1, "Reloading firewall rules...\n");
  safe_system("/usr/bin/setfwrules --ipcop");

  // Add to default runlevel for boot persistence
  verbose_printf(1, "Adding Suricata to default runlevel...\n");
  safe_system("/sbin/rc-update add suricata default 2>/dev/null");

  // Restart suricata
  verbose_printf(1, "Restarting Suricata...\n");
  if (safe_system("/sbin/rc-service suricata restart") != 0) {
    verbose_printf(1, "Restart failed, forcing reset...\n");
    safe_system("/sbin/rc-service suricata zap > /dev/null 2>&1");
    safe_system("/sbin/rc-service suricata stop > /dev/null 2>&1");
    safe_system("/sbin/rc-service suricata start");
  }

  free_kv(&suricata_kv);
  return 0;
}
