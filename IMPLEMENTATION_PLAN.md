# Marvel Rivals Ban Helper MVP Plan

## Product Scope

Build a local, personal MVP that takes one uploaded Marvel Rivals enemy-team screenshot and returns two suggested hero bans.

The MVP intentionally avoids manual name editing. It favors correctness over coverage: hidden names, ambiguous OCR results, and non-exact RivalsMeta matches are skipped instead of guessed.

## Agreed Pipeline

1. Upload screenshot.
2. Crop/split the enemy-team name area.
3. Run local OCR per row.
4. Filter OCR output by confidence/agreement.
5. Skip hidden streamer-mode names such as `****2`.
6. Search RivalsMeta using the exact extracted name only.
7. Accept only exact normalized profile matches.
8. Fetch Competitive top-hero statistics.
9. Score heroes and return two ban candidates.

## Matching Rules

- Allowed normalization:
  - trim leading/trailing whitespace;
  - collapse repeated whitespace;
  - compare case-insensitively;
  - remove invisible/control characters.
- Disallowed normalization:
  - no fuzzy name search;
  - no `0` to `o` substitution;
  - no `rn` to `m` substitution;
  - no automatic close-match acceptance.

## Milestones And Tests

### Milestone 1: Project Scaffold And Core Models

Status: Complete

Deliverables:
- Python package structure.
- Streamlit app entrypoint placeholder.
- Test setup.
- Shared data models for players, hero stats, and recommendations.

Tests:
- Import/package smoke test.

### Milestone 2: Strict Name Handling

Status: Complete

Deliverables:
- Normalize player names safely.
- Detect hidden streamer-mode names.
- Validate exact RivalsMeta display-name matches.

Tests:
- Hidden patterns such as `****`, `****2`, `******17` are skipped.
- Case and whitespace differences are accepted.
- Lookalike character differences such as `gro0ty` vs `grooty` are rejected.

### Milestone 3: Ban Scoring

Status: Complete

Deliverables:
- Aggregate Competitive hero stats across matched players.
- Return top two ban recommendations.
- Ignore tiny/noisy samples below configurable thresholds.

Tests:
- High usage and strong win rate outrank tiny perfect samples.
- Same hero appearing across multiple enemies is boosted by aggregation.
- Empty input returns no recommendations.

### Milestone 4: RivalsMeta Client Abstraction

Status: Complete for offline contract; live search route needs browser/network inspection

Deliverables:
- Client interface for searching player names and fetching profile hero stats.
- Strict exact-match profile selection.
- Offline parser fixtures so tests do not depend on the live site.
- Request caching/rate-limit-friendly structure.

Tests:
- Exact match accepted.
- Ambiguous/no match skipped.
- Fixture profile parses Competitive hero rows correctly.

### Milestone 5: Local OCR Pipeline

Status: Complete for app shell; blocked on local OCR/runtime verification

Deliverables:
- OCR interface.
- Image preprocessing hook.
- Row-based extraction strategy.
- Local engine adapter, starting with optional PaddleOCR/EasyOCR integration.

Tests:
- OCR post-processing removes UI labels/icons/noise.
- Sample-like OCR lines produce exactly six candidate slots when available.
- Hidden names pass through as skipped names.

### Milestone 6: Streamlit MVP

Status: Partial

Deliverables:
- Local upload UI.
- One-trigger processing.
- Result display with recommendations, matched count, and skipped count.

Tests:
- Integration test with mocked OCR and RivalsMeta client.
- UI pipeline returns recommendations without manual input.

## Current Progress

- Created this implementation tracker.
- Added Python package scaffold, dependencies, and pytest setup.
- Implemented strict name normalization, hidden-name detection, and exact profile matching.
- Implemented ban scoring and aggregation.
- Added RivalsMeta client abstraction plus offline parser/matching tests.
- Added OCR interface, preprocessing, and post-processing tests.
- Added optional EasyOCR adapter.
- Added one-trigger Streamlit app shell.
- Added README with setup, test, and run instructions.
- Installed EasyOCR and verified sample OCR output:
  `goreix`, `nirvreckn`, `grooty`, `grungtown`, `ChoosMcGoose`, `Krazzo Xoro`.
- Added Playwright-backed RivalsMeta browser client that uses the visible search UI and exact profile-heading verification.
- Verified live browser lookup for `v3rteegoTTV`, including Competitive hero extraction:
  `The Punisher`, 4 games, 50% win rate.
- Ran full sample pipeline on `MR_snapshot_sample.jpg`.
  - Matched exact RivalsMeta profiles: `nirvreckn`, `grooty`, `grungtown`, `ChoosMcGoose`.
  - Skipped: `goreix`, `Krazzo Xoro`.
  - Recommendations: none, because matched sample profiles did not expose parseable Competitive top-hero stats.

## Known Remaining Work

- Test the end-to-end app with a ranked-game screenshot whose matched players have Competitive top-hero stats.
- Create the GitHub repository after the local MVP skeleton is verified.

## Verification Status

- Attempted `pytest -q`: blocked because `pytest` is not available on PATH.
- Attempted `python -m pytest -q`: blocked because `python` is not available on PATH.
- Attempted `py --version`: blocked because `py` is not available on PATH.
- Attempted to locate `uv`, `pip`, `pipx`, and `poetry`: none found on PATH.
- Retried with explicit Python path outside the sandbox:
  `C:\Users\Milad\AppData\Local\Programs\Python\Python312\python.exe`
- Verified Python version: 3.12.7.
- Installed dev dependencies.
- Ran test suite successfully after browser/OCR updates: `27 passed in 0.67s`.
