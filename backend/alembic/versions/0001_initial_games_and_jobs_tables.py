"""initial: games and jobs tables

Revision ID: 0001
Revises:
Create Date: 2026-03-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- jobs table ---
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "target_count >= 10 AND target_count <= 200",
            name="ck_target_count_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- games table ---
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("designer", sa.String(200), nullable=True),
        sa.Column("editeur", sa.String(200), nullable=True),
        sa.Column("player_count_min", sa.Integer(), nullable=True),
        sa.Column("player_count_max", sa.Integer(), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("duration_max", sa.Integer(), nullable=True),
        sa.Column("age_minimum", sa.Integer(), nullable=True),
        sa.Column("complexity_score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("regles_detaillees", sa.Text(), nullable=True),
        sa.Column("theme", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mechanics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("core_mechanics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("type_jeu_famille", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("public", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("niveau_interaction", sa.String(10), nullable=True),
        sa.Column("famille_materiel", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("lien_bgg", sa.String(500), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("skip_reason", sa.String(100), nullable=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("scraped_at", sa.DateTime(), nullable=True),
        sa.Column("enriched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "complexity_score IS NULL OR (complexity_score >= 1 AND complexity_score <= 10)",
            name="ck_complexity_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # GIN indexes for JSONB columns
    op.create_index("ix_games_theme", "games", ["theme"], postgresql_using="gin")
    op.create_index("ix_games_mechanics", "games", ["mechanics"], postgresql_using="gin")
    op.create_index("ix_games_tags", "games", ["tags"], postgresql_using="gin")
    op.create_index("ix_games_type_jeu_famille", "games", ["type_jeu_famille"], postgresql_using="gin")

    # Unique functional index: lower(title), coalesce(year, 0)
    op.create_index(
        "uq_games_title_year",
        "games",
        [sa.text("lower(title)"), sa.text("coalesce(year, 0)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_games_title_year", table_name="games")
    op.drop_index("ix_games_type_jeu_famille", table_name="games")
    op.drop_index("ix_games_tags", table_name="games")
    op.drop_index("ix_games_mechanics", table_name="games")
    op.drop_index("ix_games_theme", table_name="games")
    op.drop_table("games")
    op.drop_table("jobs")
