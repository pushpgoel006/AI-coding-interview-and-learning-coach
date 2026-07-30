#helps in connection sqlite, create engine and save sessions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Helps set up database
DATABASE_URL = "sqlite:///./interviews.db"

# engine acts as  a manager between python and sqlite
engine = create_engine(DATABASE_URL)

# temp converstiaon withdatabase
SessionLocal = sessionmaker(bind=engine)

# a base class needed whenever you need to create a class
Base = declarative_base()