# App Store Connect MCP — Apple App Store Automation for AI Clients

<div align="center">

<img src="https://img.shields.io/badge/python-3.12%2B-blue.svg?style=flat-square" alt="Python 3.12+">
<a href="https://github.com/jimsimoy/appstore-connect-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green.svg?style=flat-square" alt="MCP Compatible"></a>
<img src="https://img.shields.io/badge/tools-24-brightgreen.svg?style=flat-square" alt="24 Tools">
<img src="https://img.shields.io/badge/package%20manager-uv-orange.svg?style=flat-square" alt="Managed with uv">

**24 tools for a focused slice of the App Store Connect API, ready to use inside Claude Desktop, Claude Code, and any MCP-compatible AI client.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

## What is this?

App Store Connect MCP is a [Model Context Protocol](https://modelcontextprotocol.io) server that gives AI assistants direct, structured access to Apple's App Store Connect API. It authenticates with your App Store Connect API key and exposes apps, provisioning data, TestFlight, App Store version lifecycle, and store listing content (metadata, screenshots) as typed MCP tools.

It deliberately does **not** wrap the entire App Store Connect API. First-time app creation and bundle ID registration are excluded on purpose — those actions set pricing and availability and presuppose Apple's developer agreements, so they stay a one-time action a human does in the App Store Connect portal, not something an AI agent automates.

**Supported platform:** any MCP client on macOS, Linux, or Windows with Python 3.12+.

---

## Tools

| Category | Tools | What you can do |
|---|---|---|
| **Apps** | 3 | List apps, fetch one by id, look one up by bundle id |
| **Provisioning** (read-only) | 3 | List bundle ids, certificates, and profiles |
| **TestFlight** | 3 | List builds, beta groups, and beta testers |
| **App Store Versions** | 5 | List/get versions, create a new version, attach a build, submit for review |
| **App Info** | 3 | Read/update app name, subtitle, privacy policy URL per locale |
| **Store Listing Content** | 2 | Read/update description, keywords, promo text, URLs, what's new per locale |
| **Screenshots** | 5 | List/create screenshot sets, list/upload/delete screenshots |

There is no App Store "icon" upload endpoint — the Store listing icon always comes from the app binary's own 1024pt icon asset, so there's nothing to manage separately here.

<details>
<summary>Full tool reference</summary>

| Tool | Description |
|---|---|
| `list_apps` | List all apps visible to the API key |
| `get_app` | Fetch a single app by its App Store Connect id |
| `find_app_by_bundle_id` | Look up an app by its bundle identifier |
| `list_bundle_ids` | List registered bundle ids |
| `list_certificates` | List signing certificates |
| `list_profiles` | List provisioning profiles |
| `list_builds` | List TestFlight builds for an app |
| `list_beta_groups` | List beta groups for an app |
| `list_beta_testers` | List testers in a beta group |
| `list_app_store_versions` | List App Store versions for an app |
| `get_app_store_version` | Fetch a single App Store version |
| `create_app_store_version` | Create a new version on an existing app |
| `attach_build_to_version` | Attach a TestFlight build to a version |
| `submit_for_review` | Submit a version for App Review |
| `list_app_infos` | List an app's appInfo records |
| `list_app_info_localizations` | List per-locale name/subtitle/privacy-policy-url |
| `update_app_info_localization` | Update name/subtitle/privacy-policy-url for one locale |
| `list_app_store_version_localizations` | List per-locale description/keywords/URLs/what's-new |
| `update_app_store_version_localization` | Update store listing content for one locale |
| `list_app_screenshot_sets` | List screenshot sets (one per device size) for a locale |
| `create_app_screenshot_set` | Create a screenshot set for one device display type |
| `list_app_screenshots` | List screenshots in a set, with upload/processing state |
| `upload_app_screenshot` | Upload one local image file into a screenshot set (reserve/upload/commit) |
| `delete_app_screenshot` | Remove one screenshot |

</details>

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.12 or later |
| [uv](https://docs.astral.sh/uv/) | any recent version |
| App Store Connect API key | Keys tab under Users and Access |

You'll need an App Store Connect API key: generate one from the **Keys** tab under **Users and Access** in App Store Connect. That gives you a `.p8` private key file, a Key ID, and your account's Issuer ID.

---

## Installation

```bash
git clone https://github.com/jimsimoy/appstore-connect-mcp.git
cd appstore-connect-mcp
uv sync
cp .env.example .env   # fill in ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH
```

Run directly:

```bash
uv run appstore-connect-mcp
```

---

## Client Setup

Point an MCP client at the server via its config file, e.g.:

```json
{
  "mcpServers": {
    "appstore-connect": {
      "command": "uv",
      "args": ["--directory", "/path/to/appstore-connect-mcp", "run", "appstore-connect-mcp"],
      "env": {
        "ASC_KEY_ID": "...",
        "ASC_ISSUER_ID": "...",
        "ASC_KEY_PATH": "/absolute/path/to/AuthKey_XXXXXXXXXX.p8"
      }
    }
  }
}
```

Restart your MCP client after saving. The 24 App Store Connect tools will appear automatically.

---

## Usage Examples

### Look up an app

```
Find the app with bundle id com.example.myapp and show its current status
```

### Check TestFlight

```
List the builds and beta groups for app 123456789
```

### Ship a new version

```
Create a new App Store version 1.2.0 for app 123456789, attach build 42, and submit it for review
```

### Fill in store listing content

```
Set the description, keywords, and support URL for app 123456789's en-US listing
```

### Upload screenshots

```
Create an iPhone 6.7" screenshot set for app 123456789's en-US listing and upload
these 3 PNG files into it
```

---

## Security

- The private key is referenced **by path** only, never embedded in code or config committed to this repo. `.env`, `.env.*` (except `.env.example`), and `*.p8` are gitignored.
- `submit_for_review` is a real, consequential action — it starts Apple's App Review for the given version. There's no dry-run mode; know what you're calling it on.
- This key's actual permission scope (App Manager vs. Admin, which apps it can see) is whatever was granted when the key was created in App Store Connect — this server doesn't add or remove any of that.

---

## Project Structure

```
src/appstore_connect_mcp/
  server.py   # MCP server entry point and tool definitions
  client.py   # App Store Connect API client
  auth.py     # JWT signing and API key handling
```

The server communicates over stdio using JSON-RPC 2.0, the standard MCP transport.

---

## License

[MIT](./LICENSE) — free to use, modify, and distribute.

---

<div align="center">

[Report a Bug](https://github.com/jimsimoy/appstore-connect-mcp/issues) · [Request a Feature](https://github.com/jimsimoy/appstore-connect-mcp/issues)

</div>
