"""API Gateway Client implementation."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from api_gateway_client.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from api_gateway_client.models import HealthStatus, Token, User

logger = logging.getLogger(__name__)


class _BaseSubClient:
    """Base class for sub-clients."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: httpx Response object

        Returns:
            Response JSON data

        Raises:
            AuthenticationError: On 401
            AuthorizationError: On 403
            NotFoundError: On 404
            ValidationError: On 422
            RateLimitError: On 429
            ServerError: On 5xx
        """
        if response.status_code == 204:
            return {}

        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text or "Unknown error"}

        if response.is_success:
            return data

        detail = data.get("detail", "Unknown error")

        if response.status_code == 401:
            raise AuthenticationError(detail)
        elif response.status_code == 403:
            raise AuthorizationError(detail)
        elif response.status_code == 404:
            raise NotFoundError(detail)
        elif response.status_code == 422:
            raise ValidationError(detail)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 0))
            raise RateLimitError(detail, retry_after=retry_after)
        elif response.status_code >= 500:
            raise ServerError(detail, status_code=response.status_code)
        else:
            raise ServerError(detail, status_code=response.status_code)


class HealthClient(_BaseSubClient):
    """Health check client."""

    async def check(self) -> HealthStatus:
        """Check API Gateway health.

        Returns:
            HealthStatus object
        """
        logger.debug("Checking API Gateway health")
        response = await self._client.get("/health/live")
        data = await self._handle_response(response)
        return HealthStatus(**data)

    async def check_aggregated(self) -> Dict[str, Any]:
        """Check aggregated health of all services.

        Returns:
            Dict with status and services health
        """
        logger.debug("Checking aggregated health")
        response = await self._client.get("/health/aggregated")
        return await self._handle_response(response)


class UsersClient(_BaseSubClient):
    """Users management client."""

    async def get(self, telegram_id: int) -> User:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object
        """
        logger.debug(f"Getting user with telegram_id={telegram_id}")
        response = await self._client.get(f"/api/users/{telegram_id}")
        data = await self._handle_response(response)
        return User(**data)

    async def register(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
    ) -> User:
        """Register new user.

        Args:
            telegram_id: Telegram user ID
            username: Optional username
            first_name: Optional first name

        Returns:
            Created User object
        """
        logger.debug(f"Registering user with telegram_id={telegram_id}")
        payload = {"telegram_id": telegram_id}
        if username:
            payload["username"] = username
        if first_name:
            payload["first_name"] = first_name

        response = await self._client.post("/api/users/", json=payload)
        data = await self._handle_response(response)
        return User(**data)


class TokensClient(_BaseSubClient):
    """Tokens management client."""

    async def get_next(self, telegram_id: int) -> Token:
        """Get next available token for user (round-robin).

        Args:
            telegram_id: Telegram user ID

        Returns:
            Token object
        """
        logger.debug(f"Getting next token for telegram_id={telegram_id}")
        response = await self._client.get(f"/api/tokens/next/{telegram_id}")
        data = await self._handle_response(response)
        return Token(**data)

    async def add(
        self,
        telegram_id: int,
        plain_token: str,
        token_name: Optional[str] = None,
    ) -> Token:
        """Add new token for user.

        Args:
            telegram_id: Telegram user ID
            plain_token: Unencrypted token value
            token_name: Optional token name

        Returns:
            Created Token object
        """
        logger.debug(f"Adding token for telegram_id={telegram_id}")
        payload = {
            "telegram_id": telegram_id,
            "plain_token": plain_token,
        }
        if token_name:
            payload["token_name"] = token_name

        response = await self._client.post("/api/tokens/", json=payload)
        data = await self._handle_response(response)
        return Token(**data)

    async def delete(self, token_id: int) -> bool:
        """Delete token by ID.

        Args:
            token_id: Token ID

        Returns:
            True if deleted successfully
        """
        logger.debug(f"Deleting token_id={token_id}")
        response = await self._client.delete(f"/api/tokens/{token_id}")
        await self._handle_response(response)
        return True

    async def list(self, telegram_id: int) -> List[Token]:
        """List all tokens for user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            List of Token objects
        """
        logger.debug(f"Listing tokens for telegram_id={telegram_id}")
        response = await self._client.get(f"/api/tokens/{telegram_id}")
        data = await self._handle_response(response)
        return [Token(**item) for item in data]


class APIGatewayClient:
    """Async HTTP client for API Gateway.

    Usage:
        async with APIGatewayClient(base_url="http://api-gateway:8000") as client:
            # Health check
            health = await client.health.check()

            # Users
            user = await client.users.get(telegram_id=123)
            new_user = await client.users.register(telegram_id=456, username="test")

            # Tokens
            token = await client.tokens.get_next(telegram_id=123)
            await client.tokens.add(telegram_id=123, plain_token="abc")
            await client.tokens.delete(token_id=1)
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """Initialize API Gateway Client.

        Args:
            base_url: Base URL for API Gateway (e.g., http://localhost:8000)
            api_key: Optional JWT token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._health: Optional[HealthClient] = None
        self._users: Optional[UsersClient] = None
        self._tokens: Optional[TokensClient] = None

    async def __aenter__(self):
        """Enter context manager - create HTTP client."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers,
        )

        self._health = HealthClient(self._client)
        self._users = UsersClient(self._client)
        self._tokens = TokensClient(self._client)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - close HTTP client."""
        if self._client:
            await self._client.aclose()

    @property
    def health(self) -> HealthClient:
        """Health check client."""
        if self._health is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._health

    @property
    def users(self) -> UsersClient:
        """Users management client."""
        if self._users is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._users

    @property
    def tokens(self) -> TokensClient:
        """Tokens management client."""
        if self._tokens is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._tokens
