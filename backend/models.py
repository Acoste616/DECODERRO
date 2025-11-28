from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship
from backend.database import Base
import time

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000))
    status = Column(String, default="active") # active, closed
    outcome = Column(String, nullable=True) # sale, no_sale
    journey_stage = Column(String, default="DISCOVERY")
    last_updated = Column(BigInteger, default=lambda: int(time.time() * 1000))

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    analysis_state = relationship("AnalysisState", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String) # user, ai, system
    content = Column(String)
    timestamp = Column(BigInteger, default=lambda: int(time.time() * 1000))
    
    # AI Metadata stored as JSON
    confidence = Column(Float, nullable=True)
    confidence_reason = Column(String, nullable=True)
    client_style = Column(String, nullable=True)
    context_needs = Column(JSON, nullable=True)
    suggested_actions = Column(JSON, nullable=True)
    
    # Feedback
    feedback = Column(String, nullable=True)
    feedback_details = Column(String, nullable=True)

    session = relationship("Session", back_populates="messages")

class AnalysisState(Base):
    __tablename__ = "analysis_states"

    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    
    # Storing the entire nested analysis object as JSON for flexibility
    # This matches the AnalysisState interface in types.ts
    data = Column(JSON) 
    
    last_updated = Column(BigInteger, default=lambda: int(time.time() * 1000))

    session = relationship("Session", back_populates="analysis_state")
