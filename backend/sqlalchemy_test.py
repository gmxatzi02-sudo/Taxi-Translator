# sqlalchemy_test.py - simple learning file

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Base class - every model inherits from this
Base = declarative_base()

# 2. Define a table (model)
class Person(Base):
    __tablename__ = "people"           # table name in database

    id = Column(Integer, primary_key=True)      # auto-increment ID
    name = Column(String, nullable=False)       # required field
    age = Column(Integer)                       # optional field
    city = Column(String, default="Athens")     # default value

# 3. Create engine (connection to SQLite file)
engine = create_engine("sqlite:///test_people.db", echo=True)  # echo=True shows SQL logs

# 4. Create the table in the file (only needed once)
Base.metadata.create_all(engine)

# 5. Create a session factory
SessionLocal = sessionmaker(bind=engine)

# ── Now let's use it ──────────────────────────────────────────────────────────

# Open a session (like opening a transaction)
session = SessionLocal()

try:
    # Create a new person
    new_person = Person(name="Maria", age=28, city="Thessaloniki")
    session.add(new_person)               # stage it
    session.commit()                      # save to disk
    print("Added Maria!")

    # Read all people
    all_people = session.query(Person).all()
    for p in all_people:
        print(f"ID: {p.id}, Name: {p.name}, Age: {p.age}, City: {p.city}")

except Exception as e:
    session.rollback()                    # undo if error
    print("Error:", e)

finally:
    session.close()                       # always close session