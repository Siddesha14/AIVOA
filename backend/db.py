"""SQLAlchemy engine and models for RCA investigations."""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is missing from the project .env file.")

engine = create_engine(database_url, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(30), nullable=False, default="open")
    summary = Column(JSONB, nullable=False)
    risk = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    causes = relationship(
        "CauseRecord",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    whys = relationship(
        "WhyRecord",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    evidence_items = relationship(
        "EvidenceRecord",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    capas = relationship(
        "CapaRecord",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    audit_entries = relationship(
        "AuditLog",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )


class CauseRecord(Base):
    __tablename__ = "causes"

    id = Column(Integer, primary_key=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cause_id = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String(30), nullable=False)
    is_probable_root = Column(Boolean, nullable=False, default=False)
    confidence = Column(String(10), nullable=False, default="low")
    source_quote = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="suggested")

    investigation = relationship("Investigation", back_populates="causes")


class WhyRecord(Base):
    __tablename__ = "whys"

    id = Column(Integer, primary_key=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    evidence_needed = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="whys")


class EvidenceRecord(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    why_needed = Column(Text, nullable=True)
    related_cause_id = Column(String(100), nullable=True)

    investigation = relationship("Investigation", back_populates="evidence_items")


class CapaRecord(Base):
    __tablename__ = "capas"

    id = Column(Integer, primary_key=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capa_id = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    effectiveness_check = Column(Text, nullable=False)
    linked_cause_id = Column(String(100), nullable=True)

    investigation = relationship("Investigation", back_populates="capas")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    ts = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    investigation = relationship("Investigation", back_populates="audit_entries")


def create_tables() -> None:
    """Create missing database tables."""
    Base.metadata.create_all(bind=engine)