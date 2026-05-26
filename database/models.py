#helps defining table structure

from sqlalchemy import Column, String, Integer, Text

from database.db import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True)

    jd = Column(Text)

    question = Column(Text)

    answer = Column(Text)

    score = Column(Integer)