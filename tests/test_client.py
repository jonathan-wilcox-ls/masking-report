"""Tests for the Masking Engine API client."""

import pytest
from pytest_httpx import HTTPXMock

from masking_report.client import (
    APIError,
    AuthenticationError,
    MaskingClient,
    MaskingClientError,
)


@pytest.fixture
def client():
    """Create a test client."""
    return MaskingClient(
        engine_url="https://engine.example.com",
        username="admin",
        password="secret",
        api_version="5.1.47",
    )


class TestAuthentication:
    """Tests for login functionality."""

    def test_login_success(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test successful login stores auth token."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token-12345"},
            status_code=201,
        )

        client.login()

        assert client._auth_token == "test-token-12345"

    def test_login_invalid_credentials(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test login with invalid credentials raises AuthenticationError."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            status_code=401,
        )

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            client.login()

    def test_login_server_error(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test login with server error raises APIError."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            status_code=500,
            text="Internal Server Error",
        )

        with pytest.raises(APIError, match="Login failed with status 500"):
            client.login()

    def test_login_missing_token_in_response(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test login with missing token raises AuthenticationError."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={},
            status_code=201,
        )

        with pytest.raises(AuthenticationError, match="No authorization token"):
            client.login()


class TestGetExecutionComponents:
    """Tests for fetching execution components."""

    def test_get_components_single_page(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test fetching components that fit in a single page."""
        # Login response
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        # Components response
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=123&page_number=1",
            json={
                "_pageInfo": {"numberOnPage": 2, "total": 2},
                "responseList": [
                    {
                        "executionComponentId": 1,
                        "componentName": "CUSTOMERS",
                        "executionId": 123,
                        "status": "SUCCEEDED",
                    },
                    {
                        "executionComponentId": 2,
                        "componentName": "ORDERS",
                        "executionId": 123,
                        "status": "SUCCEEDED",
                    },
                ],
            },
        )

        components = client.get_execution_components(123)

        assert len(components) == 2
        assert components[0].component_name == "CUSTOMERS"
        assert components[1].component_name == "ORDERS"

    def test_get_components_multiple_pages(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test fetching components across multiple pages."""
        # Login response
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        # Page 1
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=123&page_number=1",
            json={
                "_pageInfo": {"numberOnPage": 2, "total": 3},
                "responseList": [
                    {"executionComponentId": 1, "componentName": "TABLE_A", "executionId": 123, "status": "SUCCEEDED"},
                    {"executionComponentId": 2, "componentName": "TABLE_B", "executionId": 123, "status": "SUCCEEDED"},
                ],
            },
        )
        # Page 2
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=123&page_number=2",
            json={
                "_pageInfo": {"numberOnPage": 1, "total": 3},
                "responseList": [
                    {"executionComponentId": 3, "componentName": "TABLE_C", "executionId": 123, "status": "SUCCEEDED"},
                ],
            },
        )

        components = client.get_execution_components(123)

        assert len(components) == 3
        assert [c.component_name for c in components] == ["TABLE_A", "TABLE_B", "TABLE_C"]

    def test_get_components_empty(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test fetching components when none exist."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=123&page_number=1",
            json={
                "_pageInfo": {"numberOnPage": 0, "total": 0},
                "responseList": [],
            },
        )

        components = client.get_execution_components(123)

        assert len(components) == 0


class TestGetExecutionEvents:
    """Tests for fetching execution events."""

    def test_get_events_single_page(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test fetching events that fit in a single page."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-events?execution_id=123&page_number=1",
            json={
                "_pageInfo": {"numberOnPage": 1, "total": 1},
                "responseList": [
                    {
                        "executionEventId": 1,
                        "executionId": 123,
                        "eventType": "UNMASKED_DATA",
                        "severity": "WARNING",
                        "cause": "PATTERN_MATCH_FAILURE",
                        "count": 5,
                        "timeStamp": "2024-01-15T10:30:00.000+0000",
                        "executionComponentId": 1,
                        "maskedObjectName": "SSN",
                        "algorithmName": "SSNMask",
                    },
                ],
            },
        )

        events = client.get_execution_events(123)

        assert len(events) == 1
        assert events[0].event_type == "UNMASKED_DATA"
        assert events[0].severity == "WARNING"
        assert events[0].count == 5

    def test_get_events_multiple_pages(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test fetching events across multiple pages."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        # Page 1
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-events?execution_id=123&page_number=1",
            json={
                "_pageInfo": {"numberOnPage": 1, "total": 2},
                "responseList": [
                    {
                        "executionEventId": 1,
                        "executionId": 123,
                        "eventType": "UNMASKED_DATA",
                        "severity": "WARNING",
                        "cause": "CAUSE_A",
                        "count": 1,
                        "timeStamp": None,
                        "executionComponentId": 1,
                        "maskedObjectName": "FIELD_A",
                        "algorithmName": "Algo1",
                    },
                ],
            },
        )
        # Page 2
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-events?execution_id=123&page_number=2",
            json={
                "_pageInfo": {"numberOnPage": 1, "total": 2},
                "responseList": [
                    {
                        "executionEventId": 2,
                        "executionId": 123,
                        "eventType": "UNMASKED_DATA",
                        "severity": "ERROR",
                        "cause": "CAUSE_B",
                        "count": 2,
                        "timeStamp": None,
                        "executionComponentId": 2,
                        "maskedObjectName": "FIELD_B",
                        "algorithmName": "Algo2",
                    },
                ],
            },
        )

        events = client.get_execution_events(123)

        assert len(events) == 2
        assert events[0].severity == "WARNING"
        assert events[1].severity == "ERROR"


class TestErrorHandling:
    """Tests for error handling."""

    def test_not_found_error(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test 404 response raises APIError."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=999&page_number=1",
            status_code=404,
        )

        with pytest.raises(APIError, match="Resource not found"):
            client.get_execution_components(999)

    def test_session_expired(self, client: MaskingClient, httpx_mock: HTTPXMock):
        """Test expired session raises AuthenticationError."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://engine.example.com/masking/api/v5.1.47/execution-components?execution_id=123&page_number=1",
            status_code=401,
        )

        with pytest.raises(AuthenticationError, match="Session expired"):
            client.get_execution_components(123)


class TestClientConfiguration:
    """Tests for client configuration."""

    def test_custom_api_version(self, httpx_mock: HTTPXMock):
        """Test client uses custom API version in URLs."""
        client = MaskingClient(
            engine_url="https://engine.example.com",
            username="admin",
            password="secret",
            api_version="5.2.0",
        )

        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.2.0/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )

        client.login()

        assert client._auth_token == "test-token"

    def test_default_api_version(self):
        """Test client uses default API version when not specified."""
        client = MaskingClient(
            engine_url="https://engine.example.com",
            username="admin",
            password="secret",
        )

        assert client.api_version == "5.1.47"

    def test_engine_url_trailing_slash_removed(self):
        """Test trailing slash is removed from engine URL."""
        client = MaskingClient(
            engine_url="https://engine.example.com/",
            username="admin",
            password="secret",
        )

        assert client.engine_url == "https://engine.example.com"

    def test_base_url_construction(self):
        """Test base URL is constructed correctly."""
        client = MaskingClient(
            engine_url="https://engine.example.com",
            username="admin",
            password="secret",
            api_version="5.1.50",
        )

        assert client.base_url == "https://engine.example.com/masking/api/v5.1.50"


class TestContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_closes_client(self, httpx_mock: HTTPXMock):
        """Test context manager closes HTTP client on exit."""
        httpx_mock.add_response(
            method="POST",
            url="https://engine.example.com/masking/api/v5.1.47/login",
            json={"Authorization": "test-token"},
            status_code=201,
        )

        with MaskingClient(
            engine_url="https://engine.example.com",
            username="admin",
            password="secret",
        ) as client:
            client.login()
            assert client._client is not None

        assert client._client is None
