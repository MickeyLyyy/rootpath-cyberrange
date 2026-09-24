#!/bin/bash
ssh-keygen -A
exec /usr/sbin/sshd -D -e -p 2222
