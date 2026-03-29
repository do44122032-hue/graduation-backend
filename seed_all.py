from seed_students import seed_students
from seed_doctors import seed_doctors
from seed_courses import seed_courses
import models
from database import engine

def main():
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    
    print("\nSeeding Students...")
    seed_students()
    
    print("\nSeeding Doctors...")
    seed_doctors()
    
    print("\nSeeding Courses...")
    seed_courses()
    
    print("\nDone! Local database is ready.")

if __name__ == "__main__":
    main()
