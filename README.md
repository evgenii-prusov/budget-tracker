# Budget Tracker

Personal finance application for tracking income, expenses, and transfers.

<!-- [![CI](https://github.com/evgenii-prusov/budget-tracker/actions/workflows/ci.yml/badge.svg)](...) -->
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](...)

## Features

- Multi-account tracking (bank, cash, credit cards)
- Multi-currency support
- Invoice OCR scanning
- Budget management
- Spending reports
- **AI Assistant Integration** - MCP server for Claude/AI assistants
- **Telegram Bot** - Communication channel complimenting the app

## Quick Start

**Development (local)**

```bash
git clone ...  # TODO: Add repo URL
cd budget-tracker
make install
make db-up       # start Postgres
make db-migrate  # run migrations
make run         # start dev server (stop with Ctrl+C; make db-down to stop Postgres)
```

**Production (Docker)**

```bash
export API_KEY=your-secret-key
make docker-build   # build image (first time only)
make docker-up      # start Postgres + backend, runs migrations
make docker-down    # stop everything
```

The API will be available at `http://localhost:8000`.  
See [backend/README.md](./backend/README.md#production-docker) for full Docker documentation.

To run tests:

```bash
make test
```

## Connecting AI Assistants (MCP)

The app exposes an MCP (Model Context Protocol) server at `/mcp` using Streamable HTTP transport. After starting the production instance, you can connect AI assistants to it.

### Claude Desktop

1. Open **Settings → Integrations → Add more**
2. Name it (e.g., "Budget Tracker") and enter the MCP URL
3. Claude will prompt for authentication — provide your `API_KEY` as Bearer token

Alternatively, use `mcp-remote` in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "budget-tracker": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--header",
        "Authorization: Bearer ${API_KEY}"
      ]
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add --transport http budget-tracker http://localhost:8000/mcp \
  --header "Authorization: Bearer your-secret-key"
```

### Claude Mobile (iOS / Android)

Claude mobile syncs MCP integrations configured on the web — it cannot connect to `localhost` directly.

1. **Expose your server** to the internet using a tunnel:
   ```bash
   # Option A: ngrok
   ngrok http 8000
   # → gives you https://xxxx.ngrok-free.app

   # Option B: Cloudflare Tunnel
   cloudflared tunnel --url localhost:8000
   # → gives you https://xxxx.trycloudflare.com
   ```
2. Go to [claude.ai](https://claude.ai) → **Settings → Integrations → Add more**
3. Enter the public tunnel URL (e.g., `https://xxxx.ngrok-free.app/mcp`)
4. The integration syncs automatically to your mobile app
5. Requires a Max, Team, or Enterprise plan

### Gemini

Gemini's **web UI and mobile app do not support custom MCP servers**. However:

- **Gemini CLI** (runs on your Mac) supports MCP natively:
  ```bash
  gemini mcp add --transport http budget-tracker http://localhost:8000/mcp
  ```
- **Gemini in Android Studio** supports remote MCP via `httpUrl` configuration.
- **Gemini Enterprise** (Google Cloud) supports custom MCP servers but requires a public HTTPS URL.

For Gemini Enterprise or Android Studio, expose your server via a tunnel as described above.

### Verify the Connection

Once connected, ask your AI assistant:
> "List my accounts" or "Show my spending report for this month"

If everything is set up correctly, the assistant will call the `list_accounts` or `get_spending` MCP tools.

## Documentation

See [docs/](./docs/) for full documentation.

## Tech Stack

Python 3.12, FastAPI, SQLAlchemy, pytest, Ruff, uv
