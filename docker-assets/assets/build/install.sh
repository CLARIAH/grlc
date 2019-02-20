#!/bin/bash
set -e


## Execute a command as GITLAB_USER
exec_as_grlc() {
  if [[ $(whoami) == ${GRLC_USER} ]]; then
    $@
  else
    sudo -HEu ${GRLC_USER} "$@"
  fi
}

#add grlc user
adduser --disabled-login --gecos 'grlc' ${GRLC_USER}
passwd -d ${GRLC_USER}


cd ${GRLC_INSTALL_DIR}
chown ${GRLC_USER}:${GRLC_USER} ${GRLC_HOME} -R

pip install --upgrade pip
pip install .

npm install git2prov

#move nginx logs to ${GITLAB_LOG_DIR}/nginx
sed -i \
 -e "s|access_log /var/log/nginx/access.log;|access_log ${GRLC_LOG_DIR}/nginx/access.log;|" \
 -e "s|error_log /var/log/nginx/error.log;|error_log ${GRLC_LOG_DIR}/nginx/error.log;|" \
 /etc/nginx/nginx.conf

 # configure gitlab log rotation
 cat > /etc/logrotate.d/grlc << EOF
 ${GRLC_LOG_DIR}/grlc/*.log {
   weekly
   missingok
   rotate 52
   compress
   delaycompress
   notifempty
   copytruncate
 }
 EOF

 # configure gitlab vhost log rotation
 cat > /etc/logrotate.d/grlc-nginx << EOF
 ${GRLC_LOG_DIR}/nginx/*.log {
   weekly
   missingok
   rotate 52
   compress
   delaycompress
   notifempty
   copytruncate
 }
 EOF
