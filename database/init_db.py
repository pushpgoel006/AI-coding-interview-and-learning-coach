import os

from sqlalchemy import create_engine

from database.db import engine, Base, DATABASE_URL, _with_psycopg_driver

from database.models import Interview

schema_url = _with_psycopg_driver(os.getenv("DATABASE_URL_UNPOOLED", DATABASE_URL))
schema_engine = engine if schema_url == DATABASE_URL else create_engine(schema_url)

Base.metadata.create_all(bind=schema_engine)

print("Database created successfully")
