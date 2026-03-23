from database import engine
from sqlalchemy import inspect

def inspect_db():
    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    print("Columns in 'users' table:")
    for column in columns:
        print(f"- {column['name']} ({column['type']})")

if __name__ == "__main__":
    inspect_db()
