from datetime import UTC, datetime, timedelta

import httpx


class FactusAsyncClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        client_id: str,
        client_secret: str,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._email = email
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._http_client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    async def close(self) -> None:
        await self._http_client.aclose()

    async def authenticate(self, force_refresh: bool = False) -> str:
        if not force_refresh and self._access_token and self._token_expires_at:
            if datetime.now(UTC) < self._token_expires_at:
                return self._access_token

        response = await self._http_client.post(
            "/oauth/token",
            data={
                "email": self._email,
                "password": self._password,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        payload = response.json()

        token = payload.get("access_token")
        if not token:
            raise RuntimeError("Factus authentication failed: missing access_token")

        expires_in = int(payload.get("expires_in", 3600))
        self._access_token = token
        self._token_expires_at = datetime.now(UTC) + timedelta(
            seconds=max(expires_in - 30, 0)
        )
        return token

    async def get_active_numbering_range_id(self) -> int:
        token = await self.authenticate()
        response = await self._request_numbering_ranges(token)

        if response.status_code == httpx.codes.UNAUTHORIZED:
            token = await self.authenticate(force_refresh=True)
            response = await self._request_numbering_ranges(token)

        response.raise_for_status()
        payload = response.json()
        ranges = payload.get("data", payload)
        if not isinstance(ranges, list):
            raise RuntimeError("Factus numbering ranges response is invalid")

        for range_item in ranges:
            if not isinstance(range_item, dict):
                continue
            is_active = range_item.get("is_active")
            if is_active is None:
                is_active = range_item.get("active")
            if is_active:
                range_id = range_item.get("id")
                if range_id is None:
                    break
                return int(range_id)

        raise RuntimeError("Factus active numbering range not found")

    async def _request_numbering_ranges(self, token: str) -> httpx.Response:
        return await self._http_client.get(
            "/v1/numbering-ranges",
            headers={"Authorization": f"Bearer {token}"},
        )
