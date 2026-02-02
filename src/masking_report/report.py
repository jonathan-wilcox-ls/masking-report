"""Report generation for masking execution analysis."""

import csv
import io
import json
from collections import Counter
from typing import Optional

from rich.console import Console
from rich.table import Table

from .models import (
    ExecutionComponent,
    ExecutionEvent,
    ReportRow,
    SummaryRow,
)


class ReportBuilder:
    """Builds reports from execution components and events."""

    def __init__(
        self,
        components: list[ExecutionComponent],
        events: list[ExecutionEvent],
    ):
        """Initialize the report builder.

        Args:
            components: List of execution components
            events: List of execution events
        """
        self.components = components
        self.events = events
        self._component_map: dict[int, ExecutionComponent] = {
            c.execution_component_id: c for c in components
        }

    def _get_component_name(self, component_id: int) -> str:
        """Get component name by ID, or 'Unknown' if not found."""
        component = self._component_map.get(component_id)
        return component.component_name if component else "Unknown"

    def _get_component_status(self, component_id: int) -> str:
        """Get component status by ID, or 'Unknown' if not found."""
        component = self._component_map.get(component_id)
        return component.status if component else "Unknown"

    def filter_events(
        self,
        severity: Optional[list[str]] = None,
        event_type: Optional[list[str]] = None,
    ) -> list[ExecutionEvent]:
        """Filter events by severity and/or event type.

        Args:
            severity: List of severities to include (e.g., ['WARNING', 'ERROR'])
            event_type: List of event types to include

        Returns:
            Filtered list of events
        """
        filtered = self.events

        if severity:
            severity_upper = [s.upper() for s in severity]
            filtered = [e for e in filtered if e.severity.upper() in severity_upper]

        if event_type:
            event_type_upper = [t.upper() for t in event_type]
            filtered = [e for e in filtered if e.event_type.upper() in event_type_upper]

        return filtered

    def build_detailed_report(
        self,
        severity: Optional[list[str]] = None,
        event_type: Optional[list[str]] = None,
    ) -> list[ReportRow]:
        """Build a detailed report with one row per event.

        Args:
            severity: Filter by severity
            event_type: Filter by event type

        Returns:
            List of ReportRow objects
        """
        filtered_events = self.filter_events(severity, event_type)

        rows = []
        for event in filtered_events:
            row = ReportRow(
                component_name=self._get_component_name(event.execution_component_id),
                masked_object_name=event.masked_object_name,
                algorithm_name=event.algorithm_name,
                event_type=event.event_type,
                severity=event.severity,
                cause=event.cause,
                count=event.count,
            )
            rows.append(row)

        return rows

    def build_summary_report(
        self,
        severity: Optional[list[str]] = None,
        event_type: Optional[list[str]] = None,
    ) -> list[SummaryRow]:
        """Build a summary report aggregated by component.

        Args:
            severity: Filter by severity
            event_type: Filter by event type

        Returns:
            List of SummaryRow objects
        """
        filtered_events = self.filter_events(severity, event_type)

        # Group events by component
        component_events: dict[int, list[ExecutionEvent]] = {}
        for event in filtered_events:
            cid = event.execution_component_id
            if cid not in component_events:
                component_events[cid] = []
            component_events[cid].append(event)

        # Include components with no events
        for component in self.components:
            if component.execution_component_id not in component_events:
                component_events[component.execution_component_id] = []

        rows = []
        for component_id, events in component_events.items():
            total = len(events)
            warnings = sum(1 for e in events if e.severity.upper() == "WARNING")
            errors = sum(1 for e in events if e.severity.upper() == "ERROR")

            # Find the most common cause
            causes = [e.cause for e in events if e.cause]
            top_cause = Counter(causes).most_common(1)
            top_cause_str = top_cause[0][0] if top_cause else ""

            row = SummaryRow(
                component_name=self._get_component_name(component_id),
                status=self._get_component_status(component_id),
                total_events=total,
                warnings=warnings,
                errors=errors,
                top_cause=top_cause_str,
            )
            rows.append(row)

        # Sort by component name
        rows.sort(key=lambda r: r.component_name)
        return rows


def format_as_table(rows: list[ReportRow] | list[SummaryRow], summary: bool = False) -> str:
    """Format report rows as a rich table.

    Args:
        rows: List of ReportRow or SummaryRow objects
        summary: Whether this is a summary report

    Returns:
        Formatted table string
    """
    console = Console(force_terminal=True, width=120)

    if summary:
        table = Table(title="Execution Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Total Events", justify="right")
        table.add_column("Warnings", justify="right", style="yellow")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Top Cause")

        for row in rows:
            status_style = "green" if row.status == "SUCCEEDED" else "red"
            table.add_row(
                row.component_name,
                f"[{status_style}]{row.status}[/{status_style}]",
                str(row.total_events),
                str(row.warnings),
                str(row.errors),
                row.top_cause,
            )
    else:
        table = Table(title="Execution Events Detail")
        table.add_column("Component", style="cyan")
        table.add_column("Masked Object")
        table.add_column("Algorithm")
        table.add_column("Event Type")
        table.add_column("Severity")
        table.add_column("Cause")
        table.add_column("Count", justify="right")

        for row in rows:
            severity_style = "yellow" if row.severity == "WARNING" else "red"
            table.add_row(
                row.component_name,
                row.masked_object_name,
                row.algorithm_name,
                row.event_type,
                f"[{severity_style}]{row.severity}[/{severity_style}]",
                row.cause,
                str(row.count),
            )

    with console.capture() as capture:
        console.print(table)

    return capture.get()


def format_as_csv(rows: list[ReportRow] | list[SummaryRow]) -> str:
    """Format report rows as CSV.

    Args:
        rows: List of ReportRow or SummaryRow objects

    Returns:
        CSV string
    """
    if not rows:
        return ""

    output = io.StringIO()
    dicts = [row.to_dict() for row in rows]

    writer = csv.DictWriter(output, fieldnames=dicts[0].keys())
    writer.writeheader()
    writer.writerows(dicts)

    return output.getvalue()


def format_as_json(rows: list[ReportRow] | list[SummaryRow]) -> str:
    """Format report rows as JSON.

    Args:
        rows: List of ReportRow or SummaryRow objects

    Returns:
        JSON string
    """
    dicts = [row.to_dict() for row in rows]
    return json.dumps(dicts, indent=2)
