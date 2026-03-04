from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Create a "data" folder in the main project directory to hold the database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# The URL tells SQLAlchemy where the database file will live
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'database.db')}"

# Create the engine. The 'check_same_thread' argument is specifically needed for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a factory that generates database sessions (how we talk to the database)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This Base class is what all our database models will inherit from
Base = declarative_base()

# A helpful function we will use later in FastAPI to get a database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()