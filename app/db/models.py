import uuid
from datetime import datetime, timezone
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
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
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
        default_factory=lambda: datetime.now(timezone.utc)
    )
