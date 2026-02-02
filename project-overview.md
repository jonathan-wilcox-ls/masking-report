# Command-line utility to create report for a masking job

## Problem

Using the API client to extract execution events does not provide the table name (or file name) for each event. You need to cross-reference with execution components. This utility uses the Masking API to produce a report (CSV, JSON, or table) for troubleshooting and refining masking jobs.

## Process

For a given executionID:
1. Authenticate with the masking engine
2. Collect all execution components (with pagination)
3. Collect all execution events (with pagination)
4. Join events with components by `executionComponentId`
5. Apply optional filters (severity, eventType)
6. Generate report in requested format (detail or summary)

---

## CLI Design

### Installation

```bash
pip install -e .
```

### Usage

```bash
# Basic usage - detailed table output (uses default API version 5.1.47)
masking-report -e https://engine.example.com -x 123 -u admin

# Specify a different API version
masking-report -e https://engine.example.com -v 5.1.50 -x 123 -u admin

# JSON output to file
masking-report -e https://engine.example.com -x 123 -u admin -f json -o report.json

# CSV with filters
masking-report -e https://engine.example.com -x 123 -u admin -f csv \
    --severity WARNING --event-type UNMASKED_DATA

# Summary mode
masking-report -e https://engine.example.com -x 123 -u admin --summary
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--engine` | `-e` | Masking engine base URL | `$MASKING_ENGINE` |
| `--api-version` | `-v` | API version (e.g., `5.1.47`) | `$MASKING_API_VERSION` or `5.1.47` |
| `--execution-id` | `-x` | Execution ID to analyze | (required) |
| `--username` | `-u` | Username for authentication | `$MASKING_USERNAME` |
| `--password` | `-p` | Password (prompted if not provided) | `$MASKING_PASSWORD` |
| `--format` | `-f` | Output format: `table`, `csv`, `json` | `table` |
| `--output` | `-o` | Output file path | stdout |
| `--severity` | | Filter by severity (repeatable) | all |
| `--event-type` | | Filter by event type (repeatable) | all |
| `--summary` | `-s` | Show summary grouped by component | `false` |
| `--insecure` | `-k` | Skip TLS certificate verification | `false` |

### Environment Variables

- `MASKING_ENGINE` - Default engine URL
- `MASKING_API_VERSION` - API version (affects endpoint path: `/masking/api/v{version}/...`)
- `MASKING_USERNAME` - Default username
- `MASKING_PASSWORD` - Password (avoids command-line exposure)

---

## Output Formats

### Detailed Mode (default)

Shows one row per execution event with full context:

| componentName | maskedObjectName | algorithmName | eventType | severity | cause | count |
|---------------|------------------|---------------|-----------|----------|-------|-------|
| CUSTOMERS | FIRST_NAME | NameAlgo | UNMASKED_DATA | WARNING | PATTERN_MATCH_FAILURE | 15 |
| CUSTOMERS | SSN | SSNAlgo | UNMASKED_DATA | WARNING | NULL_VALUE | 3 |

### Summary Mode (`--summary`)

Aggregates by component showing totals:

| componentName | status | totalEvents | warnings | errors | topCause |
|---------------|--------|-------------|----------|--------|----------|
| CUSTOMERS | SUCCEEDED | 18 | 18 | 0 | PATTERN_MATCH_FAILURE |
| ORDERS | FAILED | 5 | 2 | 3 | MASKED_FIELD_ERROR |

---

## Project Structure

```
masking-job-analysis/
├── pyproject.toml
├── README.md
├── masking-report.spec      # PyInstaller build specification
├── .github/
│   └── workflows/
│       └── release.yml      # Multi-platform build & release workflow
├── src/
│   └── masking_report/
│       ├── __init__.py
│       ├── cli.py           # CLI entry point (click)
│       ├── client.py        # MaskingClient - auth, pagination, API calls
│       ├── models.py        # Dataclasses: ExecutionComponent, ExecutionEvent
│       └── report.py        # ReportBuilder - joins, filters, formatting
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_report.py
    └── fixtures/            # Sample API responses
```

---

## API Reference

### Base URL Structure

All API endpoints use the base path: `/masking/api/v{version}/`

Where `{version}` is the API version (e.g., `5.1.47`). The version affects the endpoint paths for all calls except login.

### Authentication

**Endpoint:** `POST /masking/api/v{version}/login`

```json
// Request
{"username": "admin", "password": "secret"}

// Response (201)
{"Authorization": "415aac5d-xxxx-xxxx-xxxx-af6cf70dc49e"}
```

The `Authorization` token is included in the header for all subsequent requests:
```
Authorization: 415aac5d-xxxx-xxxx-xxxx-af6cf70dc49e
```

### Execution Components

**Endpoint:** `GET /masking/api/v{version}/execution-components`

**Query Parameters:**
- `execution_id` (required) - The execution to get components for
- `page_number` - Page number (default: 1)
- `page_size` - Results per page (default: server setting)
- `status` - Filter by status: `SUCCEEDED`, `WARNING`, `FAILED`, `CANCELLED`, `RUNNING`, `WAITING`

```json
{
  "_pageInfo": {
    "numberOnPage": 10,
    "total": 25
  },
  "responseList": [
    {
      "executionComponentId": 20,
      "componentName": "CUSTOMERS",
      "executionId": 10,
      "status": "SUCCEEDED"
    }
  ]
}
```

### Execution Events

**Endpoint:** `GET /masking/api/v{version}/execution-events`

**Query Parameters:**
- `execution_id` (required) - The execution to get events for
- `page_number` - Page number (default: 1)
- `page_size` - Results per page (default: server setting)

```json
{
  "_pageInfo": {
    "numberOnPage": 10,
    "total": 50
  },
  "responseList": [
    {
      "executionEventId": 1,
      "executionId": 1,
      "eventType": "UNMASKED_DATA",
      "severity": "WARNING",
      "cause": "PATTERN_MATCH_FAILURE",
      "count": 1,
      "timeStamp": "2018-11-06T04:14:46.929+0000",
      "executionComponentId": 1,
      "maskedObjectName": "DB_FIELD_NAME",
      "algorithmName": "MyAlgorithm"
    }
  ]
}
```

---

## Implementation Notes

### Pagination Strategy

Both endpoints return paginated results. Use `page_number` query param, incrementing until `numberOnPage` is 0 or we've fetched `total` items.

```python
def fetch_all_pages(endpoint, params):
    results = []
    page = 1
    while True:
        response = self.get(endpoint, {**params, "page_number": page})
        results.extend(response["responseList"])
        if len(results) >= response["_pageInfo"]["total"]:
            break
        page += 1
    return results
```

### Error Handling

- **401 Unauthorized**: Invalid credentials or expired session
- **404 Not Found**: Invalid execution ID
- **Connection errors**: Network/TLS issues

### Dependencies

**Runtime:**
- `click` - CLI framework
- `httpx` - HTTP client (async-capable, modern)
- `rich` - Table formatting for terminal output

**Development:**
- `pytest` - Testing framework
- `pyinstaller` - Executable packaging

---

## Building Executables

### Local Build

Build an executable for your current platform:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Build executable
pyinstaller masking-report.spec

# Output: dist/masking-report (or dist/masking-report.exe on Windows)
```

### PyInstaller Specification

The `masking-report.spec` file configures the build:

```python
# masking-report.spec
a = Analysis(
    ['src/masking_report/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['click', 'httpx', 'rich'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='masking-report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

---

## CI/CD: GitHub Actions

### Release Workflow

The workflow builds executables for all platforms when a version tag is pushed:

```yaml
# .github/workflows/release.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            artifact_name: masking-report
            asset_name: masking-report-linux-amd64
          - os: windows-latest
            artifact_name: masking-report.exe
            asset_name: masking-report-windows-amd64.exe
          - os: macos-latest
            artifact_name: masking-report
            asset_name: masking-report-macos-amd64

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Build executable
        run: pyinstaller masking-report.spec

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.asset_name }}
          path: dist/${{ matrix.artifact_name }}

  release:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: artifacts/**/*
          generate_release_notes: true
```

### Creating a Release

```bash
# Tag a new version
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will automatically:
# 1. Build executables for Linux, Windows, and macOS
# 2. Create a GitHub Release with all binaries attached
```

### Release Assets

Each release will include:

| File | Platform |
|------|----------|
| `masking-report-linux-amd64` | Linux x64 |
| `masking-report-windows-amd64.exe` | Windows x64 |
| `masking-report-macos-amd64` | macOS x64 (Intel) |

Users download the appropriate binary and run it directly—no Python installation required.