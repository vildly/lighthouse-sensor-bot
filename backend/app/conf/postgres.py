import psycopg2
import dotenv
import os
from contextlib import contextmanager

dotenv.load_dotenv()

def get_connection():
    try:
        print("Current working directory:", os.getcwd())
        print("Environment variables loaded:")
        print("DB_HOST=", os.getenv('DB_HOST'))
        print("DB_PORT=", os.getenv('DB_PORT'))
        print("DB_NAME=", os.getenv('DB_NAME'))
        print("DB_USER=", os.getenv('DB_USER'))
        
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        print("Database connection successful!")
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