"""Tests for data models."""

from masking_report.models import (
    ExecutionComponent,
    ExecutionEvent,
    ReportRow,
    SummaryRow,
)


def test_execution_component_from_api():
    """Test creating ExecutionComponent from API response."""
    data = {
        "executionComponentId": 20,
        "componentName": "CUSTOMERS",
        "executionId": 10,
        "status": "SUCCEEDED",
    }
    component = ExecutionComponent.from_api(data)

    assert component.execution_component_id == 20
    assert component.component_name == "CUSTOMERS"
    assert component.execution_id == 10
    assert component.status == "SUCCEEDED"


def test_execution_event_from_api():
    """Test creating ExecutionEvent from API response."""
    data = {
        "executionEventId": 1,
        "executionId": 1,
        "eventType": "UNMASKED_DATA",
        "severity": "WARNING",
        "cause": "PATTERN_MATCH_FAILURE",
        "count": 15,
        "timeStamp": "2018-11-06T04:14:46.929+0000",
        "executionComponentId": 20,
        "maskedObjectName": "FIRST_NAME",
        "algorithmName": "NameAlgo",
    }
    event = ExecutionEvent.from_api(data)

    assert event.execution_event_id == 1
    assert event.execution_id == 1
    assert event.event_type == "UNMASKED_DATA"
    assert event.severity == "WARNING"
    assert event.cause == "PATTERN_MATCH_FAILURE"
    assert event.count == 15
    assert event.execution_component_id == 20
    assert event.masked_object_name == "FIRST_NAME"
    assert event.algorithm_name == "NameAlgo"
    assert event.timestamp is not None


def test_report_row_to_dict():
    """Test ReportRow.to_dict() output format."""
    row = ReportRow(
        component_name="CUSTOMERS",
        masked_object_name="FIRST_NAME",
        algorithm_name="NameAlgo",
        event_type="UNMASKED_DATA",
        severity="WARNING",
        cause="PATTERN_MATCH_FAILURE",
        count=15,
    )
    d = row.to_dict()

    assert d["componentName"] == "CUSTOMERS"
    assert d["maskedObjectName"] == "FIRST_NAME"
    assert d["algorithmName"] == "NameAlgo"
    assert d["eventType"] == "UNMASKED_DATA"
    assert d["severity"] == "WARNING"
    assert d["cause"] == "PATTERN_MATCH_FAILURE"
    assert d["count"] == 15


def test_summary_row_to_dict():
    """Test SummaryRow.to_dict() output format."""
    row = SummaryRow(
        component_name="CUSTOMERS",
        status="SUCCEEDED",
        total_events=18,
        warnings=15,
        errors=3,
        top_cause="PATTERN_MATCH_FAILURE",
    )
    d = row.to_dict()

    assert d["componentName"] == "CUSTOMERS"
    assert d["status"] == "SUCCEEDED"
    assert d["totalEvents"] == 18
    assert d["warnings"] == 15
    assert d["errors"] == 3
    assert d["topCause"] == "PATTERN_MATCH_FAILURE"


class TestExecutionEventEdgeCases:
    """Edge case tests for ExecutionEvent."""

    def test_event_with_null_timestamp(self):
        """Test event with null timestamp."""
        data = {
            "executionEventId": 1,
            "executionId": 1,
            "eventType": "UNMASKED_DATA",
            "severity": "WARNING",
            "cause": "CAUSE",
            "count": 1,
            "timeStamp": None,
            "executionComponentId": 1,
            "maskedObjectName": "FIELD",
            "algorithmName": "Algo",
        }
        event = ExecutionEvent.from_api(data)
        assert event.timestamp is None

    def test_event_with_missing_timestamp(self):
        """Test event with missing timestamp key."""
        data = {
            "executionEventId": 1,
            "executionId": 1,
            "eventType": "UNMASKED_DATA",
            "severity": "WARNING",
            "cause": "CAUSE",
            "count": 1,
            "executionComponentId": 1,
            "maskedObjectName": "FIELD",
            "algorithmName": "Algo",
        }
        event = ExecutionEvent.from_api(data)
        assert event.timestamp is None

    def test_event_with_invalid_timestamp_format(self):
        """Test event with invalid timestamp format doesn't crash."""
        data = {
            "executionEventId": 1,
            "executionId": 1,
            "eventType": "UNMASKED_DATA",
            "severity": "WARNING",
            "cause": "CAUSE",
            "count": 1,
            "timeStamp": "invalid-date-format",
            "executionComponentId": 1,
            "maskedObjectName": "FIELD",
            "algorithmName": "Algo",
        }
        event = ExecutionEvent.from_api(data)
        assert event.timestamp is None

    def test_event_with_different_timezone_format(self):
        """Test event with different timezone format."""
        data = {
            "executionEventId": 1,
            "executionId": 1,
            "eventType": "UNMASKED_DATA",
            "severity": "WARNING",
            "cause": "CAUSE",
            "count": 1,
            "timeStamp": "2024-01-15T10:30:00.000+0000",
            "executionComponentId": 1,
            "maskedObjectName": "FIELD",
            "algorithmName": "Algo",
        }
        event = ExecutionEvent.from_api(data)
        assert event.timestamp is not None


class TestExecutionComponentEdgeCases:
    """Edge case tests for ExecutionComponent."""

    def test_component_with_various_statuses(self):
        """Test component with different status values."""
        statuses = ["SUCCEEDED", "WARNING", "FAILED", "CANCELLED", "RUNNING", "WAITING"]

        for status in statuses:
            data = {
                "executionComponentId": 1,
                "componentName": "TABLE",
                "executionId": 1,
                "status": status,
            }
            component = ExecutionComponent.from_api(data)
            assert component.status == status

    def test_component_with_special_characters_in_name(self):
        """Test component with special characters in name."""
        data = {
            "executionComponentId": 1,
            "componentName": "SCHEMA.TABLE_NAME$1",
            "executionId": 1,
            "status": "SUCCEEDED",
        }
        component = ExecutionComponent.from_api(data)
        assert component.component_name == "SCHEMA.TABLE_NAME$1"


class TestExecutionEventOptionalFields:
    """Tests for optional fields in ExecutionEvent."""

    def test_event_without_component_id(self):
        """Test event without executionComponentId (e.g., JOB_ABORTED)."""
        data = {
            "executionEventId": 45,
            "executionId": 289,
            "eventType": "JOB_ABORTED",
            "severity": "CRITICAL",
            "cause": "UNHANDLED_EXCEPTION",
            "count": 1,
            "timeStamp": "2026-02-03T19:25:40.167+00:00",
            "exceptionType": "org.apache.hop.core.exception.HopDatabase",
            "exceptionDetail": "Error details...",
        }
        event = ExecutionEvent.from_api(data)

        assert event.execution_event_id == 45
        assert event.event_type == "JOB_ABORTED"
        assert event.severity == "CRITICAL"
        assert event.execution_component_id is None
        assert event.masked_object_name is None
        assert event.algorithm_name is None

    def test_event_with_all_optional_fields(self):
        """Test event with all optional fields present."""
        data = {
            "executionEventId": 42,
            "executionId": 289,
            "eventType": "UNMASKED_DATA",
            "severity": "WARNING",
            "cause": "PATTERN_MATCH_FAILURE",
            "count": 20000,
            "timeStamp": "2026-02-03T19:25:37.252+00:00",
            "executionComponentId": 576,
            "maskedObjectName": "AGE",
            "algorithmName": "RepeatFirstDigit",
        }
        event = ExecutionEvent.from_api(data)

        assert event.execution_component_id == 576
        assert event.masked_object_name == "AGE"
        assert event.algorithm_name == "RepeatFirstDigit"
