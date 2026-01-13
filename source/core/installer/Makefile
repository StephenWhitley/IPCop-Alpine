#
# $Id: Makefile 7846 2015-02-01 18:35:46Z owes $
#

# Support gdb, add several defines used in our code
COPTS = -g -ggdb2 -Wall -DNAME='"$(NAME)"' -DSNAME='"$(SNAME)"' -DKVER='"$(KVER)"' -DVERSION='"$(VERSION)"'

HEADERS = arch_defs.h common.h helper_apk.h

OBJS_SETUP = setup.o helper.o helper_kernel.o helper_newt.o hardware.o host_domain.o keymap.o passwords.o timezone.o \
	net_dhcp.o net_isdn.o usbnames.o networking.o
LIBS_SETUP = -lnewt -lslang -lpci -lusb-1.0 -lz -lintl

all: setup

setup: $(OBJS_SETUP) $(HEADERS)
	$(CC) $(LDFLAGS) $(CFLAGS) $(COPTS) $(OBJS_SETUP) -o $@ $(LIBS_SETUP)

helper: helper.c
	$(CC) $(CFLAGS) $(COPTS) -c  $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) $(COPTS) -c  $< -o $@
