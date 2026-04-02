from sqlalchemy import text, inspect
from database import engine

def migrate():
    print("MIGRATION: Starting database migration...")
    inspector = inspect(engine)
    
    # Get all tables
    tables = inspector.get_table_names()
    print(f"MIGRATION: Found tables: {tables}")

    if 'vital_signs' not in tables:
        print("MIGRATION: vital_signs table missing! models.Base.metadata.create_all should handle this.")
        return

    vital_columns = [c['name'] for c in inspector.get_columns('vital_signs')]
    print(f"MIGRATION: vital_signs columns: {vital_columns}")
    
    with engine.connect() as conn:
        # Helper to safely add column
        def add_column_if_missing(table, column, definition, default_val=None):
            if column not in [c['name'] for c in inspect(engine).get_columns(table)]:
                print(f"MIGRATION: Adding column '{column}' to '{table}'...")
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition};"))
                    if default_val is not None:
                        conn.execute(text(f"UPDATE {table} SET {column} = {default_val} WHERE {column} IS NULL;"))
                    conn.commit()
                    print(f"MIGRATION: Successfully added '{column}'.")
                except Exception as e:
                    print(f"MIGRATION: Failed to add '{column}': {e}")
            else:
                print(f"MIGRATION: Column '{column}' already exists in '{table}'.")

        # 1. Vital Signs Table
        add_column_if_missing('vital_signs', 'blood_glucose', 'INTEGER', 0)
        add_column_if_missing('vital_signs', 'respiratory_rate', 'INTEGER', 16)
        add_column_if_missing('vital_signs', 'oxygen_saturation', 'INTEGER', 98)
        add_column_if_missing('vital_signs', 'bmi', 'DOUBLE PRECISION', 0.0)
        add_column_if_missing('vital_signs', 'temperature', 'DOUBLE PRECISION', 98.6)

        # 2. Users Table
        user_columns = [c['name'] for c in inspector.get_columns('users')]
        add_column_if_missing('users', 'department', 'VARCHAR', "Primary Care")
        add_column_if_missing('users', 'bio', 'TEXT', "")
        add_column_if_missing('users', 'is_active', 'BOOLEAN', 'FALSE')
        add_column_if_missing('users', 'reset_code', 'VARCHAR(6)', 'NULL')
        add_column_if_missing('users', 'reset_code_expires_at', 'TIMESTAMP WITH TIME ZONE', 'NULL')

        # 3. Student Tasks
        add_column_if_missing('student_tasks', 'doctor_id', 'INTEGER', 0)
        add_column_if_missing('student_tasks', 'file_url', 'VARCHAR', "")

        print("MIGRATION: All migration steps finished.")

if __name__ == "__main__":
    migrate()
