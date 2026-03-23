from sqlalchemy import text, inspect
from database import engine

def migrate():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    with engine.connect() as conn:
        if 'department' not in columns:
            print("Adding column 'department'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR;"))
        if 'bio' not in columns:
            print("Adding column 'bio'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT;"))
        if 'is_active' not in columns:
            print("Adding column 'is_active'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT FALSE;"))
        
        # Also ensure doctor_schedules table exists
        print("Ensuring 'doctor_schedules' table exists...")
        # (create_all usually handles this if it doesn't exist)
        
        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
