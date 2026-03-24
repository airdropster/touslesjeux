# backend/tests/test_schemas.py
import pytest

from app.schemas import CollectionLaunchRequest, GameEnrichment, GameOut, GameUpdate, PaginatedResponse


def test_collection_launch_valid():
    req = CollectionLaunchRequest(categories=["des", "familial"], target_count=100)
    assert req.categories == ["des", "familial"]


def test_collection_launch_invalid_count():
    with pytest.raises(Exception):
        CollectionLaunchRequest(categories=["des"], target_count=5)  # min 10


def test_collection_launch_invalid_count_high():
    with pytest.raises(Exception):
        CollectionLaunchRequest(categories=["des"], target_count=300)  # max 200


def test_game_enrichment_valid():
    data = {
        "title": "Catan",
        "year": 1995,
        "designer": "Klaus Teuber",
        "editeur": "Kosmos",
        "player_count_min": 3,
        "player_count_max": 4,
        "duration_min": 60,
        "duration_max": 90,
        "age_minimum": 10,
        "complexity_score": 5,
        "summary": "Jeu de colonisation et de commerce sur une ile.",
        "regles_detaillees": "Les joueurs colonisent une ile. " * 50,
        "theme": ["colonisation"],
        "mechanics": ["dice_rolling", "trading"],
        "core_mechanics": ["trading"],
        "components": ["plateau", "cartes"],
        "type_jeu_famille": ["strategie"],
        "public": ["famille", "joueurs_reguliers"],
        "niveau_interaction": "moyenne",
        "famille_materiel": ["plateau", "cartes", "des"],
        "tags": ["classique"],
        "lien_bgg": "https://boardgamegeek.com/boardgame/13/catan",
    }
    enrichment = GameEnrichment(**data)
    assert enrichment.title == "Catan"
    assert enrichment.complexity_score == 5


def test_game_enrichment_rules_too_long():
    data = {
        "title": "Test",
        "summary": "Un jeu de test.",
        "regles_detaillees": "mot " * 1801,
        "theme": [],
        "mechanics": [],
        "core_mechanics": [],
    }
    with pytest.raises(Exception, match="1800"):
        GameEnrichment(**data)


def test_game_enrichment_invalid_public_filtered():
    data = {
        "title": "Test",
        "summary": "Un jeu de test pour valider.",
        "regles_detaillees": "Les regles du jeu sont simples. " * 10,
        "theme": [],
        "mechanics": [],
        "core_mechanics": [],
        "public": ["famille", "adolescents"],  # adolescents is invalid
    }
    enrichment = GameEnrichment(**data)
    assert enrichment.public == ["famille"]
