import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# Auth & User Schemas
# ============================================================
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================
# Financial Profile Schemas
# ============================================================
class FinancialProfileBase(BaseModel):
    annual_income: float = Field(ge=0.0, default=0.0)
    monthly_expenses: float = Field(ge=0.0, default=0.0)
    savings: float = Field(ge=0.0, default=0.0)
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    investment_experience: Literal["beginner", "intermediate", "advanced"] = "beginner"
    time_horizon: int = Field(ge=1, default=5)
    age: int = Field(ge=18, le=120, default=28)
    currency: str = "INR"


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileUpdate(BaseModel):
    annual_income: Optional[float] = Field(default=None, ge=0.0)
    monthly_expenses: Optional[float] = Field(default=None, ge=0.0)
    savings: Optional[float] = Field(default=None, ge=0.0)
    risk_tolerance: Optional[Literal["conservative", "moderate", "aggressive"]] = None
    investment_experience: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    time_horizon: Optional[int] = Field(default=None, ge=1)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    currency: Optional[str] = None


class FinancialProfileResponse(FinancialProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Debt Schemas
# ============================================================
class DebtBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    debt_type: str = Field(default="personal_loan", max_length=50)
    balance: float = Field(ge=0.0)
    interest_rate: float = Field(ge=0.0, le=100.0)
    minimum_payment: float = Field(ge=0.0)


class DebtCreate(DebtBase):
    pass


class DebtUpdate(BaseModel):
    name: Optional[str] = None
    debt_type: Optional[str] = None
    balance: Optional[float] = Field(default=None, ge=0.0)
    interest_rate: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    minimum_payment: Optional[float] = Field(default=None, ge=0.0)


class DebtResponse(DebtBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Financial Goal Schemas
# ============================================================
class GoalBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0.0)
    timeline_months: int = Field(ge=1)
    priority: int = Field(ge=1, le=5, default=3)
    current_amount: float = Field(ge=0.0, default=0.0)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = Field(default=None, gt=0.0)
    timeline_months: Optional[int] = Field(default=None, ge=1)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    current_amount: Optional[float] = Field(default=None, ge=0.0)


class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Onboarding Setup Schema (Profile + Debts + Goals in one go)
# ============================================================
class OnboardingSetupRequest(BaseModel):
    profile: FinancialProfileCreate
    debts: Optional[List[DebtCreate]] = Field(default_factory=list)
    goals: Optional[List[GoalCreate]] = Field(default_factory=list)


# ============================================================
# Transaction Schemas
# ============================================================
class TransactionBase(BaseModel):
    amount: float
    category: str = Field(min_length=1, max_length=100)
    type: Literal["income", "expense"]
    description: Optional[str] = Field(default=None, max_length=255)
    date: Optional[datetime] = None
    is_recurring: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionBulkCreate(BaseModel):
    transactions: List[TransactionCreate]


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class TransactionSummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_cash_flow: float
    savings_rate: float
    transaction_count: int
    category_breakdown: Dict[str, float]


# ============================================================
# AI Analysis & Chat Schemas
# ============================================================
class AnalyzeRequest(BaseModel):
    message: Optional[str] = Field(default=None, description="Optional user inquiry or instruction")
    analysis_type: Optional[str] = Field(
        default=None,
        description="Optional explicit analysis type: income_expense, budget_planning, investment_advice, debt_optimization, financial_education, comprehensive",
    )


class AnalyzeResponse(BaseModel):
    analysis_type: str
    plan_markdown: str
    insights: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    workflow_trace: List[Dict[str, Any]] = Field(default_factory=list)
    agent_flow: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class AnalysisHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_type: str
    plan_markdown: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    workflow_trace: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
