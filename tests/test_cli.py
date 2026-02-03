"""Tests for the command-line interface."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from masking_report.cli import main
from masking_report.client import AuthenticationError, APIError, MaskingClientError
from masking_report.models import ExecutionComponent, ExecutionEvent


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def extract_json_from_output(output: str) -> str:
    """Extract JSON array from CLI output (skipping status messages)."""
    # Find the JSON array in the output
    start = output.find("[")
    end = output.rfind("]") + 1
    if start != -1 and end > start:
        return output[start:end]
    return "[]"


@pytest.fixture
def mock_components():
    """Sample execution components."""
    return [
        ExecutionComponent(
            execution_component_id=1,
            component_name="CUSTOMERS",
            execution_id=123,
            status="SUCCEEDED",
        ),
        ExecutionComponent(
            execution_component_id=2,
            component_name="ORDERS",
            execution_id=123,
            status="WARNING",
        ),
    ]


@pytest.fixture
def mock_events():
    """Sample execution events."""
    return [
        ExecutionEvent(
            execution_event_id=1,
            execution_id=123,
            event_type="UNMASKED_DATA",
            severity="WARNING",
            cause="PATTERN_MATCH_FAILURE",
            count=15,
            timestamp=None,
            execution_component_id=1,
            masked_object_name="FIRST_NAME",
            algorithm_name="NameAlgo",
        ),
        ExecutionEvent(
            execution_event_id=2,
            execution_id=123,
            event_type="UNMASKED_DATA",
            severity="ERROR",
            cause="NULL_VALUE",
            count=3,
            timestamp=None,
            execution_component_id=2,
            masked_object_name="ORDER_ID",
            algorithm_name="IDAlgo",
        ),
    ]


class TestCLIBasicUsage:
    """Tests for basic CLI functionality."""

    def test_help_option(self, runner: CliRunner):
        """Test --help shows usage information."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Generate reports for Delphix Masking Engine" in result.output
        assert "--engine" in result.output
        assert "--execution-id" in result.output

    def test_version_option(self, runner: CliRunner):
        """Test --version shows version."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_missing_required_options(self, runner: CliRunner):
        """Test error when required options are missing."""
        result = runner.invoke(main, [])

        assert result.exit_code != 0
        assert "Missing option" in result.output


class TestCLIWithMockedClient:
    """Tests for CLI with mocked API client."""

    @patch("masking_report.cli.MaskingClient")
    def test_successful_detailed_report(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test successful detailed report generation."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
            ],
        )

        assert result.exit_code == 0
        assert "CUSTOMERS" in result.output
        assert "FIRST_NAME" in result.output
        mock_client.get_execution_components.assert_called_once_with(123)
        mock_client.get_execution_events.assert_called_once_with(123)

    @patch("masking_report.cli.MaskingClient")
    def test_successful_summary_report(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test successful summary report generation."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "--summary",
            ],
        )

        assert result.exit_code == 0
        assert "CUSTOMERS" in result.output
        assert "ORDERS" in result.output

    @patch("masking_report.cli.MaskingClient")
    def test_json_output_format(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test JSON output format."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "-f", "json",
            ],
        )

        assert result.exit_code == 0
        # Parse the JSON output
        data = json.loads(extract_json_from_output(result.output))
        assert len(data) == 2
        assert data[0]["componentName"] == "CUSTOMERS"

    @patch("masking_report.cli.MaskingClient")
    def test_csv_output_format(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test CSV output format."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "-f", "csv",
            ],
        )

        assert result.exit_code == 0
        assert "componentName" in result.output
        assert "CUSTOMERS" in result.output

    @patch("masking_report.cli.MaskingClient")
    def test_output_to_file(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test output written to file."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                [
                    "-e", "https://engine.example.com",
                    "-x", "123",
                    "-u", "admin",
                    "-p", "secret",
                    "-f", "json",
                    "-o", "report.json",
                ],
            )

            assert result.exit_code == 0
            assert "Report written to report.json" in result.output

            with open("report.json") as f:
                data = json.load(f)
                assert len(data) == 2


class TestCLIFiltering:
    """Tests for CLI filtering options."""

    @patch("masking_report.cli.MaskingClient")
    def test_filter_by_severity(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test filtering by severity."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "-f", "json",
                "--severity", "WARNING",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(extract_json_from_output(result.output))
        assert len(data) == 1
        assert data[0]["severity"] == "WARNING"

    @patch("masking_report.cli.MaskingClient")
    def test_filter_by_multiple_severities(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test filtering by multiple severities."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "-f", "json",
                "--severity", "WARNING",
                "--severity", "ERROR",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(extract_json_from_output(result.output))
        assert len(data) == 2

    @patch("masking_report.cli.MaskingClient")
    def test_filter_by_event_type(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
    ):
        """Test filtering by event type."""
        events = [
            ExecutionEvent(
                execution_event_id=1,
                execution_id=123,
                event_type="UNMASKED_DATA",
                severity="WARNING",
                cause="CAUSE_A",
                count=1,
                timestamp=None,
                execution_component_id=1,
                masked_object_name="FIELD_A",
                algorithm_name="Algo",
            ),
            ExecutionEvent(
                execution_event_id=2,
                execution_id=123,
                event_type="OTHER_TYPE",
                severity="WARNING",
                cause="CAUSE_B",
                count=1,
                timestamp=None,
                execution_component_id=1,
                masked_object_name="FIELD_B",
                algorithm_name="Algo",
            ),
        ]

        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "-f", "json",
                "--event-type", "UNMASKED_DATA",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(extract_json_from_output(result.output))
        assert len(data) == 1
        assert data[0]["eventType"] == "UNMASKED_DATA"


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    @patch("masking_report.cli.MaskingClient")
    def test_authentication_error(self, mock_client_class: MagicMock, runner: CliRunner):
        """Test authentication error is handled gracefully."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_execution_components.side_effect = AuthenticationError(
            "Invalid credentials"
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "wrong",
            ],
        )

        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    @patch("masking_report.cli.MaskingClient")
    def test_api_error(self, mock_client_class: MagicMock, runner: CliRunner):
        """Test API error is handled gracefully."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_execution_components.side_effect = APIError(
            "Resource not found"
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "999",
                "-u", "admin",
                "-p", "secret",
            ],
        )

        assert result.exit_code == 1
        assert "API error" in result.output

    @patch("masking_report.cli.MaskingClient")
    def test_connection_error(self, mock_client_class: MagicMock, runner: CliRunner):
        """Test connection error is handled gracefully."""
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_execution_components.side_effect = MaskingClientError(
            "Connection refused"
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
            ],
        )

        assert result.exit_code == 1
        assert "Error" in result.output


class TestCLIEnvironmentVariables:
    """Tests for environment variable support."""

    @patch("masking_report.cli.MaskingClient")
    def test_engine_from_env(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test engine URL from environment variable."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            ["-x", "123", "-u", "admin", "-p", "secret"],
            env={"MASKING_ENGINE": "https://env-engine.example.com"},
        )

        assert result.exit_code == 0
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["engine_url"] == "https://env-engine.example.com"

    @patch("masking_report.cli.MaskingClient")
    def test_api_version_from_env(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test API version from environment variable."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
            ],
            env={"MASKING_API_VERSION": "5.2.0"},
        )

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["api_version"] == "5.2.0"


class TestCLIInsecureOption:
    """Tests for insecure TLS option."""

    @patch("masking_report.cli.MaskingClient")
    def test_insecure_flag(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        mock_components,
        mock_events,
    ):
        """Test --insecure flag disables SSL verification."""
        mock_client = MagicMock()
        mock_client.get_execution_components.return_value = mock_components
        mock_client.get_execution_events.return_value = mock_events
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main,
            [
                "-e", "https://engine.example.com",
                "-x", "123",
                "-u", "admin",
                "-p", "secret",
                "--insecure",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs["verify_ssl"] is False
