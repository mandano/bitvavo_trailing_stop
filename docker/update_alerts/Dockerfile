FROM ubuntu:focal
RUN apt update
RUN apt install wget -y

RUN cd /tmp/
RUN wget https://github.com/dshearer/jobber/releases/download/v1.4.4/jobber_1.4.4-1_amd64.deb
RUN dpkg -i jobber_1.4.4-1_amd64.deb

ENV USERID 1000
RUN useradd jobberuser -m -s /bin/bash --user-group --uid ${USERID} && \
    mkdir -p "/var/jobber/${USERID}" && \
    chown -R jobberuser:jobberuser "/var/jobber/${USERID}"

COPY --chown=jobberuser:jobberuser jobfile /home/jobberuser/.jobber
RUN chmod 0600 /home/jobberuser/.jobber

RUN apt install python3 python3-venv python3-pip -y
RUN pip3 install Faker pytest simplejson python-dotenv python-bitvavo-api

RUN apt remove wget -y
RUN apt autoremove -y

USER jobberuser

