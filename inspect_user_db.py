import sqlite3
import os

db_path = r'c:\development\graduation_backend\graduation.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} does not exist.")
else:
    print(f"Checking database: {db_path}")
    print(f"File size: {os.path.getsize(db_path)} bytes")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Found tables: {tables}")
        
        if 'users' in tables:
            print("\nSearching for users...")
            cursor.execute("SELECT * FROM users WHERE email='do44122032@cihanuniversity.edu.iq'")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(users)")
            cols = [c[1] for c in cursor.fetchall()]
            print(f"Columns: {cols}")
            
            if rows:
                for row in rows:
                    user_dict = dict(zip(cols, row))
                    # Mask password for security if needed, but here it's likely plaintext or hashed
                    print(f"User Found: {user_dict}")
            else:
                print("No user found with email 'do44122032@cihanuniversity.edu.iq'")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
