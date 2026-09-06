"""MCP server exposing a focused set of App Store Connect API operations.

Scope is deliberately narrow rather than wrapping the whole API surface:
app/build/TestFlight visibility, and the app-store-version lifecycle actions
needed to ship a build that already has an app record. It does NOT expose
first-time app creation or bundle ID registration — those touch pricing,
availability and the developer agreements, and are treated as a one-time
human action in the App Store Connect portal, not something to automate.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from .auth import AscCredentials, TokenProvider
from .client import AscClient

mcp = MCPServer(
    name="appstore-connect",
    version="0.1.0",
    instructions=(
        "Read and manage App Store Connect apps, builds, TestFlight, and "
        "app-store-version submission for apps that already have an app "
        "record. Requires ASC_KEY_ID, ASC_ISSUER_ID, and ASC_KEY_PATH to be "
        "set in the environment."
    ),
)

_client: AscClient | None = None


def _get_client() -> AscClient:
    global _client
    if _client is None:
        credentials = AscCredentials.from_env()
        _client = AscClient(TokenProvider(credentials))
    return _client


# --- App management -------------------------------------------------------


@mcp.tool()
async def list_apps() -> list[dict[str, Any]]:
    """List every app visible to this API key: id, bundle id, name, sku."""
    client = _get_client()
    rows = await client.get_all_pages("/apps")
    return [_summarize_app(row) for row in rows]


@mcp.tool()
async def get_app(app_id: str) -> dict[str, Any]:
    """Fetch one app's full attributes by its App Store Connect app id."""
    client = _get_client()
    body = await client.get(f"/apps/{app_id}")
    return body.get("data", {})


@mcp.tool()
async def find_app_by_bundle_id(bundle_id: str) -> dict[str, Any] | None:
    """Look up an app by its bundle identifier (e.g. com.example.app). Returns None if it doesn't exist yet."""
    client = _get_client()
    rows = await client.get_all_pages("/apps", params={"filter[bundleId]": bundle_id})
    if not rows:
        return None
    return _summarize_app(rows[0])


def _summarize_app(row: dict[str, Any]) -> dict[str, Any]:
    attrs = row.get("attributes", {})
    return {
        "id": row.get("id"),
        "bundleId": attrs.get("bundleId"),
        "name": attrs.get("name"),
        "sku": attrs.get("sku"),
        "primaryLocale": attrs.get("primaryLocale"),
    }


# --- Provisioning (read-only) ----------------------------------------------


@mcp.tool()
async def list_bundle_ids() -> list[dict[str, Any]]:
    """List registered Bundle IDs and whether each is used for an app."""
    client = _get_client()
    rows = await client.get_all_pages("/bundleIds")
    return [
        {
            "id": row.get("id"),
            "identifier": row.get("attributes", {}).get("identifier"),
            "name": row.get("attributes", {}).get("name"),
            "platform": row.get("attributes", {}).get("platform"),
        }
        for row in rows
    ]


@mcp.tool()
async def list_certificates() -> list[dict[str, Any]]:
    """List signing certificates on the account (type, name, expiry)."""
    client = _get_client()
    rows = await client.get_all_pages("/certificates")
    return [
        {
            "id": row.get("id"),
            "name": row.get("attributes", {}).get("name"),
            "certificateType": row.get("attributes", {}).get("certificateType"),
            "expirationDate": row.get("attributes", {}).get("expirationDate"),
        }
        for row in rows
    ]


@mcp.tool()
async def list_profiles() -> list[dict[str, Any]]:
    """List provisioning profiles on the account."""
    client = _get_client()
    rows = await client.get_all_pages("/profiles")
    return [
        {
            "id": row.get("id"),
            "name": row.get("attributes", {}).get("name"),
            "profileType": row.get("attributes", {}).get("profileType"),
            "profileState": row.get("attributes", {}).get("profileState"),
            "expirationDate": row.get("attributes", {}).get("expirationDate"),
        }
        for row in rows
    ]


# --- TestFlight -------------------------------------------------------------


@mcp.tool()
async def list_builds(app_id: str) -> list[dict[str, Any]]:
    """List TestFlight builds for an app: version, build number, processing state."""
    client = _get_client()
    rows = await client.get_all_pages(f"/apps/{app_id}/builds")
    return [
        {
            "id": row.get("id"),
            "version": row.get("attributes", {}).get("version"),
            "processingState": row.get("attributes", {}).get("processingState"),
            "uploadedDate": row.get("attributes", {}).get("uploadedDate"),
        }
        for row in rows
    ]


@mcp.tool()
async def list_beta_groups(app_id: str) -> list[dict[str, Any]]:
    """List TestFlight beta groups (internal/external) for an app."""
    client = _get_client()
    rows = await client.get_all_pages(f"/apps/{app_id}/betaGroups")
    return [
        {
            "id": row.get("id"),
            "name": row.get("attributes", {}).get("name"),
            "isInternalGroup": row.get("attributes", {}).get("isInternalGroup"),
            "publicLinkEnabled": row.get("attributes", {}).get("publicLinkEnabled"),
        }
        for row in rows
    ]


@mcp.tool()
async def list_beta_testers(beta_group_id: str) -> list[dict[str, Any]]:
    """List testers in a TestFlight beta group."""
    client = _get_client()
    rows = await client.get_all_pages(f"/betaGroups/{beta_group_id}/betaTesters")
    return [
        {
            "id": row.get("id"),
            "email": row.get("attributes", {}).get("email"),
            "firstName": row.get("attributes", {}).get("firstName"),
            "lastName": row.get("attributes", {}).get("lastName"),
            "inviteType": row.get("attributes", {}).get("inviteType"),
        }
        for row in rows
    ]


# --- App Store version lifecycle --------------------------------------------


@mcp.tool()
async def list_app_store_versions(app_id: str) -> list[dict[str, Any]]:
    """List App Store versions for an app: version string, platform, state."""
    client = _get_client()
    rows = await client.get_all_pages(f"/apps/{app_id}/appStoreVersions")
    return [_summarize_version(row) for row in rows]


@mcp.tool()
async def get_app_store_version(version_id: str) -> dict[str, Any]:
    """Fetch one App Store version's full attributes, including appStoreState."""
    client = _get_client()
    body = await client.get(f"/appStoreVersions/{version_id}")
    return _summarize_version(body.get("data", {}))


def _summarize_version(row: dict[str, Any]) -> dict[str, Any]:
    attrs = row.get("attributes", {})
    return {
        "id": row.get("id"),
        "versionString": attrs.get("versionString"),
        "platform": attrs.get("platform"),
        "appStoreState": attrs.get("appStoreState"),
        "releaseType": attrs.get("releaseType"),
    }


@mcp.tool()
async def create_app_store_version(
    app_id: str, version_string: str, platform: str = "IOS"
) -> dict[str, Any]:
    """Create a new App Store version on an EXISTING app record (does not create the app itself)."""
    client = _get_client()
    body = await client.post(
        "/appStoreVersions",
        {
            "data": {
                "type": "appStoreVersions",
                "attributes": {"versionString": version_string, "platform": platform},
                "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
            }
        },
    )
    return _summarize_version(body.get("data", {}))


@mcp.tool()
async def attach_build_to_version(version_id: str, build_id: str) -> dict[str, Any]:
    """Attach a processed TestFlight build to an App Store version, ready for submission."""
    client = _get_client()
    await client.patch(
        f"/appStoreVersions/{version_id}",
        {
            "data": {
                "type": "appStoreVersions",
                "id": version_id,
                "relationships": {"build": {"data": {"type": "builds", "id": build_id}}},
            }
        },
    )
    return await get_app_store_version(version_id)


@mcp.tool()
async def submit_for_review(version_id: str) -> dict[str, Any]:
    """Submit an App Store version for Apple review.

    This is a real, consequential action: it starts Apple's App Review
    (typically 24-48h) for the given version. Confirm the version has a
    build attached and all required metadata before calling this.
    """
    client = _get_client()
    body = await client.post(
        "/appStoreVersionSubmissions",
        {
            "data": {
                "type": "appStoreVersionSubmissions",
                "relationships": {
                    "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}
                },
            }
        },
    )
    return body.get("data", {})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
