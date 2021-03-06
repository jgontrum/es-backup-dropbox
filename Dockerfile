FROM python:3.5
MAINTAINER Johannes Gontrum <gontrum@me.com>

# You should add a volume in docker to provide this file
#COPY config/dropbox /root/.dropbox_uploader
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
RUN cd /app && make clean && make

RUN (crontab -l 2>/dev/null; echo "0 0,6,12,18 * * * /root/backup.sh") | crontab -

RUN touch /app/config/dropbox
RUN ln -s /app/config/dropbox /root/.dropbox_uploader

ENTRYPOINT sh /root/start-cron.sh
