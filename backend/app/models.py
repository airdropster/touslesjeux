from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class JsonbOrJson(TypeDecorator):
    """Uses JSONB on PostgreSQL, falls back to JSON on other databases (e.g. SQLite for tests)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    categories: Mapped[list] = mapped_column(JsonbOrJson, nullable=False)
    target_count: Mapped[int] = mapped_column(nullable=False)
    processed_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column()

    games: Mapped[list["Game"]] = relationship(back_populates="job")

    __table_args__ = (
        CheckConstraint("target_count >= 10 AND target_count <= 200", name="ck_target_count_range"),
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    year: Mapped[int | None] = mapped_column()
    designer: Mapped[str | None] = mapped_column(String(200))
    editeur: Mapped[str | None] = mapped_column(String(200))
    player_count_min: Mapped[int | None] = mapped_column()
    player_count_max: Mapped[int | None] = mapped_column()
    duration_min: Mapped[int | None] = mapped_column()
    duration_max: Mapped[int | None] = mapped_column()
    age_minimum: Mapped[int | None] = mapped_column()
    complexity_score: Mapped[int | None] = mapped_column()
    summary: Mapped[str | None] = mapped_column(Text)
    regles_detaillees: Mapped[str | None] = mapped_column(Text)
    theme: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    mechanics: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    core_mechanics: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    components: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    type_jeu_famille: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    public: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    niveau_interaction: Mapped[str | None] = mapped_column(String(10))
    famille_materiel: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    tags: Mapped[list | None] = mapped_column(JsonbOrJson, default=list)
    lien_bgg: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    skip_reason: Mapped[str | None] = mapped_column(String(100))
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"))
    scraped_at: Mapped[datetime | None] = mapped_column()
    enriched_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())

    job: Mapped[Job | None] = relationship(back_populates="games")

    __table_args__ = (
        CheckConstraint(
            "complexity_score IS NULL OR (complexity_score >= 1 AND complexity_score <= 10)",
            name="ck_complexity_range",
        ),
        Index("ix_games_theme", "theme", postgresql_using="gin"),
        Index("ix_games_mechanics", "mechanics", postgresql_using="gin"),
        Index("ix_games_tags", "tags", postgresql_using="gin"),
        Index("ix_games_type_jeu_famille", "type_jeu_famille", postgresql_using="gin"),
        Index(
            "uq_games_title_year",
            func.lower(title),
            func.coalesce(year, 0),
            unique=True,
        ),
    )
