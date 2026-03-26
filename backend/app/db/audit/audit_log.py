from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Text,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

# TYPE_CHECKING opcional si quieres relationships tipadas
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db.auth import User
    from app.db.social import Group


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        # --------
        # Checks básicos (evitan basura tipo strings vacíos)
        # --------
        CheckConstraint("action_type <> ''", name="ck_audit_logs_action_type_not_empty"),
        CheckConstraint("entity_schema <> ''", name="ck_audit_logs_entity_schema_not_empty"),
        CheckConstraint("entity_table <> ''", name="ck_audit_logs_entity_table_not_empty"),
        CheckConstraint("entity_id <> ''", name="ck_audit_logs_entity_id_not_empty"),

        # --------
        # Índices típicos (logs = mucho volumen, esto importa)
        # --------
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_action_type", "action_type"),

        # buscar por “qué entidad cambió”
        Index("ix_audit_logs_entity", "entity_schema", "entity_table", "entity_id"),

        # buscar por “en qué contexto pasó” (ranking, scoring publish, etc.)
        Index("ix_audit_logs_context", "context_schema", "context_table", "context_id"),

        # filtrar por grupo rápido
        Index("ix_audit_logs_group_id", "group_id"),

        {"schema": "audit"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --------------------
    # Actor (quién lo hizo)
    # --------------------
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    actor_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --------------------
    # Grupo
    # --------------------
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social.groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --------------------
    # Acción
    # --------------------
    action_type: Mapped[str] = mapped_column(Text, nullable=False)

    # --------------------
    # Entidad afectada (obligatorio)
    # --------------------
    entity_schema: Mapped[str] = mapped_column(Text, nullable=False)
    entity_table: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)

    # --------------------
    # Contexto (opcional)
    # --------------------
    context_schema: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_table: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --------------------
    # Datos
    # --------------------
    old_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata",JSONB, nullable=True)

    # --------------------
    # Relationships (opcional)
    # --------------------
    actor_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[actor_user_id],
        back_populates="audit_logs_as_actor",
    )

    group: Mapped[Optional["Group"]] = relationship(
        "Group",
        foreign_keys=[group_id],
        back_populates="audit_logs",
    )
