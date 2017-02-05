#!/bin/bash
set -e
GRLC_CLONE_URL=https://github.com/CLARIAH/grlc.git

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

#configure git
exec_as_grlc git config --global core.autocrlf input
exec_as_grlc git config --global gc.auto 0



exec_as_grlc git clone ${GRLC_CLONE_URL} ${GRLC_INSTALL_DIR}
cd ${GRLC_INSTALL_DIR}
pip install -r requirements.txt





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
