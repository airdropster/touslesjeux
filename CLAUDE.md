# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Board game data enrichment pipeline. Takes a `games.json` source file containing board games with OCR-extracted rule text, cleans/translates the text via OpenAI API (GPT-4o-mini), enriches metadata (theme, mechanics, complexity, player count, etc.), and outputs structured JSON files.

## Language & Runtime

- Python 3 (no virtual environment or dependency manager configured yet)
- Single dependency: `openai` (`pip install openai`)

## Running

```bash
python enrichir_batch.py
```

Requires `games.json` in the working directory. Outputs:
- `enrichi/<id>.json` — one file per game (enables resume on restart)
- `batch_XXX.json` — combined batch files of 10 games each

## Architecture

Single-script pipeline (`enrichir_batch.py`) with this flow:

1. **Pre-clean** (`pre_clean`) — local regex cleanup of OCR artifacts before API calls (saves tokens)
2. **Process** (`process_game`) — two paths based on text length:
   - Small text (< 12k chars): single API call with full schema (metadata + cleaned rules)
   - Large text (>= 12k chars): chunk-by-chunk cleaning, then separate metadata extraction
3. **Fallback** — if API fails, saves raw data with empty enrichment fields
4. **Batch assembly** (`generate_batches`) — merges individual JSON files into batch files

## Key Configuration (top of script)

| Constant | Purpose |
|---|---|
| `GAMES_FILE` | Source file path (`games.json`) |
| `OUTPUT_DIR` | Individual results directory (`enrichi/`) |
| `BATCH_SIZE` | Games per batch file (10) |
| `BIG_THRESHOLD` | Char limit before chunked processing (12000) |
| `CHUNK_SIZE` | Characters per cleaning chunk (10000) |

## Data Schema

Each enriched game JSON includes: `id`, `title`, `year`, `designer`, player counts, duration, `complexity_score_1_to_10`, `summary`, `regles_detaillees` (cleaned full rules text), `theme[]`, `mechanics[]`, `components[]`, `core_mechanics[]`, `public[]`, `niveau_interaction`, `famille_materiel[]`, `tags[]`, `editeur`, `type_jeu_famille[]`, `lien_bgg`.

## Known Issues

- API key is hardcoded — must be moved to environment variable (`OPENAI_API_KEY`)
- No `requirements.txt` or `pyproject.toml`
- No tests
- Not a git repository yet
