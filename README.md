<p align="center">
  <img src="./MR_ban.jfif" alt="Description of image" width="500" height="600">
</p>

# Marvel Rivals Ban Helper

Local personal MVP for recommending Marvel Rivals bans from an uploaded enemy-team screenshot.

## Current State

Implemented:

- strict name normalization and hidden-name detection;
- exact-only RivalsMeta profile matching;
- ban scoring from Competitive hero stats;
- OCR preprocessing/post-processing boundary;
- optional EasyOCR adapter;
- Playwright browser automation for RivalsMeta's visible search UI;
- Streamlit app shell;
- unit and integration-style tests.

Not yet verified locally:

- end-to-end recommendation output from a ranked screenshot with matched Competitive stats.

Verified:

- Python 3.12.7 works when invoked through the explicit executable path from Codex.
- `python -m pytest -q` passes.
- OCR extracts six names from `MR_snapshot_sample.jpg`.
- Browser lookup works against RivalsMeta for exact player names.

## Setup

Install Python 3.11 or newer, then from this folder run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev,ocr]
```

## Test

```powershell
python -m pytest -q
```

In this Codex app session, Python may need to be called by explicit path:

```powershell
& 'C:\Users\Milad\AppData\Local\Programs\Python\Python312\python.exe' -m pytest -q
```

## Run

```powershell
streamlit run app.py
```

## Design Choice

The app does not fuzzy-match player names. If OCR reads `gro0ty` and RivalsMeta returns `grooty`, the profile is skipped. That reduces coverage, but avoids confidently looking up the wrong player.
