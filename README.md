# masking-report

A command-line tool for generating reports from Delphix Masking Engine job executions.

## Problem

When using the Masking Engine API to extract execution events, the response does not include the table or file name for each event—only an `executionComponentId`. This tool cross-references execution events with execution components to produce a unified report showing component names alongside event details.

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd masking-job-analysis

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install
pip install -e .
```

### Pre-built Executables

Download the latest release for your platform from the [Releases](../../releases) page:

| Platform | File |
|----------|------|
| Linux | `masking-report-linux-amd64` |
| Windows | `masking-report-windows-amd64.exe` |
| macOS | `masking-report-macos-amd64` |

## Usage

### Basic Usage

```bash
# Interactive password prompt
masking-report -e https://engine.example.com -x 123 -u admin

# With environment variables
export MASKING_ENGINE=https://engine.example.com
export MASKING_USERNAME=admin
export MASKING_PASSWORD=secret
masking-report -x 123
```

### Output Formats

```bash
# Table output (default) - formatted for terminal
masking-report -e https://engine.example.com -x 123 -u admin

# CSV output
masking-report -e https://engine.example.com -x 123 -u admin -f csv

# JSON output
masking-report -e https://engine.example.com -x 123 -u admin -f json

# Write to file
masking-report -e https://engine.example.com -x 123 -u admin -f csv -o report.csv
```

### Filtering

```bash
# Filter by severity
masking-report -e https://engine.example.com -x 123 -u admin --severity WARNING

# Filter by multiple severities
masking-report -e https://engine.example.com -x 123 -u admin \
    --severity WARNING --severity ERROR

# Filter by event type
masking-report -e https://engine.example.com -x 123 -u admin \
    --event-type UNMASKED_DATA
```

### Summary Mode

```bash
# Show aggregated summary by component
masking-report -e https://engine.example.com -x 123 -u admin --summary
```

### API Version

```bash
# Specify a different API version (default: 5.1.47)
masking-report -e https://engine.example.com -v 5.1.50 -x 123 -u admin
```

### TLS Options

```bash
# Skip certificate verification (not recommended for production)
masking-report -e https://engine.example.com -x 123 -u admin --insecure
```

## Options Reference

| Option | Short | Environment Variable | Description |
|--------|-------|---------------------|-------------|
| `--engine` | `-e` | `MASKING_ENGINE` | Masking engine base URL |
| `--api-version` | `-v` | `MASKING_API_VERSION` | API version (default: 5.1.47) |
| `--execution-id` | `-x` | | Execution ID to analyze |
| `--username` | `-u` | `MASKING_USERNAME` | Username for authentication |
| `--password` | `-p` | `MASKING_PASSWORD` | Password (prompted if not provided) |
| `--format` | `-f` | | Output format: table, csv, json |
| `--output` | `-o` | | Output file path |
| `--severity` | | | Filter by severity (repeatable) |
| `--event-type` | | | Filter by event type (repeatable) |
| `--summary` | `-s` | | Show summary grouped by component |
| `--insecure` | `-k` | | Skip TLS certificate verification |

## Output Examples

### Detailed Mode (Default)

```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Component   ┃ Masked Object  ┃ Algorithm   ┃ Event Type    ┃ Severity ┃ Cause                 ┃ Count ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ CUSTOMERS   │ FIRST_NAME     │ NameAlgo    │ UNMASKED_DATA │ WARNING  │ PATTERN_MATCH_FAILURE │    15 │
│ CUSTOMERS   │ SSN            │ SSNAlgo     │ UNMASKED_DATA │ WARNING  │ NULL_VALUE            │     3 │
│ ORDERS      │ CREDIT_CARD    │ CCAlgo      │ UNMASKED_DATA │ ERROR    │ INVALID_FORMAT        │     1 │
└─────────────┴────────────────┴─────────────┴───────────────┴──────────┴───────────────────────┴───────┘
```

### Summary Mode

```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component   ┃ Status    ┃ Total Events ┃ Warnings ┃ Errors ┃ Top Cause             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ CUSTOMERS   │ SUCCEEDED │           18 │       18 │      0 │ PATTERN_MATCH_FAILURE │
│ ORDERS      │ FAILED    │            5 │        2 │      3 │ INVALID_FORMAT        │
└─────────────┴───────────┴──────────────┴──────────┴────────┴───────────────────────┘
```

## Development

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Building Executables Locally

```bash
# Build for current platform
pyinstaller masking-report.spec

# Output in dist/masking-report (or dist/masking-report.exe on Windows)
```

## Releasing

To create a new release with pre-built executables for all platforms:

```bash
# Tag a new version
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build executables for Linux, Windows, and macOS
2. Create a GitHub Release with all binaries attached

## License

MIT
