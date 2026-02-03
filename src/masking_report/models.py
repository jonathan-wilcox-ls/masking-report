"""Data models for masking execution components and events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ExecutionComponent:
    """Represents a component (table/file) in a masking job execution."""

    execution_component_id: int
    component_name: str
    execution_id: int
    status: str

    @classmethod
    def from_api(cls, data: dict) -> "ExecutionComponent":
        """Create an ExecutionComponent from API response data."""
        return cls(
            execution_component_id=data["executionComponentId"],
            component_name=data["componentName"],
            execution_id=data["executionId"],
            status=data["status"],
        )


@dataclass
class ExecutionEvent:
    """Represents an event (warning/error) from a masking job execution."""

    execution_event_id: int
    execution_id: int
    event_type: str
    severity: str
    cause: str
    count: int
    timestamp: Optional[datetime]
    execution_component_id: Optional[int]
    masked_object_name: Optional[str]
    algorithm_name: Optional[str]

    @classmethod
    def from_api(cls, data: dict) -> "ExecutionEvent":
        """Create an ExecutionEvent from API response data."""
        timestamp = None
        if data.get("timeStamp"):
            try:
                # Handle both +0000 and +00:00 timezone formats
                ts = data["timeStamp"]
                ts = ts.replace("+0000", "+00:00").replace("+00:00:00", "+00:00")
                timestamp = datetime.fromisoformat(ts)
            except ValueError:
                pass

        return cls(
            execution_event_id=data["executionEventId"],
            execution_id=data["executionId"],
            event_type=data["eventType"],
            severity=data["severity"],
            cause=data["cause"],
            count=data["count"],
            timestamp=timestamp,
            execution_component_id=data.get("executionComponentId"),
            masked_object_name=data.get("maskedObjectName"),
            algorithm_name=data.get("algorithmName"),
        )


@dataclass
class ReportRow:
    """A single row in the detailed report output."""

    component_name: str
    masked_object_name: str
    algorithm_name: str
    event_type: str
    severity: str
    cause: str
    count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/CSV output."""
        return {
            "componentName": self.component_name,
            "maskedObjectName": self.masked_object_name,
            "algorithmName": self.algorithm_name,
            "eventType": self.event_type,
            "severity": self.severity,
            "cause": self.cause,
            "count": self.count,
        }


@dataclass
class SummaryRow:
    """A single row in the summary report output."""

    component_name: str
    status: str
    total_events: int
    warnings: int
    errors: int
    top_cause: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/CSV output."""
        return {
            "componentName": self.component_name,
            "status": self.status,
            "totalEvents": self.total_events,
            "warnings": self.warnings,
            "errors": self.errors,
            "topCause": self.top_cause,
        }
