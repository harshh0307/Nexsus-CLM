import uuid
from datetime import datetime, timezone

_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel


class Contract(SQLModel, table=True):
    __tablename__ = "contracts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: str = Field(index=True, default="default")
    file_name: str
    storage_path: str = Field(default="")
    status: str = Field(default="pending", index=True)
    extracted_metadata: dict = Field(default_factory=dict, sa_type=JSON)
    raw_text: str = Field(default="")
    version: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=_utcnow
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"onupdate": _utcnow},
    )

    clauses: list["ContractClause"] = Relationship(back_populates="contract")


class ContractClause(SQLModel, table=True):
    __tablename__ = "contract_clauses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    contract_id: uuid.UUID = Field(foreign_key="contracts.id", index=True)
    tenant_id: str = Field(index=True, default="default")
    clause_type: str = Field(index=True)
    text_content: str
    embedding: Any = Field(default=None, sa_type=Vector(1536), nullable=True)

    contract: Contract = Relationship(back_populates="clauses")


class CorporateGuideline(SQLModel, table=True):
    __tablename__ = "corporate_guidelines"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: str = Field(index=True, default="default")
    guideline_type: str = Field(index=True)
    standard_text: str
    risk_level: str = Field(default="medium")
    embedding: Any = Field(default=None, sa_type=Vector(1536), nullable=True)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: str = Field(index=True, default="default")
    contract_id: Optional[uuid.UUID] = None
    action: str
    performed_by: str = Field(default="system")
    details: dict = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(
        default_factory=_utcnow
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=_utcnow
    )


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token_hash: str
    expires_at: datetime
    used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utcnow
    )
