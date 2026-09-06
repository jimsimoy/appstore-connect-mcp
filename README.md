# appstore-connect-mcp

An MCP (Model Context Protocol) server that exposes a focused set of Apple
App Store Connect API operations as tools for an MCP-compatible AI client.

## Scope

This deliberately does not wrap the entire App Store Connect API. It covers:

- **Apps** — list apps, fetch one, look one up by bundle id
- **Provisioning (read-only)** — bundle ids, certificates, profiles
- **TestFlight** — builds, beta groups, beta testers
- **App Store version lifecycle** — list/get versions, create a new version
  on an existing app, attach a build, submit for review

It intentionally does **not** support first-time app creation or bundle ID
registration. Those actions set pricing, availability, and presuppose
Apple's developer agreements — treat that as a one-time action a human does
in the App Store Connect portal, not something to automate.

## Setup

Requires Python 3.12+ and an App Store Connect API key (Keys tab under
Users and Access in App Store Connect — generates a `.p8` file, a Key ID,
and gives you your account's Issuer ID).

```bash
uv sync
cp .env.example .env   # fill in ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH
```

Run directly:

```bash
uv run appstore-connect-mcp
```

Or point an MCP client at it, e.g. in a client's server config:

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

## Security

- The private key is referenced **by path** only, never embedded in code or
  config committed to this repo. `.env`, `.env.*` (except `.env.example`),
  and `*.p8` are gitignored.
- `submit_for_review` is a real, consequential action — it starts Apple's
  App Review for the given version. There's no dry-run mode; know what
  you're calling it on.
- This key's actual permission scope (App Manager vs. Admin, which apps
  it can see) is whatever was granted when the key was created in App
  Store Connect — this server doesn't add or remove any of that.
