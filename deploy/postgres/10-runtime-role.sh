#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v ON_ERROR_STOP=1 -v runtime_password="$REKNYX_RUNTIME_PASSWORD" <<'SQL'
CREATE ROLE reknyx_runtime NOLOGIN;
SELECT format('CREATE ROLE reknyx_app LOGIN PASSWORD %L', :'runtime_password') \gexec
GRANT reknyx_runtime TO reknyx_app;
SQL
