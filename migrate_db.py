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
            print("Converting 'bmi' column to FLOAT...")
            try:
                conn.execute(text("ALTER TABLE vital_signs ALTER COLUMN bmi TYPE DOUBLE PRECISION;"))
            except Exception as e:
                print(f"Skipping BMI type conversion: {e}")

        if 'temperature' in vital_columns:
            print("Converting 'temperature' column to FLOAT...")
            try:
                conn.execute(text("ALTER TABLE vital_signs ALTER COLUMN temperature TYPE DOUBLE PRECISION;"))
            except Exception as e:
                print(f"Skipping temperature type conversion: {e}")
        
        # StudentTasks Table Migrations
        st_columns = [c['name'] for c in inspector.get_columns('student_tasks')]
        if 'doctor_id' not in st_columns:
            print("Adding column 'doctor_id' to student_tasks...")
            try:
                conn.execute(text("ALTER TABLE student_tasks ADD COLUMN doctor_id INTEGER;"))
            except Exception as e:
                print(f"Error adding doctor_id: {e}")
        if 'file_url' not in st_columns:
            print("Adding column 'file_url' to student_tasks...")
            try:
              conn.execute(text("ALTER TABLE student_tasks ADD COLUMN file_url VARCHAR;"))
            except Exception as e:
                print(f"Error adding file_url: {e}")

        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
