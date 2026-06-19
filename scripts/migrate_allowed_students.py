import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # try another path
    load_dotenv(dotenv_path="app/.env")
    DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL:", DATABASE_URL)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if allowed_students table has 'role' column
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='allowed_students' AND column_name='role';
    """)
    res = cursor.fetchone()
    if not res:
        print("Adding 'role' column to allowed_students table...")
        cursor.execute("ALTER TABLE allowed_students ADD COLUMN role VARCHAR(20) DEFAULT 'student';")
        conn.commit()
        print("'role' column added successfully.")
    else:
        print("'role' column already exists.")
        
    # Let's inspect the current allowed_students rows
    cursor.execute("SELECT id, email, role FROM allowed_students;")
    rows = cursor.fetchall()
    print("Whitelisted users:")
    for r in rows:
        print(r)
        
    cursor.close()
    conn.close()
except Exception as e:
    print("Error during migration:", e)
