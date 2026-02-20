import asyncio
import unittest

import httpx

from app.main import app


class TestMetricsEndpoint(unittest.TestCase):
    def test_metrics_endpoint_is_available(self) -> None:
        async def _request_metrics() -> httpx.Response:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                return await client.get("/metrics")

        response = asyncio.run(_request_metrics())
        self.assertEqual(response.status_code, 200)
        self.assertIn("# HELP", response.text)


if __name__ == "__main__":
    unittest.main()
