from sqlalchemy import text, inspect
from database import engine

def migrate():
    inspector = inspect(engine)
    user_columns = [c['name'] for c in inspector.get_columns('users')]
    vital_columns = [c['name'] for c in inspector.get_columns('vital_signs')]
    
    with engine.connect() as conn:
        # Users Table Migrations
        if 'department' not in user_columns:
            print("Adding column 'department'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR;"))
        if 'bio' not in user_columns:
            print("Adding column 'bio'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT;"))
        if 'is_active' not in user_columns:
            print("Adding column 'is_active'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT FALSE;"))
            
        # VitalSigns Table Migrations
        if 'bmi' in vital_columns:
            # Check current type if possible, or just ensure it's FLOAT (in Postgres DOUBLE PRECISION)
            print("Converting 'bmi' column to FLOAT...")
            try:
                # This works for PostgreSQL
                conn.execute(text("ALTER TABLE vital_signs ALTER COLUMN bmi TYPE DOUBLE PRECISION;"))
            except Exception as e:
                print(f"Skipping BMI type conversion (might be SQLite or already done): {e}")
        
        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
