"""API client for the Delphix Masking Engine."""

from typing import Optional

import httpx

from .models import ExecutionComponent, ExecutionEvent


class MaskingClientError(Exception):
    """Base exception for MaskingClient errors."""

    pass


class AuthenticationError(MaskingClientError):
    """Raised when authentication fails."""

    pass


class APIError(MaskingClientError):
    """Raised when an API call fails."""

    pass


class MaskingClient:
    """Client for interacting with the Delphix Masking Engine API."""

    DEFAULT_API_VERSION = "5.1.47"

    def __init__(
        self,
        engine_url: str,
        username: str,
        password: str,
        api_version: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        """Initialize the masking client.

        Args:
            engine_url: Base URL of the masking engine (e.g., https://engine.example.com)
            username: Username for authentication
            password: Password for authentication
            api_version: API version (default: 5.1.47)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.engine_url = engine_url.rstrip("/")
        self.username = username
        self.password = password
        self.api_version = api_version or self.DEFAULT_API_VERSION
        self.verify_ssl = verify_ssl
        self._auth_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls including version."""
        return f"{self.engine_url}/masking/api/v{self.api_version}"

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                verify=self.verify_ssl,
                timeout=30.0,
            )
        return self._client

    def login(self) -> None:
        """Authenticate with the masking engine and store the auth token."""
        client = self._get_client()
        url = f"{self.base_url}/login"

        try:
            response = client.post(
                url,
                json={"username": self.username, "password": self.password},
            )
        except httpx.RequestError as e:
            raise MaskingClientError(f"Connection error: {e}") from e

        if response.status_code == 401:
            raise AuthenticationError("Invalid username or password")

        if response.status_code != 201:
            raise APIError(
                f"Login failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        self._auth_token = data.get("Authorization")

        if not self._auth_token:
            raise AuthenticationError("No authorization token in response")

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid auth token."""
        if self._auth_token is None:
            self.login()

    def _get_headers(self) -> dict:
        """Get headers for authenticated requests."""
        return {"Authorization": self._auth_token}

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make an authenticated GET request.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response as dictionary
        """
        self._ensure_authenticated()
        client = self._get_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = client.get(url, params=params, headers=self._get_headers())
        except httpx.RequestError as e:
            raise MaskingClientError(f"Request error: {e}") from e

        if response.status_code == 401:
            raise AuthenticationError("Session expired or invalid token")

        if response.status_code == 404:
            raise APIError(f"Resource not found: {endpoint}")

        if response.status_code != 200:
            raise APIError(
                f"Request failed with status {response.status_code}: {response.text}"
            )

        return response.json()

    def _fetch_all_pages(self, endpoint: str, params: dict) -> list[dict]:
        """Fetch all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint
            params: Base query parameters (page_number will be added)

        Returns:
            List of all items from responseList across all pages
        """
        results = []
        page = 1

        while True:
            response = self._get(endpoint, {**params, "page_number": page})
            page_info = response.get("_pageInfo", {})
            response_list = response.get("responseList", [])

            results.extend(response_list)

            total = page_info.get("total", 0)
            if len(results) >= total or not response_list:
                break

            page += 1

        return results

    def get_execution_components(
        self, execution_id: int
    ) -> list[ExecutionComponent]:
        """Get all execution components for an execution.

        Args:
            execution_id: The execution ID to get components for

        Returns:
            List of ExecutionComponent objects
        """
        data = self._fetch_all_pages(
            "execution-components",
            {"execution_id": execution_id},
        )
        return [ExecutionComponent.from_api(item) for item in data]

    def get_execution_events(self, execution_id: int) -> list[ExecutionEvent]:
        """Get all execution events for an execution.

        Args:
            execution_id: The execution ID to get events for

        Returns:
            List of ExecutionEvent objects
        """
        data = self._fetch_all_pages(
            "execution-events",
            {"execution_id": execution_id},
        )
        return [ExecutionEvent.from_api(item) for item in data]

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "MaskingClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
