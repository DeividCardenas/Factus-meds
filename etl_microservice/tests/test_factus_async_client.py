import unittest
import json

import httpx

from app.invoicing.infrastructure.api.factus.factus_async_client import FactusAsyncClient


class TestFactusAsyncClient(unittest.IsolatedAsyncioTestCase):
    async def test_reuses_token_until_expiration(self) -> None:
        calls = {"token": 0, "ranges": 0}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                calls["token"] += 1
                return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
            if request.url.path == "/v1/numbering-ranges":
                calls["ranges"] += 1
                return httpx.Response(200, json={"data": [{"id": 9, "is_active": True}]})
            return httpx.Response(404)

        client = FactusAsyncClient(
            base_url="https://api-sandbox.factus.com.co",
            email="email@example.com",
            password="secret",
            client_id="client-id",
            client_secret="client-secret",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(await client.get_active_numbering_range_id(), 9)
        self.assertEqual(await client.get_active_numbering_range_id(), 9)
        await client.close()

        self.assertEqual(calls["token"], 1)
        self.assertEqual(calls["ranges"], 2)

    async def test_reauthenticates_on_401(self) -> None:
        calls = {"token": 0, "ranges": 0}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                calls["token"] += 1
                return httpx.Response(
                    200,
                    json={"access_token": f"token-{calls['token']}", "expires_in": 3600},
                )

            if request.url.path == "/v1/numbering-ranges":
                calls["ranges"] += 1
                if request.headers.get("Authorization") == "Bearer token-1":
                    return httpx.Response(401, json={"message": "Unauthorized"})
                return httpx.Response(200, json={"data": [{"id": 11, "is_active": True}]})

            return httpx.Response(404)

        client = FactusAsyncClient(
            base_url="https://api-sandbox.factus.com.co",
            email="email@example.com",
            password="secret",
            client_id="client-id",
            client_secret="client-secret",
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(await client.get_active_numbering_range_id(), 11)
        await client.close()
        self.assertEqual(calls["token"], 2)

    async def test_create_invoice_posts_validate_payload(self) -> None:
        captured_payload = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/oauth/token":
                return httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
            if request.url.path == "/v1/bills/validate":
                nonlocal captured_payload
                captured_payload = dict(json.loads(request.content.decode()))
                return httpx.Response(200, json={"data": {"id": 123, "qr": "qr-code", "pdf": "pdf-url"}})
            return httpx.Response(404)

        client = FactusAsyncClient(
            base_url="https://api-sandbox.factus.com.co",
            email="email@example.com",
            password="secret",
            client_id="client-id",
            client_secret="client-secret",
            transport=httpx.MockTransport(handler),
        )

        response = await client.create_invoice(
            {"reference_code": "INV-1", "customer": {"identification": "CUST-1"}, "items": []},
            numbering_range_id=15,
        )
        await client.close()

        self.assertEqual(captured_payload["numbering_range_id"], 15)
        self.assertEqual(captured_payload["reference_code"], "INV-1")
        self.assertEqual(response["data"]["id"], 123)
