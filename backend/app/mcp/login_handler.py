"""Login/consent page for OAuth 2.1 MCP authentication.

Renders a simple HTML form that asks for the owner password.
On success, creates an authorization code and redirects back to the client.
"""

from __future__ import annotations

from html import escape
from urllib.parse import urlencode

import bcrypt
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from app.mcp.oauth_provider import PostgresOAuthProvider

_LOGIN_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Budget Tracker — Sign In</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 400px;
           margin: 80px auto; padding: 0 16px; }}
    h1 {{ font-size: 1.4rem; }}
    label {{ display: block; margin-top: 12px; font-weight: 600; }}
    input[type=password] {{ width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; }}
    button {{ margin-top: 16px; padding: 10px 24px; cursor: pointer; }}
    .error {{ color: #c00; margin-top: 12px; }}
  </style>
</head>
<body>
  <h1>Budget Tracker</h1>
  <p>Sign in to authorize <strong>{client_id}</strong>.</p>
  {error_html}
  <form method="POST" action="/login">
    <input type="hidden" name="client_id" value="{client_id}">
    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
    <input type="hidden" name="redirect_uri_provided_explicitly"
           value="{redirect_uri_provided_explicitly}">
    <input type="hidden" name="state" value="{state}">
    <input type="hidden" name="code_challenge" value="{code_challenge}">
    <input type="hidden" name="scopes" value="{scopes}">
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required autofocus>
    <button type="submit">Sign in</button>
  </form>
</body>
</html>"""


def _render_form(
    *,
    client_id: str,
    redirect_uri: str,
    redirect_uri_provided_explicitly: str,
    state: str,
    code_challenge: str,
    scopes: str,
    error: str | None = None,
) -> HTMLResponse:
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""
    html = _LOGIN_HTML.format(
        client_id=escape(client_id),
        redirect_uri=escape(redirect_uri),
        redirect_uri_provided_explicitly=escape(redirect_uri_provided_explicitly),
        state=escape(state),
        code_challenge=escape(code_challenge),
        scopes=escape(scopes),
        error_html=error_html,
    )
    return HTMLResponse(html)


async def _get_login(request: Request) -> HTMLResponse:
    params = request.query_params
    return _render_form(
        client_id=params.get("client_id", ""),
        redirect_uri=params.get("redirect_uri", ""),
        redirect_uri_provided_explicitly=params.get("redirect_uri_provided_explicitly", "True"),
        state=params.get("state", ""),
        code_challenge=params.get("code_challenge", ""),
        scopes=params.get("scopes", ""),
    )


async def _post_login(request: Request) -> HTMLResponse | RedirectResponse:
    provider: PostgresOAuthProvider = request.app.state.oauth_provider
    form = await request.form()

    client_id = str(form.get("client_id", ""))
    redirect_uri = str(form.get("redirect_uri", ""))
    redirect_uri_provided_explicitly = str(form.get("redirect_uri_provided_explicitly", "True"))
    state = str(form.get("state", ""))
    code_challenge = str(form.get("code_challenge", ""))
    scopes_str = str(form.get("scopes", ""))
    password = str(form.get("password", ""))

    # Verify password
    if not password or not bcrypt.checkpw(
        password.encode("utf-8"),
        provider._owner_password_hash.encode("utf-8"),
    ):
        return _render_form(
            client_id=client_id,
            redirect_uri=redirect_uri,
            redirect_uri_provided_explicitly=redirect_uri_provided_explicitly,
            state=state,
            code_challenge=code_challenge,
            scopes=scopes_str,
            error="Invalid password. Please try again.",
        )

    # Create authorization code
    scopes = scopes_str.split() if scopes_str else []
    code = await provider.create_authorization_code(
        client_id=client_id,
        redirect_uri=redirect_uri,
        redirect_uri_provided_explicitly=redirect_uri_provided_explicitly == "True",
        scopes=scopes,
        code_challenge=code_challenge,
    )

    # Redirect back to the client
    query = urlencode({"code": code, "state": state})
    return RedirectResponse(url=f"{redirect_uri}?{query}", status_code=302)


def create_login_app(provider: PostgresOAuthProvider) -> Starlette:
    """Create a Starlette app for the login page, used both standalone and mounted."""
    app = Starlette(
        routes=[
            Route("/login", _get_login, methods=["GET"]),
            Route("/login", _post_login, methods=["POST"]),
        ],
    )
    app.state.oauth_provider = provider
    return app
