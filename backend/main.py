import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import create_access_token, get_current_user, get_password_hash, verify_password
from config import settings
from database import get_db, init_db
from graph.workflow import create_financial_workflow
from agents.financial_educator import FinancialEducatorAgent
import models
import schemas

# Setup application logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("finwise.api")

# Initialize AI workflow and agents
workflow_engine = create_financial_workflow()
financial_educator = FinancialEducatorAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing FinWise Backend services...")
    init_db()
    yield
    logger.info("FinWise Backend services shut down.")


app = FastAPI(
    title="FinWise Personal Finance AI Agent API",
    description="Backend API powering multi-agent financial planning, budgeting, debt optimization, and financial education.",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check
# ============================================================
@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint indicating server and service connectivity."""
    db_status = "connected"
    try:
        db.execute(func.now())
    except Exception as exc:
        logger.warning("Database ping warning: %s", exc)
        db_status = "disconnected"

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": settings.is_gemini_available(),
        "database": db_status,
        "default_currency": settings.CURRENCY_DEFAULT,
    }


# ============================================================
# Auth Routes
# ============================================================
@app.post(
    "/api/auth/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account with hashed password and return JWT access token."""
    existing = db.query(models.User).filter(models.User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = models.User(
        email=user_in.email.lower(),
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
    )
    db.add(new_user)
    db.flush()

    # Create empty default profile for newly registered user
    default_profile = models.FinancialProfile(
        user_id=new_user.id,
        annual_income=0.0,
        monthly_expenses=0.0,
        savings=0.0,
        currency=settings.CURRENCY_DEFAULT,
    )
    db.add(default_profile)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id), "user_id": str(new_user.id)})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(new_user),
    )


@app.post("/api/auth/login", response_model=schemas.TokenResponse, tags=["Authentication"])
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate email and password, returning a 24-hour JWT token."""
    user = db.query(models.User).filter(models.User.email == credentials.email.lower()).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id), "user_id": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user),
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse, tags=["Authentication"])
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """Get the authenticated user's account details."""
    return schemas.UserResponse.model_validate(current_user)


# ============================================================
# Profile Routes
# ============================================================
@app.get("/api/profile", response_model=schemas.FinancialProfileResponse, tags=["Profile"])
def get_financial_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the financial profile for the current authenticated user."""
    profile = db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.FinancialProfile(user_id=current_user.id, currency=settings.CURRENCY_DEFAULT)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return schemas.FinancialProfileResponse.model_validate(profile)


@app.put("/api/profile", response_model=schemas.FinancialProfileResponse, tags=["Profile"])
def update_financial_profile(
    profile_update: schemas.FinancialProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update financial parameters for the current authenticated user."""
    profile = db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.FinancialProfile(user_id=current_user.id)
        db.add(profile)

    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return schemas.FinancialProfileResponse.model_validate(profile)


@app.post("/api/profile/setup", tags=["Profile"])
def setup_onboarding_profile(
    setup_req: schemas.OnboardingSetupRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initial onboarding setup: sets up profile, debts, and goals in a single atomic transaction."""
    # 1. Update or create profile
    profile = db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.FinancialProfile(user_id=current_user.id)
        db.add(profile)

    for field, val in setup_req.profile.model_dump().items():
        setattr(profile, field, val)

    # 2. Add initial debts if provided
    created_debts = []
    if setup_req.debts:
        for d_in in setup_req.debts:
            debt = models.Debt(
                user_id=current_user.id,
                name=d_in.name,
                debt_type=d_in.debt_type,
                balance=d_in.balance,
                interest_rate=d_in.interest_rate,
                minimum_payment=d_in.minimum_payment,
            )
            db.add(debt)
            created_debts.append(debt)

    # 3. Add initial goals if provided
    created_goals = []
    if setup_req.goals:
        for g_in in setup_req.goals:
            goal = models.FinancialGoal(
                user_id=current_user.id,
                name=g_in.name,
                target_amount=g_in.target_amount,
                timeline_months=g_in.timeline_months,
                priority=g_in.priority,
                current_amount=g_in.current_amount,
            )
            db.add(goal)
            created_goals.append(goal)

    db.commit()
    db.refresh(profile)

    return {
        "message": "Onboarding profile setup completed successfully.",
        "profile": schemas.FinancialProfileResponse.model_validate(profile),
        "debts_count": len(created_debts),
        "goals_count": len(created_goals),
    }


# ============================================================
# Transaction Routes
# ============================================================
@app.get("/api/transactions", response_model=List[schemas.TransactionResponse], tags=["Transactions"])
def list_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    txn_type: Optional[str] = Query(None, alias="type"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve list of user transactions with optional category, type filters and pagination."""
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    if category:
        query = query.filter(models.Transaction.category.ilike(f"%{category}%"))
    if txn_type:
        query = query.filter(models.Transaction.type == txn_type.lower())

    transactions = query.order_by(models.Transaction.date.desc()).offset(offset).limit(limit).all()
    return [schemas.TransactionResponse.model_validate(t) for t in transactions]


@app.post(
    "/api/transactions",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Transactions"],
)
def create_transaction(
    txn_in: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log a single financial transaction (income or expense)."""
    txn = models.Transaction(
        user_id=current_user.id,
        amount=txn_in.amount,
        category=txn_in.category.strip(),
        type=txn_in.type.lower(),
        description=txn_in.description,
        date=txn_in.date or datetime.now(timezone.utc),
        is_recurring=txn_in.is_recurring,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return schemas.TransactionResponse.model_validate(txn)


@app.post("/api/transactions/bulk", status_code=status.HTTP_201_CREATED, tags=["Transactions"])
def bulk_create_transactions(
    bulk_in: schemas.TransactionBulkCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk import an array of transactions in a single operation."""
    created_txns = []
    for item in bulk_in.transactions:
        txn = models.Transaction(
            user_id=current_user.id,
            amount=item.amount,
            category=item.category.strip(),
            type=item.type.lower(),
            description=item.description,
            date=item.date or datetime.now(timezone.utc),
            is_recurring=item.is_recurring,
        )
        db.add(txn)
        created_txns.append(txn)

    db.commit()
    return {
        "message": f"Successfully imported {len(created_txns)} transactions.",
        "count": len(created_txns),
    }


@app.get("/api/transactions/summary", response_model=schemas.TransactionSummaryResponse, tags=["Transactions"])
def get_transactions_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate aggregated transaction metrics including total income, expenses, and category breakdown."""
    txns = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()

    total_income = sum(t.amount for t in txns if t.type == "income" or (t.amount > 0 and t.type != "expense"))
    total_expenses = sum(abs(t.amount) for t in txns if t.type == "expense" or t.amount < 0)
    net_cash_flow = total_income - total_expenses
    savings_rate = ((net_cash_flow / total_income) * 100.0) if total_income > 0 else 0.0

    cat_breakdown: Dict[str, float] = {}
    for t in txns:
        if t.type == "expense" or t.amount < 0:
            cat = t.category.title()
            cat_breakdown[cat] = cat_breakdown.get(cat, 0.0) + abs(t.amount)

    return schemas.TransactionSummaryResponse(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_cash_flow=round(net_cash_flow, 2),
        savings_rate=round(savings_rate, 1),
        transaction_count=len(txns),
        category_breakdown={k: round(v, 2) for k, v in cat_breakdown.items()},
    )


# ============================================================
# Debt Routes
# ============================================================
@app.get("/api/debts", response_model=List[schemas.DebtResponse], tags=["Debts"])
def list_debts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all debts and loans belonging to the authenticated user."""
    debts = db.query(models.Debt).filter(models.Debt.user_id == current_user.id).order_by(models.Debt.interest_rate.desc()).all()
    return [schemas.DebtResponse.model_validate(d) for d in debts]


@app.post("/api/debts", response_model=schemas.DebtResponse, status_code=status.HTTP_201_CREATED, tags=["Debts"])
def create_debt(
    debt_in: schemas.DebtCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new debt obligation."""
    debt = models.Debt(
        user_id=current_user.id,
        name=debt_in.name.strip(),
        debt_type=debt_in.debt_type.strip(),
        balance=debt_in.balance,
        interest_rate=debt_in.interest_rate,
        minimum_payment=debt_in.minimum_payment,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return schemas.DebtResponse.model_validate(debt)


@app.put("/api/debts/{debt_id}", response_model=schemas.DebtResponse, tags=["Debts"])
def update_debt(
    debt_id: uuid.UUID,
    debt_update: schemas.DebtUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update details or balance of an existing debt."""
    debt = db.query(models.Debt).filter(models.Debt.id == debt_id, models.Debt.user_id == current_user.id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found.")

    for field, val in debt_update.model_dump(exclude_unset=True).items():
        setattr(debt, field, val)

    db.commit()
    db.refresh(debt)
    return schemas.DebtResponse.model_validate(debt)


@app.delete("/api/debts/{debt_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Debts"])
def delete_debt(
    debt_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a debt record."""
    debt = db.query(models.Debt).filter(models.Debt.id == debt_id, models.Debt.user_id == current_user.id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found.")

    db.delete(debt)
    db.commit()
    return None


# ============================================================
# Goal Routes
# ============================================================
@app.get("/api/goals", response_model=List[schemas.GoalResponse], tags=["Goals"])
def list_goals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List financial goals for current user."""
    goals = db.query(models.FinancialGoal).filter(models.FinancialGoal.user_id == current_user.id).order_by(models.FinancialGoal.priority.asc()).all()
    return [schemas.GoalResponse.model_validate(g) for g in goals]


@app.post("/api/goals", response_model=schemas.GoalResponse, status_code=status.HTTP_201_CREATED, tags=["Goals"])
def create_goal(
    goal_in: schemas.GoalCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new savings or milestone goal."""
    goal = models.FinancialGoal(
        user_id=current_user.id,
        name=goal_in.name.strip(),
        target_amount=goal_in.target_amount,
        timeline_months=goal_in.timeline_months,
        priority=goal_in.priority,
        current_amount=goal_in.current_amount,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return schemas.GoalResponse.model_validate(goal)


@app.put("/api/goals/{goal_id}", response_model=schemas.GoalResponse, tags=["Goals"])
def update_goal(
    goal_id: uuid.UUID,
    goal_update: schemas.GoalUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update milestone targets, timeline, or saved balance for a financial goal."""
    goal = db.query(models.FinancialGoal).filter(models.FinancialGoal.id == goal_id, models.FinancialGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial goal not found.")

    for field, val in goal_update.model_dump(exclude_unset=True).items():
        setattr(goal, field, val)

    db.commit()
    db.refresh(goal)
    return schemas.GoalResponse.model_validate(goal)


@app.delete("/api/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Goals"])
def delete_goal(
    goal_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a financial goal."""
    goal = db.query(models.FinancialGoal).filter(models.FinancialGoal.id == goal_id, models.FinancialGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial goal not found.")

    db.delete(goal)
    db.commit()
    return None


# ============================================================
# AI Analysis Routes
# ============================================================
@app.post("/api/analyze", response_model=schemas.AnalyzeResponse, tags=["AI Analysis"])
def run_financial_analysis(
    req: schemas.AnalyzeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger the multi-agent LangGraph workflow against the user's financial profile."""
    # 1. Load user data from DB
    profile = db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == current_user.id).first()
    debts = db.query(models.Debt).filter(models.Debt.user_id == current_user.id).all()
    goals = db.query(models.FinancialGoal).filter(models.FinancialGoal.user_id == current_user.id).all()
    txns = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).order_by(models.Transaction.date.desc()).limit(100).all()

    # 2. Build profile dictionary snapshot for agents
    profile_dict: Dict[str, Any] = {
        "age": profile.age if profile else 28,
        "annual_income": profile.annual_income if profile else 0.0,
        "monthly_expenses": profile.monthly_expenses if profile else 0.0,
        "savings": profile.savings if profile else 0.0,
        "risk_tolerance": profile.risk_tolerance if profile else "moderate",
        "investment_experience": profile.investment_experience if profile else "beginner",
        "time_horizon": profile.time_horizon if profile else 5,
        "currency": profile.currency if profile else settings.CURRENCY_DEFAULT,
        "debts": [
            {
                "name": d.name,
                "debt_type": d.debt_type,
                "balance": d.balance,
                "interest_rate": d.interest_rate,
                "minimum_payment": d.minimum_payment,
            }
            for d in debts
        ],
        "financial_goals": [
            {
                "name": g.name,
                "target_amount": g.target_amount,
                "target": g.target_amount,
                "timeline_months": g.timeline_months,
                "priority": g.priority,
                "current_amount": g.current_amount,
            }
            for g in goals
        ],
        "transactions": [
            {
                "amount": t.amount,
                "category": t.category,
                "type": t.type,
                "description": t.description,
                "date": t.date.isoformat() if t.date else None,
                "is_recurring": t.is_recurring,
            }
            for t in txns
        ],
    }

    user_query = req.message or "Analyze my finances and provide an optimized financial plan"
    options = {}
    if req.analysis_type:
        options["analysis_type"] = req.analysis_type

    # 3. Execute LangGraph workflow
    workflow_state = workflow_engine.process_request(
        user_input=user_query,
        user_profile=profile_dict,
        options=options,
    )

    final_output = workflow_state.get("final_output") or {}
    plan_markdown = ""
    insights = []
    metrics = {}

    if isinstance(final_output, dict):
        plan_markdown = final_output.get("response") or ""
        insights = final_output.get("insights") or []
        plan_data = final_output.get("plan") or {}
        metrics = plan_data.get("key_metrics") or {}
    elif isinstance(final_output, str):
        plan_markdown = final_output

    workflow_trace = workflow_state.get("workflow_trace") or []
    agent_flow = [str(step.get("agent")) for step in workflow_trace if step.get("agent")]
    analysis_type_val = str(workflow_state.get("current_analysis", {}).get("type") or "comprehensive")

    # 4. Save analysis result in DB
    try:
        saved_result = models.AnalysisResult(
            user_id=current_user.id,
            analysis_type=analysis_type_val,
            input_snapshot={"query": user_query, "profile": {k: v for k, v in profile_dict.items() if k != "transactions"}},
            result_data=final_output if isinstance(final_output, dict) else {"response": plan_markdown},
            plan_markdown=plan_markdown,
            workflow_trace=workflow_trace,
        )
        db.add(saved_result)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to save analysis result to database: %s", exc)

    return schemas.AnalyzeResponse(
        analysis_type=analysis_type_val,
        plan_markdown=plan_markdown,
        insights=insights,
        metrics=metrics,
        workflow_trace=workflow_trace,
        agent_flow=agent_flow,
    )


@app.post("/api/chat", response_model=schemas.ChatResponse, tags=["AI Chat"])
def educational_chat(
    req: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Engage in educational financial Q&A powered by the Financial Educator agent."""
    session_uuid = uuid.UUID(req.session_id) if req.session_id else uuid.uuid4()

    # 1. Log incoming user message
    user_msg = models.ChatMessage(
        user_id=current_user.id,
        session_id=session_uuid,
        role="user",
        content=req.message.strip(),
    )
    db.add(user_msg)

    # 2. Extract profile context
    profile = db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == current_user.id).first()
    profile_summary = {
        "age": profile.age if profile else 28,
        "risk_tolerance": profile.risk_tolerance if profile else "moderate",
        "investment_experience": profile.investment_experience if profile else "beginner",
    }

    # 3. Ask Financial Educator Agent
    result = financial_educator.explain_concept(req.message, profile_summary)
    response_text = result.get("explanation", "I am currently unable to answer that question.")

    # 4. Log assistant response
    assistant_msg = models.ChatMessage(
        user_id=current_user.id,
        session_id=session_uuid,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)
    db.commit()

    return schemas.ChatResponse(
        response=response_text,
        session_id=str(session_uuid),
    )


@app.get("/api/analysis/history", response_model=List[schemas.AnalysisHistoryItem], tags=["AI Analysis"])
def get_analysis_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve historical analysis reports run for the current user."""
    results = (
        db.query(models.AnalysisResult)
        .filter(models.AnalysisResult.user_id == current_user.id)
        .order_by(models.AnalysisResult.created_at.desc())
        .limit(20)
        .all()
    )
    return [schemas.AnalysisHistoryItem.model_validate(r) for r in results]
