#!/bin/bash

rm -r /tmp/backup
mkdir /tmp/backup
cd /tmp/backup

while read p; do
  /app/env/bin/backup --index $p --chunksize 1000 --host elasticsearch
done < /app/config/backup_index

for i in *
do
  echo "Uploading $i..."
  /root/dropbox_uploader.sh upload /tmp/backup/$i $i
done

rm -r /tmp/backup

echo "Finished."

