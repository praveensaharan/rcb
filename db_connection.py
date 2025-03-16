import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get connection details from environment variables
HOST = os.getenv('NEON_DB_HOST')
PORT = os.getenv('NEON_DB_PORT', 5432)  # Default PostgreSQL port
DATABASE = os.getenv('NEON_DB_DATABASE')
USER = os.getenv('NEON_DB_USER')
PASSWORD = os.getenv('NEON_DB_PASSWORD')


def connect_to_db():
    """Establish and return a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD
        )
        print("Connection to the database established successfully.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
