#!/bin/bash
set -e

# Check if llm_models table already exists and capture the actual result
TABLE_EXISTS=$(psql -t -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'llm_models'
  );" | grep -v '^$')

# Trim whitespace
TABLE_EXISTS=$(echo "$TABLE_EXISTS" | xargs)

echo "Table existence check result: '$TABLE_EXISTS'"

# Check the actual result (t for true, f for false)
if [ "$TABLE_EXISTS" = "f" ]; then
  echo "Database tables not found. Initializing database schema..."
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/db_schemas.sql
  
  # Run the insert_models.sql script to populate the llm_models table
  echo "Populating llm_models table with initial data..."
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/insert_models.sql
  
  echo "Database schema and initial data initialized successfully."
else
  echo "Database schema already exists. Checking if llm_models table has data..."
  
  # Check if llm_models table is empty
  MODELS_COUNT=$(psql -t -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "SELECT COUNT(*) FROM llm_models;")
  
  if [ "$MODELS_COUNT" -eq "0" ]; then
    echo "llm_models table is empty. Populating with initial data..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/insert_models.sql
    echo "Initial data loaded successfully."
  else
    echo "llm_models table already has data. Skipping initialization."
  fi
fi