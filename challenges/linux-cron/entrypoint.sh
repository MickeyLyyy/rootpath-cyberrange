#!/bin/bash
ssh-keygen -A
cron
exec /usr/sbin/sshd -D -e -p 2222
