CC=gcc
CFLAGS=-D_GNU_SOURCE -I. -Wall -Wno-format-truncation -Wno-main -Wno-address -Wno-unused-but-set-variable -Wformat-overflow=0 -Wno-logical-not-parentheses -DNAME='"IPCop"' -DSNAME='"ipcop"' -DVERSION='"2.2.0"' -DKVER='"2.2.0"'
OBJLIBS=setuid.o helper.o helper_backup.o

# Find all .c files that are NOT the helpers (and avoid overwriting helper.c/setuid.c logic)
# We want to build specific binaries.
# List of standard progs that might be here (dynamically found)
SRCS=$(filter-out setuid.c helper.c helper_backup.c, $(wildcard *.c))
PROGS=$(SRCS:.c=)

all: $(PROGS)

# Compile helpers
setuid.o: setuid.c setuid.h
	$(CC) $(CFLAGS) -c setuid.c -o setuid.o

helper.o: helper.c common.h
	$(CC) $(CFLAGS) -c helper.c -o helper.o

helper_backup.o: helper_backup.c common_backup.h
	$(CC) $(CFLAGS) -c helper_backup.c -o helper_backup.o

# Compile each program
%: %.c $(OBJLIBS)
	$(CC) $(CFLAGS) $< $(OBJLIBS) -o $@ -lcrypt

clean:
	rm -f $(PROGS) *.o
