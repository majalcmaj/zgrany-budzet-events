import os
from main import app, db

def init_database():
    """
    Initialize the database by executing create_tables.sql and populate.sql.
    """
    with app.app_context():
        # Paths to SQL files
        base_dir = os.path.dirname(os.path.abspath(__file__))
        create_tables_path = os.path.join(base_dir, 'sql_scripts', 'create_tables.sql')
        populate_path = os.path.join(base_dir, 'sql_scripts', 'populate.sql')

        # Check if files exist
        if not os.path.exists(create_tables_path):
            print(f"Error: {create_tables_path} not found.")
            return
        if not os.path.exists(populate_path):
            print(f"Error: {populate_path} not found.")
            return

        # Get the raw SQLite connection to use executescript
        # This allows executing multiple SQL statements at once
        with db.engine.connect() as connection:
            raw_connection = connection.connection
            cursor = raw_connection.cursor()

            try:
                print("Creating tables...")
                with open(create_tables_path, 'r', encoding='utf-8') as f:
                    create_sql = f.read()
                    cursor.executescript(create_sql)
                
                print("Populating database...")
                with open(populate_path, 'r', encoding='utf-8') as f:
                    populate_sql = f.read()
                    cursor.executescript(populate_sql)
                
                raw_connection.commit()
                print("Database initialized successfully!")
                
            except Exception as e:
                raw_connection.rollback()
                print(f"An error occurred: {e}")

if __name__ == '__main__':
    init_database()
