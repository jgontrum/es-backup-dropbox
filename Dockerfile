FROM python:3.5
MAINTAINER Johannes Gontrum <gontrum@me.com>

COPY config/dropbox /root/.dropbox_uploader
COPY backup.sh /root/backup.sh
COPY start-cron.sh /root/start-cron.sh

RUN apt-get update
RUN apt-get install -y curl cron

RUN curl "https://raw.githubusercontent.com/andreafabrizi/Dropbox-Uploader/master/dropbox_uploader.sh" -o /root/dropbox_uploader.sh

RUN chmod +x /root/dropbox_uploader.sh
RUN chmod +x /root/backup.sh
RUN chmod +x /root/start-cron.sh

# Copy and set up the app
RUN mkdir /app
RUN pip install virtualenv
COPY . /app
RUN cd /app && make clean

RUN (crontab -l 2>/dev/null; echo "0 0,6,12,18 * * * /root/backup.sh") | crontab -

ENTRYPOINT sh /root/start-cron.sh
