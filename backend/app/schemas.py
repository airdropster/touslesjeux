# backend/app/schemas.py
import logging
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

CURRENT_YEAR = datetime.now().year


# --- Collection / Job schemas ---

class CollectionLaunchRequest(BaseModel):
    categories: list[str] = Field(..., min_length=1)
    target_count: int = Field(100, ge=10, le=200)


class JobOut(BaseModel):
    id: int
    categories: list[str]
    target_count: int
    processed_count: int
    skipped_count: int
    failed_count: int
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Game schemas ---

class GameEnrichment(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    year: int | None = Field(None, ge=1900, le=CURRENT_YEAR + 2)
    designer: str | None = Field(None, max_length=200)
    editeur: str | None = Field(None, max_length=200)
    player_count_min: int | None = Field(None, ge=1, le=100)
    player_count_max: int | None = Field(None, ge=1, le=100)
    duration_min: int | None = Field(None, ge=1, le=1440)
    duration_max: int | None = Field(None, ge=1, le=1440)
    age_minimum: int | None = Field(None, ge=1, le=21)
    complexity_score: int | None = Field(None, ge=1, le=10)
    summary: str = Field(..., min_length=10, max_length=1000)
    regles_detaillees: str = Field(..., min_length=50)
    theme: list[str] = Field(default_factory=list)
    mechanics: list[str] = Field(default_factory=list)
    core_mechanics: list[str] = Field(default_factory=list, max_length=3)
    components: list[str] = Field(default_factory=list)
    type_jeu_famille: list[str] = Field(default_factory=list)
    public: list[str] = Field(default_factory=list)
    niveau_interaction: str | None = Field(None, pattern=r"^(nulle|faible|moyenne|forte)$")
    famille_materiel: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    lien_bgg: str | None = Field(None, max_length=500)

    @field_validator("regles_detaillees")
    @classmethod
    def check_word_count(cls, v: str) -> str:
        word_count = len(v.split())
        if word_count > 1800:
            raise ValueError(f"regles_detaillees depasse 1800 mots ({word_count})")
        return v

    @field_validator("public", mode="before")
    @classmethod
    def validate_public(cls, v: list[str]) -> list[str]:
        allowed = {"enfants", "famille", "joueurs_occasionnels", "joueurs_reguliers", "joueurs_experts"}
        invalid = [x for x in v if x not in allowed]
        if invalid:
            logger.warning("Valeurs public ignorees: %s", invalid)
        return [x for x in v if x in allowed]


class GameOut(BaseModel):
    id: int
    title: str
    year: int | None = None
    designer: str | None = None
    editeur: str | None = None
    player_count_min: int | None = None
    player_count_max: int | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    age_minimum: int | None = None
    complexity_score: int | None = None
    summary: str | None = None
    regles_detaillees: str | None = None
    theme: list[str] = []
    mechanics: list[str] = []
    core_mechanics: list[str] = []
    components: list[str] = []
    type_jeu_famille: list[str] = []
    public: list[str] = []
    niveau_interaction: str | None = None
    famille_materiel: list[str] = []
    tags: list[str] = []
    lien_bgg: str | None = None
    source_url: str | None = None
    status: str
    skip_reason: str | None = None
    job_id: int | None = None
    scraped_at: datetime | None = None
    enriched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class GameCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    year: int | None = None
    designer: str | None = None
    editeur: str | None = None
    player_count_min: int | None = None
    player_count_max: int | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    age_minimum: int | None = None
    complexity_score: int | None = Field(None, ge=1, le=10)
    summary: str | None = None
    regles_detaillees: str | None = None
    theme: list[str] = []
    mechanics: list[str] = []
    core_mechanics: list[str] = []
    components: list[str] = []
    type_jeu_famille: list[str] = []
    public: list[str] = []
    niveau_interaction: str | None = None
    famille_materiel: list[str] = []
    tags: list[str] = []
    lien_bgg: str | None = None


class GameUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = None
    designer: str | None = None
    editeur: str | None = None
    player_count_min: int | None = None
    player_count_max: int | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    age_minimum: int | None = None
    complexity_score: int | None = Field(None, ge=1, le=10)
    summary: str | None = None
    regles_detaillees: str | None = None
    theme: list[str] | None = None
    mechanics: list[str] | None = None
    core_mechanics: list[str] | None = None
    components: list[str] | None = None
    type_jeu_famille: list[str] | None = None
    public: list[str] | None = None
    niveau_interaction: str | None = None
    famille_materiel: list[str] | None = None
    tags: list[str] | None = None
    lien_bgg: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def title_not_null(cls, v):
        """Prevent explicitly setting title to null (DB NOT NULL constraint)."""
        if v is None:
            raise ValueError("title cannot be set to null")
        return v


# --- Pagination ---

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int


# --- Error ---

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
