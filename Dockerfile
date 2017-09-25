FROM node:0.12.5
MAINTAINER Aarni Koskela <aarni.koskela@shuup.com>
EXPOSE 8080
ADD . /var/www/shuup/working_copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-minimal python3-virtualenv python3-pip python3-dev python3-pil && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN python3 -m virtualenv -p /usr/bin/python3 --system-site-packages /var/www/shuup/venv && \
    /var/www/shuup/venv/bin/pip install -U pip setuptools
RUN /var/www/shuup/venv/bin/pip install /var/www/shuup/working_copy
RUN /var/www/shuup/venv/bin/python -m shuup_workbench migrate
RUN /var/www/shuup/venv/bin/python -m shuup_workbench shuup_populate_mock --with-superuser=admin
CMD /var/www/shuup/venv/bin/python -m shuup_workbench runserver 0:8080
