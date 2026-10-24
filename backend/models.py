import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import relationship
from database import Base


def utc_now():
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """User account model for authentication and relations."""
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    financial_profile = relationship("FinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    financial_goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class FinancialProfile(Base):
    """User's core financial profile metrics and preferences."""
    __tablename__ = "financial_profiles"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    annual_income = Column(Float, default=0.0, nullable=False)
    monthly_expenses = Column(Float, default=0.0, nullable=False)
    savings = Column(Float, default=0.0, nullable=False)
    risk_tolerance = Column(String(50), default="moderate", nullable=False)  # conservative, moderate, aggressive
    investment_experience = Column(String(50), default="beginner", nullable=False)  # beginner, intermediate, advanced
    time_horizon = Column(Integer, default=5, nullable=False)  # in years
    age = Column(Integer, default=28, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="financial_profile")


class Transaction(Base):
    """Income and expense transactions."""
    __tablename__ = "transactions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # income, expense
    description = Column(String(255), nullable=True)
    date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="transactions")


class Debt(Base):
    """Debt obligations and loan details."""
    __tablename__ = "debts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    debt_type = Column(String(50), nullable=False)  # credit_card, education_loan, personal_loan, mortgage, etc.
    balance = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)  # annual percentage, e.g. 8.5
    minimum_payment = Column(Float, nullable=False)  # monthly minimum
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="debts")


class FinancialGoal(Base):
    """Financial milestones and savings targets."""
    __tablename__ = "financial_goals"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    timeline_months = Column(Integer, nullable=False)
    priority = Column(Integer, default=3, nullable=False)  # 1 (highest) to 5 (lowest)
    current_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="financial_goals")


class AnalysisResult(Base):
    """Saved AI financial plan and analysis snapshot."""
    __tablename__ = "analysis_results"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    input_snapshot = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    plan_markdown = Column(Text, nullable=True)
    workflow_trace = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="analysis_results")


class ChatMessage(Base):
    """Educational chat dialog history."""
    __tablename__ = "chat_messages"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Uuid, nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="chat_messages")
