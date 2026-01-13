/* This file is part of the IPCop Firewall.
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
 * along with IPCop; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
 *
 * Copyright (C) 2003-04-22 Robert Kerr <rkerr@go.to>
 *
 * $Id: setuid.c 1779 2008-09-02 08:04:36Z owes $
 *
 */

#include "setuid.h"
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef OPEN_MAX
#define OPEN_MAX 256
#endif

/* Trusted environment for executing commands */
char *trusted_env[4] = {"PATH=/usr/bin:/usr/sbin:/sbin:/bin", "SHELL=/bin/sh",
                        "TERM=dumb", NULL};

#define DEBUG_LOG_FILE "/var/log/ipcop/debug.log"
#define DEBUG_LOG_MAX_SIZE (10 * 1024 * 1024) /* 10 MB */
#define DEBUG_SETTING_FILE "/var/ipcop/main/settings"

/* Check if debug logging is enabled */
static int is_debug_enabled(void) {
  FILE *f = fopen(DEBUG_SETTING_FILE, "r");
  if (!f)
    return 0;

  char line[256];
  int enabled = 0;
  while (fgets(line, sizeof(line), f)) {
    if (strstr(line, "DEBUG_SYSTEM_CALLS") && strstr(line, "=on")) {
      enabled = 1;
      break;
    }
  }
  fclose(f);
  return enabled;
}

/* Rotate log file if it exceeds max size */
static void rotate_debug_log(void) {
  struct stat st;
  if (stat(DEBUG_LOG_FILE, &st) == 0 && st.st_size > DEBUG_LOG_MAX_SIZE) {
    char old_log[512];
    snprintf(old_log, sizeof(old_log), "%s.old", DEBUG_LOG_FILE);
    rename(DEBUG_LOG_FILE, old_log);
  }
}

/* Log command execution with stdout/stderr output */
static void log_command_execution(const char *progname, const char *command,
                                  const char *stdout_buf,
                                  const char *stderr_buf, int exit_code) {
  if (!is_debug_enabled())
    return;

  rotate_debug_log();

  FILE *logf = fopen(DEBUG_LOG_FILE, "a");
  if (!logf)
    return;

  /* Get timestamp */
  time_t now = time(NULL);
  char timebuf[64];
  strftime(timebuf, sizeof(timebuf), "%Y-%m-%d %H:%M:%S", localtime(&now));

  /* Write log entry */
  fprintf(logf, "[%s] %s[%d] UID=%d EUID=%d\n", timebuf, progname, getpid(),
          getuid(), geteuid());
  fprintf(logf, "  CMD: %s\n", command);

  if (stdout_buf && stdout_buf[0]) {
    fprintf(logf, "  STDOUT:\n");
    /* Indent each line */
    char *line = strtok((char *)stdout_buf, "\n");
    while (line) {
      fprintf(logf, "    %s\n", line);
      line = strtok(NULL, "\n");
    }
  } else {
    fprintf(logf, "  STDOUT: (empty)\n");
  }

  if (stderr_buf && stderr_buf[0]) {
    fprintf(logf, "  STDERR:\n");
    char *line = strtok((char *)stderr_buf, "\n");
    while (line) {
      fprintf(logf, "    %s\n", line);
      line = strtok(NULL, "\n");
    }
  } else {
    fprintf(logf, "  STDERR: (empty)\n");
  }

  fprintf(logf, "  EXIT: %d\n\n", exit_code);
  fflush(logf);
  fclose(logf);
}

/* Spawns a child process that uses /bin/sh to interpret a command.
 * This is much the same in use and purpose as system(), yet as it uses execve
 * to pass a trusted environment it's immune to attacks based upon changing
 * IFS, ENV, BASH_ENV and other such variables.
 * Note this does NOT guard against any other attacks, inparticular you MUST
 * validate the command you are passing. If the command is formed from user
 * input be sure to check this input is what you expect. Nasty things can
 * happen if a user can inject ; or `` into your command for example */
int safe_system(char *command) {
  return system_core(command, 0, 0, "safe_system");
}

/* Much like safe_system but lets you specify a non-root uid and gid to run
 * the command as */
int unpriv_system(char *command, uid_t uid, gid_t gid) {
  return system_core(command, uid, gid, "unpriv_system");
}

int system_core(char *command, uid_t uid, gid_t gid, char *error) {
  int pid, status;
  int stdout_pipe[2], stderr_pipe[2];
  char stdout_buf[4096] = {0};
  char stderr_buf[4096] = {0};
  int debug_enabled = is_debug_enabled();

  if (!command)
    return 1;

  /* Create pipes for capturing output if debug is enabled */
  if (debug_enabled) {
    if (pipe(stdout_pipe) == -1 || pipe(stderr_pipe) == -1) {
      debug_enabled = 0; /* Disable debug on pipe failure */
    }
  }

  switch (pid = fork()) {
  case -1:
    if (debug_enabled) {
      close(stdout_pipe[0]);
      close(stdout_pipe[1]);
      close(stderr_pipe[0]);
      close(stderr_pipe[1]);
    }
    return -1;

  case 0: /* child */
  {
    char *argv[4];

    /* Redirect stdout/stderr to pipes if debug enabled */
    if (debug_enabled) {
      close(stdout_pipe[0]); /* Close read end in child */
      close(stderr_pipe[0]);
      dup2(stdout_pipe[1], STDOUT_FILENO);
      dup2(stderr_pipe[1], STDERR_FILENO);
      close(stdout_pipe[1]); /* Close after dup */
      close(stderr_pipe[1]);
    }

    if (gid && setgid(gid)) {
      fprintf(stderr, "%s: ", error);
      perror("Couldn't setgid");
      exit(127);
    }
    if (uid && setuid(uid)) {
      fprintf(stderr, "%s: ", error);
      perror("Couldn't setuid");
      exit(127);
    }
    argv[0] = "sh";
    argv[1] = "-c";
    argv[2] = command;
    argv[3] = NULL;
    execve("/bin/sh", argv, trusted_env);
    fprintf(stderr, "%s: ", error);
    perror("execve failed");
    exit(127);
  }

  default: /* parent */
  {
    if (debug_enabled) {
      close(stdout_pipe[1]); /* Close write end in parent */
      close(stderr_pipe[1]);

      /* Read from pipes using select() */
      fd_set read_fds;
      int stdout_fd = stdout_pipe[0];
      int stderr_fd = stderr_pipe[0];
      int stdout_pos = 0, stderr_pos = 0;
      int stdout_open = 1, stderr_open = 1;

      while (stdout_open || stderr_open) {
        FD_ZERO(&read_fds);
        int max_fd = -1;

        if (stdout_open) {
          FD_SET(stdout_fd, &read_fds);
          max_fd = stdout_fd;
        }
        if (stderr_open) {
          FD_SET(stderr_fd, &read_fds);
          if (stderr_fd > max_fd)
            max_fd = stderr_fd;
        }

        struct timeval timeout = {1, 0}; /* 1 second timeout */
        int ret = select(max_fd + 1, &read_fds, NULL, NULL, &timeout);

        if (ret > 0) {
          if (stdout_open && FD_ISSET(stdout_fd, &read_fds)) {
            ssize_t n = read(stdout_fd, stdout_buf + stdout_pos,
                             sizeof(stdout_buf) - stdout_pos - 1);
            if (n > 0)
              stdout_pos += n;
            else
              stdout_open = 0;
          }
          if (stderr_open && FD_ISSET(stderr_fd, &read_fds)) {
            ssize_t n = read(stderr_fd, stderr_buf + stderr_pos,
                             sizeof(stderr_buf) - stderr_pos - 1);
            if (n > 0)
              stderr_pos += n;
            else
              stderr_open = 0;
          }
        } else if (ret == 0) {
          /* Timeout - check if child has exited */
          break;
        }
      }

      close(stdout_fd);
      close(stderr_fd);
      stdout_buf[stdout_pos] = '\0';
      stderr_buf[stderr_pos] = '\0';
    }

    /* Wait for child */
    do {
      if (waitpid(pid, &status, 0) == -1) {
        if (errno != EINTR)
          return -1;
      } else {
        /* Log command execution if debug enabled */
        if (debug_enabled) {
          int exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
          log_command_execution(error, command, stdout_buf, stderr_buf,
                                exit_code);
        }
        return status;
      }
    } while (1);
  }
  }
}

/* BSD style safe strcat; from the secure programming cookbook */
size_t strlcat(char *dst, const char *src, size_t len) {
  char *dstptr = dst;
  size_t dstlen, tocopy = len;
  const char *srcptr = src;

  while (tocopy-- && *dstptr)
    dstptr++;
  dstlen = dstptr - dst;
  if (!(tocopy = len - dstlen))
    return (dstlen + strlen(src));
  while (*srcptr) {
    if (tocopy != 1) {
      *dstptr++ = *srcptr;
      tocopy--;
    }
    srcptr++;
  }
  *dstptr = 0;

  return (dstlen + (srcptr - src));
}

/* General routine to initialise a setuid root program, and put the
 * environment in a known state. Returns 1 on success, if initsetuid() returns
 * 0 then you should exit(1) immediately, DON'T attempt to recover from the
 * error */
int initsetuid(void) {
  int fds, i;
  struct stat st;
  struct rlimit rlim;

  /* Prevent signal tricks by ignoring all except SIGKILL and SIGCHILD */
  for (i = 0; i < NSIG; i++) {
    if (i != SIGKILL && i != SIGCHLD)
      signal(i, SIG_IGN);
  }

  /* dump all non-standard file descriptors (a full descriptor table could
   * lead to DoS by preventing us opening files) */
  if ((fds = getdtablesize()) == -1)
    fds = OPEN_MAX;
  for (i = 3; i < fds; i++)
    close(i);

  /* check stdin, stdout & stderr are open before going any further */
  for (i = 0; i < 3; i++)
    if (fstat(i, &st) == -1 &&
        ((errno != EBADF) || (close(i), open("/dev/null", O_RDWR, 0)) != i))
      return 0;

  /* disable core dumps in case we're processing sensitive information */
  rlim.rlim_cur = rlim.rlim_max = 0;
  if (setrlimit(RLIMIT_CORE, &rlim)) {
    perror("Couldn't disable core dumps");
    return 0;
  }

  /* drop any supplementary groups, set uid & gid to root */
  if (setgroups(0, NULL)) {
    perror("Couldn't clear group list");
    return 0;
  }
  if (setgid(0)) {
    perror("Couldn't setgid(0)");
    return 0;
  }
  if (setuid(0)) {
    perror("Couldn't setuid(0)");
    return 0;
  }

  return 1;
}
