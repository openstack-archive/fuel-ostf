#!/bin/sh

cat > ${OSTF_DB_CONF} <<EOL
DEVELOPMENT: 1
DATABASE:
  name: "${OSTF_DB}"
  engine: "postgresql"
  host: "localhost"
  port: "8777"
  user: "${OSTF_DB_USER}"
  passwd: "${OSTF_DB_PW}"

EOL