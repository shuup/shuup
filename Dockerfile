FROM ubuntu:18.04 as base

USER root
RUN apt update
#    && apt --assume-yes install \
#        libpangocairo-1.0-0 \
#        python3 \
#        python3-dev \
#        python3-pil \
#        python3-pip \
#    &&
RUN apt-get -y install curl gnupg
RUN apt-get --assume-yes -q install python3
RUN apt-get --assume-yes -q install python3-pip
RUN apt-get --assume-yes -q install python3-dev

RUN curl -sL https://deb.nodesource.com/setup_11.x  | bash -
RUN apt-get -y install nodejs

RUN rm -rf /var/lib/apt/lists/ /var/cache/apt/

# These invalidate the cache every single time but
# there really isn't any other obvious way to do this.
COPY . /app
WORKDIR /app

RUN pip3 install -r requirements-dev.txt
RUN python3 setup.py build_resources

RUN python3 -m shuup_workbench migrate
RUN python3 -m shuup_workbench shuup_init

RUN echo '\
from django.contrib.auth import get_user_model\n\
from django.db import IntegrityError\n\
try:\n\
    get_user_model().objects.create_superuser("admin", "admin@admin.com", "admin")\n\
except IntegrityError:\n\
    pass\n'\
| python3 -m shuup_workbench shell

CMD ["python3", "-m", "shuup_workbench", "runserver", "0.0.0.0:8000"]
