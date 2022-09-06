#!/bin/sh
set -e

# shellcheck disable=SC1091
. /app/.env

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "template1" <<-EOSQL
    CREATE EXTENSION pg_trgm;
    CREATE EXTENSION btree_gin;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER booklogger WITH PASSWORD '${BOOKLOGGER_PASSWORD}';
	CREATE DATABASE booklogger;
	GRANT ALL PRIVILEGES ON DATABASE booklogger TO booklogger;

    CREATE USER test_user WITH PASSWORD '${BOOKLOGGER_PASSWORD}' CREATEDB;
EOSQL
