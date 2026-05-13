from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guest_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    motor_profile: Mapped["MotorSkillProfileORM"] = relationship(back_populates="user", uselist=False)
    cognitive_profile: Mapped["CognitiveSkillProfileORM"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["TypingSessionORM"]] = relationship(back_populates="user")
    vocab_words: Mapped[list["UserVocabORM"]] = relationship(back_populates="user")


class MotorSkillProfileORM(Base):
    __tablename__ = "motor_skill_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    overall_wpm: Mapped[float] = mapped_column(Float, nullable=False)
    overall_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    key_profiles: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    bigram_stats: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="motor_profile")


class CognitiveSkillProfileORM(Base):
    __tablename__ = "cognitive_skill_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    grammar_level: Mapped[int] = mapped_column(Integer, nullable=False)
    vocabulary_tier: Mapped[int] = mapped_column(Integer, nullable=False)
    weak_areas: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    strong_areas: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    cefr_level: Mapped[str] = mapped_column(String(2), nullable=False, server_default="A1")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="cognitive_profile")


class PassageORM(Base):
    __tablename__ = "passages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    grammar_tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sessions: Mapped[list["TypingSessionORM"]] = relationship(back_populates="passage")


class UserVocabORM(Base):
    __tablename__ = "user_vocab"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(2), nullable=False)
    pos: Mapped[str] = mapped_column(String(50), nullable=False, server_default="")
    practiced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="vocab_words")


class TypingSessionORM(Base):
    __tablename__ = "typing_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    passage_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("passages.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    keystrokes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["UserORM"] = relationship(back_populates="sessions")
    passage: Mapped["PassageORM"] = relationship(back_populates="sessions")
