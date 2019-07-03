FROM ubuntu:bionic

ARG buildtime_uid
ARG buildtime_gid

ENV RUNTIME_UID=$buildtime_uid
ENV RUNTIME_GID=$buildtime_gid

# install latest python and nodejs
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      curl \
      software-properties-common

# Install nodejs and add 'hold' such that it doesn't get upgraded
RUN echo "deb https://deb.nodesource.com/node_6.x xenial main" > /etc/apt/sources.list.d/node.list \
    && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - 

# add yarn ppa
#RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
#RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      gettext \
      git \
      nodejs=6.17.1-1nodesource1 \
      psmisc \
      python2.7 \
      python-pip \
      python-sphinx \
      python-virtualenv \
      libmysqlclient-dev \
      make \
      python-yaml \
      wget

RUN pip install protobuf

RUN npm install -g "grunt-cli"

RUN addgroup --gid $RUNTIME_GID kalite && \
    adduser --uid $RUNTIME_UID --ingroup kalite --home /home/kalite --shell /bin/sh --disabled-password --gecos "" kalite
WORKDIR /home/kalite
USER kalite

# A volume used to share `pex`/`whl` files and fixtures with docker host
VOLUME /docker/mnt

# do the time-consuming base install commands
CMD cd /docker/mnt \
    && virtualenv -p python2 --system-site-packages ~/venv \
    && . ~/venv/bin/activate \
    && pip install -r requirements.txt \
    && pip install -r ka-lite-submodule/requirements.txt \
    && npm install \
    && cd ka-lite-submodule \
    && npm install \
    && ../make_assets_kalite.sh \
    && cd .. \
#    && npm install grunt-cli \
    && cd centralserver \
    && python manage.py setup --no-assessment-items --noinput \
    && grunt \
    && cd .. \
    && cd ka-lite-submodule \
    && node build.js
