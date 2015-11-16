#!/bin/sh

cat > ${OSTF_CI_CONF} <<EOL
[adapter]
server_host = 127.0.0.1
server_port = 8777
nailgun_host = 127.0.0.1
nailgun_port = 8000
log_file = ${OSTF_LOGS}"
after_init_hook = False
auth_enable = False
name: "${OSTF_DB}"
engine: "postgresql"
user: "${OSTF_DB_USER}"
passwd: "${OSTF_DB_PW}"
EOL