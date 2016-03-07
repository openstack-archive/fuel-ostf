#!/bin/sh

echo "Preparing pgpass file ${DB_ROOTPGPASS}"
echo "*:*:*:${OSTF_DB_ROOT}:${OSTF_DB_ROOTPW}" > ${OSTF_DB_ROOTPGPASS}
chmod 600 ${OSTF_DB_ROOTPGPASS}

export PGPASSFILE=${OSTF_DB_ROOTPGPASS}
cat $PGPASSFIL
