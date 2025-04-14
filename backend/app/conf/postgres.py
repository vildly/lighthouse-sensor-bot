import psycopg2
import dotenv
import os
from contextlib import contextmanager
from pathlib import Path

dotenv.load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise


@contextmanager
def get_cursor():
    connection = get_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def init_db():
    """Initialize the database with required schemas if they don't exist."""
    try:
        # Check if tables already exist
        with get_cursor() as cursor:
            # Check if the llm_models table exists (as a proxy for checking if the schema is initialized)
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'llm_models'
                );
            """
            )

            tables_exist = cursor.fetchone()[0]  # type: ignore

            if not tables_exist:
                print(
                    "Database tables not found. Initializing database schema..."
                )

                # Get the path to the SQL schema file
                script_dir = Path(__file__).parent.resolve()
                project_root = script_dir.parent.parent
                schema_path = project_root / "postgres" / "backups" / "db_schemas.sql"

                # Read the SQL file
                with open(schema_path, 'r') as f:
                    sql_script = f.read()

                # Execute the SQL script
                cursor.execute(sql_script)

                print("Database schema initialized successfully.")
            else:
                print("Database schema already exists. Skipping initialization.")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
