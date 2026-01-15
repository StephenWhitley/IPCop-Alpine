#!/bin/sh

cd /

find usr etc var -mindepth 1 \( -type f -o -type d -o -type l \) -exec stat -c '%A %U %G %y %n' {} + | grep -E '2026-01-(0[3-9]|1[0-9])' \
| grep -v -E 'usr/share/man|usr/share/info|usr/local|usr/x86|usr/share/perl|usr/share/X11|/cache|usr/lib/lib|usr/lib/xtable|usr/lib/gcc' \
| grep -v -E 'usr/lib/slang|usr/lib/perl5|usr/lib/sasl|usr/lib/slang|usr/lib/python|usr/lib/libexec|usr/share/slsh'





