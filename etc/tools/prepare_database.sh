#!/bin/sh

echo "Preparing pgpass file ${DB_ROOTPGPASS}"
echo "*:*:*:${DB_ROOT}:${DB_ROOTPW}" > ${DB_ROOTPGPASS}
chmod 600 ${DB_ROOTPGPASS}

export PGPASSFILE=${DB_ROOTPGPASS}

echo "Trying to find out if role ${OSTF_DB_USER} exists"
root_roles=$(psql -h 127.0.0.1 -U ${DB_ROOT} -t -c "SELECT 'HERE' from pg_roles where rolname='${OSTF_DB_USER}'")
if [[ ${root_roles} == *HERE ]];then
  echo "Role ${OSTF_DB_USER} exists. Setting password ${OSTF_DB_PW}"
  psql -h 127.0.0.1 -U ${DB_ROOT} -c "ALTER ROLE ${OSTF_DB_USER} WITH SUPERUSER LOGIN PASSWORD '${OSTF_DB_PW}'"
else
  echo "Creating role ${OSTF_DB_USER} with password ${OSTF_DB_PASSWD}"
  psql -h 127.0.0.1 -U ${DB_ROOT} -c "CREATE ROLE ${OSTF_DB_USER} WITH SUPERUSER LOGIN PASSWORD '${OSTF_DB_PW}'"
fi

echo "Dropping database ${OSTF_DB} if exists"
psql -h 127.0.0.1 -U ${DB_ROOT} -c "DROP DATABASE IF EXISTS ${OSTF_DB}"
echo "Creating database ${OSTF_DB}"
psql -h 127.0.0.1 -U ${DB_ROOT} -c "CREATE DATABASE ${OSTF_DB} OWNER ${OSTF_DB_USER}"