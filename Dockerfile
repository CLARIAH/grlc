# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

FROM python:3.11-slim
MAINTAINER albert.merono@vu.nl

# Default values for env variables
ARG GRLC_GITHUB_ACCESS_TOKEN=
ARG GRLC_GITLAB_ACCESS_TOKEN=
ARG GRLC_SERVER_NAME=grlc.io
ARG GRLC_SPARQL_ENDPOINT=http://dbpedia.org/sparql

ENV GRLC_GITHUB_ACCESS_TOKEN=$GRLC_GITHUB_ACCESS_TOKEN \
    GRLC_GITLAB_ACCESS_TOKEN=$GRLC_GITLAB_ACCESS_TOKEN \
    GRLC_SERVER_NAME=$GRLC_SERVER_NAME \
    GRLC_SPARQL_ENDPOINT=$GRLC_SPARQL_ENDPOINT

ENV GRLC_USER="grlc" \
    GRLC_HOME="/home/grlc" \
    GRLC_LOG_DIR="/var/log/grlc" \
    GITLAB_VERSION=8.10.4 \
    GRLC_CACHE_DIR="/etc/docker-grlc"

ENV GRLC_INSTALL_DIR="${GRLC_HOME}/grlc" \
    GRLC_DATA_DIR="${GRLC_HOME}/data" \
    GRLC_BUILD_DIR="${GRLC_CACHE_DIR}/build" \
    GRLC_RUNTIME_DIR="${GRLC_CACHE_DIR}/runtime"

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y nginx git-core logrotate python3-pip locales gettext-base sudo build-essential apt-utils \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && DEBIAN_FRONTEND=noninteractive dpkg-reconfigure locales \
 && rm -rf /var/lib/apt/lists/*

# RUN curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
RUN apt-get update && apt-get install -y nodejs npm

COPY ./ ${GRLC_INSTALL_DIR}

COPY docker-assets/assets/build/ ${GRLC_BUILD_DIR}/
RUN bash ${GRLC_BUILD_DIR}/install.sh

COPY docker-assets/assets/runtime/ ${GRLC_RUNTIME_DIR}/
COPY docker-assets/entrypoint.sh /sbin/entrypoint.sh


RUN chmod 755 /sbin/entrypoint.sh

EXPOSE 80/tcp

VOLUME ["${GRLC_DATA_DIR}", "${GRLC_LOG_DIR}"]
WORKDIR ${GRLC_INSTALL_DIR}
ENTRYPOINT ["/sbin/entrypoint.sh"]
CMD ["app:start"]
