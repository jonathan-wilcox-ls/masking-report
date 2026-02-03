"""Tests for report generation."""

import json

from masking_report.models import ExecutionComponent, ExecutionEvent
from masking_report.report import (
    ReportBuilder,
    format_as_csv,
    format_as_json,
)


def make_component(id: int, name: str, status: str = "SUCCEEDED") -> ExecutionComponent:
    """Helper to create test components."""
    return ExecutionComponent(
        execution_component_id=id,
        component_name=name,
        execution_id=1,
        status=status,
    )


def make_event(
    id: int,
    component_id: int,
    severity: str = "WARNING",
    event_type: str = "UNMASKED_DATA",
    cause: str = "PATTERN_MATCH_FAILURE",
) -> ExecutionEvent:
    """Helper to create test events."""
    return ExecutionEvent(
        execution_event_id=id,
        execution_id=1,
        event_type=event_type,
        severity=severity,
        cause=cause,
        count=1,
        timestamp=None,
        execution_component_id=component_id,
        masked_object_name=f"FIELD_{id}",
        algorithm_name="TestAlgo",
    )


def test_detailed_report_joins_component_names():
    """Test that detailed report includes component names from components."""
    components = [
        make_component(1, "CUSTOMERS"),
        make_component(2, "ORDERS"),
    ]
    events = [
        make_event(1, component_id=1),
        make_event(2, component_id=2),
    ]

    builder = ReportBuilder(components, events)
    rows = builder.build_detailed_report()

    assert len(rows) == 2
    assert rows[0].component_name == "CUSTOMERS"
    assert rows[1].component_name == "ORDERS"


def test_detailed_report_filter_by_severity():
    """Test filtering events by severity."""
    components = [make_component(1, "CUSTOMERS")]
    events = [
        make_event(1, component_id=1, severity="WARNING"),
        make_event(2, component_id=1, severity="ERROR"),
        make_event(3, component_id=1, severity="WARNING"),
    ]

    builder = ReportBuilder(components, events)
    rows = builder.build_detailed_report(severity=["ERROR"])

    assert len(rows) == 1
    assert rows[0].severity == "ERROR"


def test_detailed_report_filter_by_event_type():
    """Test filtering events by event type."""
    components = [make_component(1, "CUSTOMERS")]
    events = [
        make_event(1, component_id=1, event_type="UNMASKED_DATA"),
        make_event(2, component_id=1, event_type="OTHER_EVENT"),
    ]

    builder = ReportBuilder(components, events)
    rows = builder.build_detailed_report(event_type=["UNMASKED_DATA"])

    assert len(rows) == 1
    assert rows[0].event_type == "UNMASKED_DATA"


def test_summary_report_aggregates_by_component():
    """Test that summary report aggregates events by component."""
    components = [
        make_component(1, "CUSTOMERS", "SUCCEEDED"),
        make_component(2, "ORDERS", "FAILED"),
    ]
    events = [
        make_event(1, component_id=1, severity="WARNING"),
        make_event(2, component_id=1, severity="WARNING"),
        make_event(3, component_id=2, severity="ERROR"),
    ]

    builder = ReportBuilder(components, events)
    rows = builder.build_summary_report()

    # Should be sorted by component name
    assert len(rows) == 2
    assert rows[0].component_name == "CUSTOMERS"
    assert rows[0].total_events == 2
    assert rows[0].warnings == 2
    assert rows[0].errors == 0

    assert rows[1].component_name == "ORDERS"
    assert rows[1].total_events == 1
    assert rows[1].warnings == 0
    assert rows[1].errors == 1


def test_summary_report_includes_components_with_no_events():
    """Test that components with no events still appear in summary."""
    components = [
        make_component(1, "CUSTOMERS"),
        make_component(2, "EMPTY_TABLE"),
    ]
    events = [
        make_event(1, component_id=1),
    ]

    builder = ReportBuilder(components, events)
    rows = builder.build_summary_report()

    assert len(rows) == 2
    empty_row = next(r for r in rows if r.component_name == "EMPTY_TABLE")
    assert empty_row.total_events == 0


def test_format_as_csv():
    """Test CSV output format."""
    components = [make_component(1, "CUSTOMERS")]
    events = [make_event(1, component_id=1)]

    builder = ReportBuilder(components, events)
    rows = builder.build_detailed_report()
    csv_output = format_as_csv(rows)

    assert "componentName" in csv_output
    assert "CUSTOMERS" in csv_output
    assert "FIELD_1" in csv_output


def test_format_as_json():
    """Test JSON output format."""
    components = [make_component(1, "CUSTOMERS")]
    events = [make_event(1, component_id=1)]

    builder = ReportBuilder(components, events)
    rows = builder.build_detailed_report()
    json_output = format_as_json(rows)

    data = json.loads(json_output)
    assert len(data) == 1
    assert data[0]["componentName"] == "CUSTOMERS"


class TestReportBuilderEdgeCases:
    """Edge case tests for ReportBuilder."""

    def test_event_with_unknown_component(self):
        """Test event referencing non-existent component shows 'Unknown'."""
        components = [make_component(1, "CUSTOMERS")]
        events = [make_event(1, component_id=999)]  # Non-existent component

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report()

        assert len(rows) == 1
        assert rows[0].component_name == "Unknown"

    def test_event_without_component_id(self):
        """Test event without component ID (e.g., JOB_ABORTED) shows 'N/A'."""
        components = [make_component(1, "CUSTOMERS")]
        # Create an event without component_id
        event = ExecutionEvent(
            execution_event_id=99,
            execution_id=1,
            event_type="JOB_ABORTED",
            severity="CRITICAL",
            cause="UNHANDLED_EXCEPTION",
            count=1,
            timestamp=None,
            execution_component_id=None,
            masked_object_name=None,
            algorithm_name=None,
        )

        builder = ReportBuilder(components, [event])
        rows = builder.build_detailed_report()

        assert len(rows) == 1
        assert rows[0].component_name == "N/A"
        assert rows[0].masked_object_name == "N/A"
        assert rows[0].algorithm_name == "N/A"
        assert rows[0].event_type == "JOB_ABORTED"
        assert rows[0].severity == "CRITICAL"

    def test_empty_events_list(self):
        """Test report with no events."""
        components = [make_component(1, "CUSTOMERS")]
        events = []

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report()

        assert len(rows) == 0

    def test_empty_components_list(self):
        """Test report with no components."""
        components = []
        events = [make_event(1, component_id=1)]

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report()

        assert len(rows) == 1
        assert rows[0].component_name == "Unknown"

    def test_both_empty(self):
        """Test report with no components and no events."""
        builder = ReportBuilder([], [])
        detailed = builder.build_detailed_report()
        summary = builder.build_summary_report()

        assert len(detailed) == 0
        assert len(summary) == 0

    def test_filter_case_insensitive(self):
        """Test that filters are case-insensitive."""
        components = [make_component(1, "CUSTOMERS")]
        events = [
            make_event(1, component_id=1, severity="WARNING"),
            make_event(2, component_id=1, severity="warning"),  # lowercase
        ]

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report(severity=["warning"])

        assert len(rows) == 2  # Both should match

    def test_multiple_filters_combined(self):
        """Test combining severity and event_type filters."""
        components = [make_component(1, "CUSTOMERS")]
        events = [
            make_event(1, component_id=1, severity="WARNING", event_type="TYPE_A"),
            make_event(2, component_id=1, severity="WARNING", event_type="TYPE_B"),
            make_event(3, component_id=1, severity="ERROR", event_type="TYPE_A"),
        ]

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report(severity=["WARNING"], event_type=["TYPE_A"])

        assert len(rows) == 1
        assert rows[0].severity == "WARNING"
        assert rows[0].event_type == "TYPE_A"

    def test_summary_top_cause_with_ties(self):
        """Test summary top_cause when multiple causes have same count."""
        components = [make_component(1, "CUSTOMERS")]
        events = [
            make_event(1, component_id=1, cause="CAUSE_A"),
            make_event(2, component_id=1, cause="CAUSE_B"),
        ]

        builder = ReportBuilder(components, events)
        rows = builder.build_summary_report()

        # Should pick one of them (implementation returns first most common)
        assert rows[0].top_cause in ["CAUSE_A", "CAUSE_B"]

    def test_summary_top_cause_empty_when_no_events(self):
        """Test summary top_cause is empty when component has no events."""
        components = [make_component(1, "CUSTOMERS")]
        events = []

        builder = ReportBuilder(components, events)
        rows = builder.build_summary_report()

        assert len(rows) == 1
        assert rows[0].top_cause == ""

    def test_summary_counts_severities_correctly(self):
        """Test that summary correctly counts different severities."""
        components = [make_component(1, "TABLE")]
        events = [
            make_event(1, component_id=1, severity="WARNING"),
            make_event(2, component_id=1, severity="WARNING"),
            make_event(3, component_id=1, severity="ERROR"),
            make_event(4, component_id=1, severity="INFO"),  # Neither warning nor error
        ]

        builder = ReportBuilder(components, events)
        rows = builder.build_summary_report()

        assert rows[0].total_events == 4
        assert rows[0].warnings == 2
        assert rows[0].errors == 1


class TestOutputFormatEdgeCases:
    """Edge case tests for output formatting."""

    def test_csv_empty_rows(self):
        """Test CSV output with empty rows."""
        csv_output = format_as_csv([])
        assert csv_output == ""

    def test_json_empty_rows(self):
        """Test JSON output with empty rows."""
        json_output = format_as_json([])
        data = json.loads(json_output)
        assert data == []

    def test_csv_special_characters(self):
        """Test CSV handles special characters in data."""
        components = [make_component(1, 'TABLE,WITH"SPECIAL')]
        events = [make_event(1, component_id=1)]

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report()
        csv_output = format_as_csv(rows)

        # CSV should properly escape the special characters
        assert "TABLE" in csv_output

    def test_json_special_characters(self):
        """Test JSON handles special characters in data."""
        components = [make_component(1, 'TABLE"WITH\\SPECIAL')]
        events = [make_event(1, component_id=1)]

        builder = ReportBuilder(components, events)
        rows = builder.build_detailed_report()
        json_output = format_as_json(rows)

        # Should be valid JSON
        data = json.loads(json_output)
        assert 'TABLE"WITH\\SPECIAL' in data[0]["componentName"]
