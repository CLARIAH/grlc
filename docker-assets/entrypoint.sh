#!/bin/bash
set -e
source ${GRLC_RUNTIME_DIR}/functions

[[ $DEBUG == true ]] && set -x

map_uidgid

case ${1} in
  app:start)
    setup_nginx
    # initialize_system
    # configure_gitlab
    # configure_gitlab_shell
    # configure_nginx

    case ${1} in
      app:start)
        cd ${GRLC_INSTALL_DIR}
        # put github's access_token in place
        cp config.default.ini config.ini
        sed -i "s/xxx/${GRLC_GITHUB_ACCESS_TOKEN}/" config.ini
        # configure grlc server name
        sed -i "s/grlc.io/${GRLC_SERVER_NAME}/" config.ini
        # configure default sparql endpoint
        sed -i "s|http://dbpedia.org/sparql|${GRLC_SPARQL_ENDPOINT}|" config.ini
        # enable/disable debugging
        sed -i "s/debug = False/debug = ${DEBUG}/" config.ini

        grlc-server --port=8088
        # migrate_database
        # rm -rf /var/run/supervisor.sock
        # exec /usr/bin/supervisord -nc /etc/supervisor/supervisord.conf
        ;;
      # app:init)
      #   migrate_database
      #   ;;
      # app:sanitize)
      #   sanitize_datadir
      #   ;;
      # app:rake)
      #   shift 1
      #   execute_raketask $@
      #   ;;
    esac
    ;;
  app:help)
    echo "Available options:"
    echo " app:start        - Starts the grlc server (default)"
    # echo " app:init         - Initialize the gitlab server (e.g. create databases, compile assets), but don't start it."
    # echo " app:sanitize     - Fix repository/builds directory permissions."
    # echo " app:rake <task>  - Execute a rake task."
    echo " app:help         - Displays the help"
    echo " [command]        - Execute the specified command, eg. bash."
    ;;
  *)
    exec "$@"
    ;;
esac
