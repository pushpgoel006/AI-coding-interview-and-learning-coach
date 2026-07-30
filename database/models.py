#helps defining table structure
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from database.db import Base
from  sqlalchemy.orm import relationship

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True)

    jd = Column(Text)

    question = Column(Text)

    answer = Column(Text)

    score = Column(Integer)

    followups= relationship(
        "Followup",
        back_populates="interview"
    )


class Followup(Base):
    __tablename__ = "followups"

    id=Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    interview_id=Column(
        String,
        ForeignKey("interviews.id")

    )

    question=Column(Text)
    answer=Column(Text)
    score=Column(Integer)
    followup_number= Column(Integer)
    interview = relationship(
        "Interview",
        back_populates="followups"
    )
    