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
