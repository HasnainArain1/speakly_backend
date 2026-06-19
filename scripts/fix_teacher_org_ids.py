import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    load_dotenv(dotenv_path="app/.env")
    DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Let's find any teacher users whose organization_id is NULL, but their email is whitelisted
    cursor.execute("""
        SELECT u.id, u.email, a.organization_id 
        FROM users u 
        JOIN allowed_students a ON u.email = a.email 
        WHERE u.role = 'teacher' AND u.organization_id IS NULL;
    """)
    rows = cursor.fetchall()
    print("Found teachers with NULL organization_id:")
    for r in rows:
        print(r)
        
    # Update them
    for r in rows:
        user_id, email, org_id = r
        print(f"Updating organization_id for {email} to {org_id}...")
        cursor.execute("UPDATE users SET organization_id = %s WHERE id = %s;", (org_id, user_id))
    
    conn.commit()
    print("Update complete.")
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
