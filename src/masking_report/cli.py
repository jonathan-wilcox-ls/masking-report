"""Command-line interface for masking-report."""

import sys
from typing import Optional

import click

from . import __version__
from .client import (
    APIError,
    AuthenticationError,
    MaskingClient,
    MaskingClientError,
)
from .report import (
    ReportBuilder,
    format_as_csv,
    format_as_json,
    format_as_table,
)


@click.command()
@click.option(
    "-e",
    "--engine",
    envvar="MASKING_ENGINE",
    required=True,
    help="Masking engine base URL (e.g., https://engine.example.com)",
)
@click.option(
    "-v",
    "--api-version",
    envvar="MASKING_API_VERSION",
    default=MaskingClient.DEFAULT_API_VERSION,
    show_default=True,
    help="API version",
)
@click.option(
    "-x",
    "--execution-id",
    required=True,
    type=int,
    help="Execution ID to analyze",
)
@click.option(
    "-u",
    "--username",
    envvar="MASKING_USERNAME",
    required=True,
    help="Username for authentication",
)
@click.option(
    "-p",
    "--password",
    envvar="MASKING_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Password for authentication (prompted if not provided)",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["table", "csv", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--severity",
    multiple=True,
    help="Filter by severity (repeatable, e.g., --severity WARNING --severity ERROR)",
)
@click.option(
    "--event-type",
    multiple=True,
    help="Filter by event type (repeatable)",
)
@click.option(
    "-s",
    "--summary",
    is_flag=True,
    help="Show summary grouped by component instead of detailed events",
)
@click.option(
    "-k",
    "--insecure",
    is_flag=True,
    help="Skip TLS certificate verification",
)
@click.version_option(version=__version__)
def main(
    engine: str,
    api_version: str,
    execution_id: int,
    username: str,
    password: str,
    output_format: str,
    output: Optional[str],
    severity: tuple[str, ...],
    event_type: tuple[str, ...],
    summary: bool,
    insecure: bool,
) -> None:
    """Generate reports for Delphix Masking Engine job executions.

    This tool fetches execution components and events from the Masking Engine API,
    joins them together, and produces a report showing the component name alongside
    event details like masked object, algorithm, severity, and cause.

    \b
    Examples:
        # Basic usage with table output
        masking-report -e https://engine.example.com -x 123 -u admin

        # Export to CSV with filters
        masking-report -e https://engine.example.com -x 123 -u admin \\
            -f csv --severity WARNING -o report.csv

        # Summary view
        masking-report -e https://engine.example.com -x 123 -u admin --summary
    """
    # Convert filter tuples to lists (or None if empty)
    severity_filter = list(severity) if severity else None
    event_type_filter = list(event_type) if event_type else None

    try:
        with MaskingClient(
            engine_url=engine,
            username=username,
            password=password,
            api_version=api_version,
            verify_ssl=not insecure,
        ) as client:
            # Fetch data from API
            click.echo("Fetching execution components...", err=True)
            components = client.get_execution_components(execution_id)
            click.echo(f"  Found {len(components)} components", err=True)

            click.echo("Fetching execution events...", err=True)
            events = client.get_execution_events(execution_id)
            click.echo(f"  Found {len(events)} events", err=True)

            # Build report
            builder = ReportBuilder(components, events)

            if summary:
                rows = builder.build_summary_report(severity_filter, event_type_filter)
            else:
                rows = builder.build_detailed_report(severity_filter, event_type_filter)

            # Format output
            if output_format == "table":
                result = format_as_table(rows, summary=summary)
            elif output_format == "csv":
                result = format_as_csv(rows)
            else:
                result = format_as_json(rows)

            # Write output
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(result)
                click.echo(f"Report written to {output}", err=True)
            else:
                click.echo(result)

    except AuthenticationError as e:
        click.echo(f"Authentication failed: {e}", err=True)
        sys.exit(1)
    except APIError as e:
        click.echo(f"API error: {e}", err=True)
        sys.exit(1)
    except MaskingClientError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
