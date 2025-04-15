#!/bin/bash
set -e

# Check if llm_models table already exists
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'llm_models'
  );
EOSQL

# If the table doesn't exist (exit code 1), run the schema file
if [ $? -eq 1 ]; then
  echo "Database tables not found. Initializing database schema..."
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/db_schemas.sql
  echo "Database schema initialized successfully."
else
  echo "Database schema already exists. Skipping initialization."
fi