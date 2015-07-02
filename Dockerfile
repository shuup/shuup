FROM node:0.12.5
MAINTAINER Aarni Koskela <aarni.koskela@shoop.io>
EXPOSE 8080
ADD . /var/www/shoop/working_copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-minimal python3-virtualenv python3-pip python3-dev python3-pil && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN python3 -m virtualenv -p /usr/bin/python3 --system-site-packages /var/www/shoop/venv && \
    /var/www/shoop/venv/bin/pip install -U pip setuptools
RUN /var/www/shoop/venv/bin/pip install /var/www/shoop/working_copy
RUN /var/www/shoop/venv/bin/python -m shoop_workbench migrate
RUN /var/www/shoop/venv/bin/python -m shoop_workbench shoop_populate_mock --with-superuser=admin
CMD /var/www/shoop/venv/bin/python -m shoop_workbench runserver 0:8080
