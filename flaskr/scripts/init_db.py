import os
import sqlite3


def init_database() -> None:
    """
    Initialize the database by executing create_tables.sql and populate.sql.
    This script is standalone and does not depend on the Flask app.
    """
    # Base directory (flaskr/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Project root (parent of flaskr/)
    project_root = os.path.dirname(base_dir)

    # Database path (instance/zgrany_budget.db)
    instance_dir = os.path.join(project_root, "instance")
    db_path = os.path.join(instance_dir, "zgrany_budget.db")

    # Ensure instance directory exists
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created directory: {instance_dir}")

    # Paths to SQL files
    create_tables_path = os.path.join(base_dir, "sql", "create_tables.sql")
    populate_path = os.path.join(base_dir, "sql", "populate.sql")

    # Check if SQL files exist
    if not os.path.exists(create_tables_path):
        print(f"Error: {create_tables_path} not found.")
        return
    if not os.path.exists(populate_path):
        print(f"Error: {populate_path} not found.")
        return

    conn = None
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Connected to database at: {db_path}")

        print("Creating tables...")
        with open(create_tables_path, "r", encoding="utf-8") as f:
            create_sql = f.read()
            cursor.executescript(create_sql)

        print("Populating database...")
        with open(populate_path, "r", encoding="utf-8") as f:
            populate_sql = f.read()
            cursor.executescript(populate_sql)

        conn.commit()
        print("Database initialized successfully!")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    init_database()
