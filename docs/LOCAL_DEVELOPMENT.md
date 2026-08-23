# Local Development

## Prerequisites

- Git
- Python 3.12+
- Docker Desktop
- VS Code

## Clone

```bash
git clone git@github.com:nikhil-247/airindex-india.git
cd airindex-india
code .
```

HTTPS alternative:

```bash
git clone https://github.com/nikhil-247/airindex-india.git
cd airindex-india
code .
```

## Python environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Environment

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

No external API key is required for the core health/test path.

## Infrastructure

Start local PostgreSQL and Redis:

```bash
docker compose up -d
```

## Validation

```bash
pytest
ruff check .
```

The project should remain runnable when optional AI provider keys are absent.

## Git workflow

Create a feature branch:

```bash
git checkout -b feature/<short-name>
```

Before pushing:

```bash
pytest
ruff check .
git status
git add .
git commit -m "feat: <description>"
git push -u origin feature/<short-name>
```

The repository uses pull requests for major changes.
