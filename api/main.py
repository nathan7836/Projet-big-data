"""
FastAPI REST API - US Health Insurance Datamarts
==================================================
Exposes the 3 datamarts (Affordability, Market Structure, Competitiveness)
with JWT authentication and pagination.

Endpoints:
  POST /auth/login                    - Get JWT token
  GET  /datamarts/affordability       - DM1: paginated
  GET  /datamarts/market-structure    - DM2: paginated
  GET  /datamarts/competitiveness     - DM3: paginated
  GET  /datamarts/affordability/stats - Aggregated stats
  GET  /health                        - Health check
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Any

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ── Config ───────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://api:apipass@postgres-gold:5432/datamarts"
)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key-for-bigdata-project")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60

# ── DB ───────────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth ─────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Demo users (in real app would be in a DB)
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
    },
    "analyst": {
        "username": "analyst",
        "hashed_password": pwd_context.hash("analyst123"),
        "role": "analyst",
    },
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise cred_exception
        user = USERS_DB.get(username)
        if not user:
            raise cred_exception
        return user
    except JWTError:
        raise cred_exception


# ── Schemas ──────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: List[Any]


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str


# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="US Health Insurance Datamarts API",
    description="REST API exposing 3 datamarts: Affordability, Market Structure, Competitiveness",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return HealthResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.utcnow().isoformat(),
    )


# ── Auth endpoint ────────────────────────────────────────────────────
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_MINUTES * 60,
    )


# ── Helper: paginated query ──────────────────────────────────────────
def paginated_query(
    db: Session,
    table: str,
    filters: dict,
    page: int,
    page_size: int,
    order_by: str = "snapshot_date DESC",
) -> PaginatedResponse:
    where_parts = []
    params = {}
    for key, value in filters.items():
        if value is not None:
            where_parts.append(f'"{key}" = :{key}')
            params[key] = value

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    # Total count
    count_sql = f"SELECT COUNT(*) AS c FROM {table} {where_sql}"
    total = db.execute(text(count_sql), params).scalar() or 0

    # Paginated rows
    offset = (page - 1) * page_size
    data_sql = f"SELECT * FROM {table} {where_sql} ORDER BY {order_by} LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = offset

    rows = db.execute(text(data_sql), params).mappings().all()
    items = [dict(r) for r in rows]

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=items,
    )


# ── Datamart 1: Affordability ────────────────────────────────────────
@app.get("/datamarts/affordability", response_model=PaginatedResponse, tags=["datamarts"])
def get_affordability(
    state: Optional[str] = Query(None, description="Filter by US state code (e.g. CA)"),
    metal_level: Optional[str] = Query(None, description="Bronze, Silver, Gold, Platinum, Catastrophic"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated DM1: Affordability indicators (avg deductible, OOP max) by state and metal level."""
    return paginated_query(
        db,
        table="datamart_affordability",
        filters={"StateCode": state, "MetalLevel": metal_level},
        page=page,
        page_size=page_size,
    )


@app.get("/datamarts/affordability/stats", tags=["datamarts"])
def affordability_stats(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregated stats across all states/metal levels for DM1."""
    sql = """
        SELECT
            "MetalLevel" AS metallevel,
            COUNT(*) AS num_state_groups,
            ROUND(AVG(avg_individual_deductible)::numeric, 2) AS overall_avg_deductible,
            ROUND(AVG(avg_individual_oop_max)::numeric, 2) AS overall_avg_oop_max,
            ROUND(MIN(avg_individual_deductible)::numeric, 2) AS lowest_avg_deductible,
            ROUND(MAX(avg_individual_deductible)::numeric, 2) AS highest_avg_deductible
        FROM datamart_affordability
        GROUP BY "MetalLevel"
        ORDER BY overall_avg_deductible
    """
    rows = db.execute(text(sql)).mappings().all()
    return {"items": [dict(r) for r in rows]}


# ── Datamart 2: Market Structure ─────────────────────────────────────
@app.get("/datamarts/market-structure", response_model=PaginatedResponse, tags=["datamarts"])
def get_market_structure(
    state: Optional[str] = Query(None),
    network_type: Optional[str] = Query(None, description="HMO, PPO, EPO, POS"),
    issuer: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated DM2: Market structure (network types, issuers, diversity)."""
    return paginated_query(
        db,
        table="datamart_market_structure",
        filters={
            "StateCode": state,
            "NetworkType": network_type,
            "IssuerName": issuer,
        },
        page=page,
        page_size=page_size,
        order_by="num_plans DESC",
    )


@app.get("/datamarts/market-structure/by-network", tags=["datamarts"])
def market_structure_by_network(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """National network type distribution."""
    sql = """
        SELECT
            "NetworkType" AS networktype,
            SUM(num_plans) AS total_plans,
            COUNT(DISTINCT "IssuerName") AS unique_issuers,
            COUNT(DISTINCT "StateCode") AS state_coverage,
            ROUND(AVG(avg_deductible)::numeric, 2) AS avg_deductible
        FROM datamart_market_structure
        GROUP BY "NetworkType"
        ORDER BY total_plans DESC
    """
    rows = db.execute(text(sql)).mappings().all()
    return {"items": [dict(r) for r in rows]}


# ── Datamart 3: Competitiveness ──────────────────────────────────────
@app.get("/datamarts/competitiveness", response_model=PaginatedResponse, tags=["datamarts"])
def get_competitiveness(
    state: Optional[str] = Query(None),
    metal_level: Optional[str] = Query(None),
    network_type: Optional[str] = Query(None),
    benefit_category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated DM3: Competitiveness (copays, exclusions, limits)."""
    return paginated_query(
        db,
        table="datamart_competitiveness",
        filters={
            "StateCode": state,
            "MetalLevel": metal_level,
            "NetworkType": network_type,
            "BenefitCategory": benefit_category,
        },
        page=page,
        page_size=page_size,
        order_by="avg_copay_primary ASC",
    )


@app.get("/datamarts/competitiveness/copay-summary", tags=["datamarts"])
def copay_summary(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Average copays per metal level."""
    sql = """
        SELECT
            "MetalLevel" AS metallevel,
            ROUND(AVG(avg_copay_primary)::numeric, 2) AS avg_copay_primary,
            ROUND(AVG(avg_copay_specialist)::numeric, 2) AS avg_copay_specialist,
            ROUND(AVG(avg_copay_er)::numeric, 2) AS avg_copay_er,
            ROUND(AVG(avg_copay_generic)::numeric, 2) AS avg_copay_generic,
            ROUND(AVG(avg_coinsurance_rate)::numeric, 4) AS avg_coinsurance_rate,
            SUM(num_excluded) AS total_exclusions,
            SUM(num_hsa_eligible) AS total_hsa_eligible
        FROM datamart_competitiveness
        GROUP BY "MetalLevel"
        ORDER BY avg_copay_primary
    """
    rows = db.execute(text(sql)).mappings().all()
    return {"items": [dict(r) for r in rows]}
