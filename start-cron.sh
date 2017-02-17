#!/bin/sh

/root/backup.sh
cron
touch /var/log/cron.log
tail -F /var/log/cron.log
