"""Minimal async client for Apple's App Store Connect API (JSON:API v1)."""

from __future__ import annotations

from typing import Any

import httpx

from .auth import TokenProvider

_BASE_URL = "https://api.appstoreconnect.apple.com/v1"


class AscApiError(RuntimeError):
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"App Store Connect API error {status_code}: {body}")


class AscClient:
    def __init__(self, token_provider: TokenProvider) -> None:
        self._tokens = token_provider
        self._http = httpx.AsyncClient(base_url=_BASE_URL, timeout=30.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._tokens.get_token()}"}

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json_body=json_body)

    async def patch(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PATCH", path, json_body=json_body)

    async def delete(self, path: str) -> None:
        await self._request("DELETE", path)

    async def upload_bytes(
        self, url: str, method: str, headers: list[dict[str, str]], content: bytes
    ) -> None:
        """PUT/POST raw bytes to a pre-signed upload URL (e.g. from an uploadOperations
        entry). These URLs are not on api.appstoreconnect.apple.com and must NOT carry
        our Bearer token — only the exact headers Apple returned for that operation."""
        header_map = {h["name"]: h["value"] for h in headers}
        response = await self._http.request(method, url, headers=header_map, content=content)
        if response.status_code >= 300:
            raise AscApiError(response.status_code, response.text)

    async def get_all_pages(
        self, path: str, params: dict[str, Any] | None = None, max_pages: int = 10
    ) -> list[dict[str, Any]]:
        """Follow JSON:API `links.next` up to max_pages, returning the concatenated `data`."""
        results: list[dict[str, Any]] = []
        next_path = path
        next_params = params
        for _ in range(max_pages):
            page = await self._request("GET", next_path, params=next_params)
            results.extend(page.get("data", []))
            next_url = page.get("links", {}).get("next")
            if not next_url:
                break
            # `next` is a fully-qualified URL already carrying query params.
            next_path = next_url.removeprefix(_BASE_URL)
            next_params = None
        return results

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = await self._http.request(
            method, path, params=params, json=json_body, headers=self._headers()
        )
        if response.status_code >= 400:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            raise AscApiError(response.status_code, body)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()
