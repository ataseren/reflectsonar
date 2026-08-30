# ReflectSonar repository guidance

## Architecture

- `src/reflectsonar/main.py` owns CLI parsing and orchestration.
- `src/reflectsonar/api/get_data.py` is the SonarQube HTTP boundary.
- `src/reflectsonar/data/models.py` contains normalized report data.
- `src/reflectsonar/report/` renders ReportLab flowables and the final PDF.
- Keep API parsing separate from PDF layout so each layer can be tested independently.

## Development setup

Use Python 3.8 or newer in a local virtual environment:

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
```

Never commit SonarQube tokens, generated reports, virtual environments, or source snippets from private projects.

## Required validation

Run these checks for code changes:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m black --check src tests scripts
.venv\Scripts\python.exe -m flake8 src tests scripts
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe -m build
```

For report-layout changes, generate the synthetic PDF used by the tests, render every page with Poppler, and inspect the PNGs for clipping, overflow, missing headers, and unreadable text.

## Change expectations

- Add a regression test for every bug fix.
- Test both Standard Experience and MQR responses when changing API behavior.
- Treat partial API results as failures unless the user explicitly opts into truncation.
- Encode query parameters rather than interpolating raw project, component, or rule keys.
- Preserve Python 3.8 compatibility unless a release explicitly changes the support policy.
- Keep `VERSION`, `pyproject.toml`, and `src/reflectsonar/__init__.py` synchronized for releases.
