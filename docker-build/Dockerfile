FROM python:2.7.12
MAINTAINER albert.merono@vu.nl

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
 && DEBIAN_FRONTEND=noninteractive apt-get install -y nginx git-core logrotate python-pip locales gettext-base sudo \
 && update-locale LANG=C.UTF-8 LC_MESSAGES=POSIX \
 && locale-gen en_US.UTF-8 \
 && DEBIAN_FRONTEND=noninteractive dpkg-reconfigure locales \
 && rm -rf /var/lib/apt/lists/*

COPY assets/build/ ${GRLC_BUILD_DIR}/
RUN bash ${GRLC_BUILD_DIR}/install.sh

COPY assets/runtime/ ${GRLC_RUNTIME_DIR}/
COPY entrypoint.sh /sbin/entrypoint.sh
RUN chmod 755 /sbin/entrypoint.sh

EXPOSE 80/tcp

VOLUME ["${GRLC_DATA_DIR}", "${GRLC_LOG_DIR}"]
WORKDIR ${GRLC_INSTALL_DIR}
ENTRYPOINT ["/sbin/entrypoint.sh"]
CMD ["app:start"]
