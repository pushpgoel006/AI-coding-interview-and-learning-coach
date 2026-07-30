from database.db import engine, Base

from database.models import Interview

Base.metadata.create_all(bind=engine)

print("Database created successfully")