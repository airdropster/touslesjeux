# Listicle Game Title Extraction — Design Spec

## Problem

When Exa returns listicle pages (e.g., "Top 30 des meilleurs jeux de stratégie"), the scraper creates one ScrapedGame with the article title. The enricher then fails because the title isn't a game name. Collection #2 had 21/22 failures for this reason.

## Solution

After reading a page with Jina Reader, send the Markdown to OpenAI (gpt-4o-mini) to extract individual board game titles. Each extracted title becomes its own ScrapedGame entry.

## Changes

### New function: `extract_titles_from_page(raw_text: str) -> list[str]`

- Location: `backend/app/services/scraper.py`
- Takes Jina Markdown text, sends first ~3000 characters to gpt-4o-mini
- System prompt: "Extract all board game titles mentioned in this text. Return a JSON array of strings. Only include actual board game names, not article titles or categories. If no board games are found, return an empty array []."
- Returns list of clean game title strings
- Uses `AsyncOpenAI` with `settings.openai_api_key` (already configured)
- On failure (API error, invalid JSON, empty result): returns empty list

### Modified: `discover_games(categories) -> list[ScrapedGame]`

Current flow per search result:
1. Read page with Jina → raw_text
2. Clean search result title → 1 ScrapedGame

New flow per search result:
1. Read page with Jina → raw_text
2. Extract titles from raw_text via OpenAI → list of game titles
3. If extraction returns titles: create 1 ScrapedGame per title (shared raw_text, shared source_url)
4. If extraction returns empty: fall back to clean_title on search result title (current behavior)
5. Dedup by normalized title (lowercase strip) in addition to URL dedup

### No changes to:

- `ScrapedGame` dataclass (unchanged)
- `collector.py` (unchanged — still receives list[ScrapedGame])
- `enricher.py` (unchanged)
- `config.py` (uses existing openai_api_key)
- Public interface of `discover_games` (unchanged)

## Cost

- gpt-4o-mini: ~3000 input tokens + ~50 output tokens per page ≈ $0.001/page
- 40-page collection ≈ $0.04 total extraction cost
- Enrichment cost (existing) unchanged

## Error Handling

- OpenAI API failure → fall back to clean_title (current behavior)
- Invalid JSON response → fall back to clean_title
- Empty extraction → fall back to clean_title
- No collection should break because of this feature

## Testing

- `test_extract_titles_from_page_success`: mock OpenAI, verify list of titles returned
- `test_extract_titles_from_page_empty`: mock OpenAI returning [], verify empty list
- `test_extract_titles_from_page_api_error`: mock OpenAI raising exception, verify empty list returned
- `test_discover_games_with_extraction`: integration test verifying multiple ScrapedGame entries per page
- Update existing `test_discover_games_integration` to account for extraction step
