"""PostgreSQL-backed OAuth 2.1 provider for the MCP server.

Subclasses FastMCP's OAuthProvider, replacing in-memory dicts with
PostgreSQL tables. Uses SA Core (not ORM) since these are infrastructure
tables, not domain entities.
"""

from __future__ import annotations

import secrets
import time
from urllib.parse import urlencode

import sqlalchemy as sa
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from sqlalchemy import Engine

from fastmcp.server.auth.auth import (
    ClientRegistrationOptions,
    OAuthProvider,
    RevocationOptions,
)

# Default expiration times (in seconds)
AUTH_CODE_EXPIRY_SECONDS = 5 * 60  # 5 minutes
ACCESS_TOKEN_EXPIRY_SECONDS = 60 * 60  # 1 hour

# ── SA Core table definitions ────────────────────────────────────────

oauth_tables_metadata = sa.MetaData()

oauth_client_table = sa.Table(
    "oauth_client",
    oauth_tables_metadata,
    sa.Column("client_id", sa.String, primary_key=True),
    sa.Column("client_info_json", sa.Text, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
)

oauth_authorization_code_table = sa.Table(
    "oauth_authorization_code",
    oauth_tables_metadata,
    sa.Column("code", sa.String, primary_key=True),
    sa.Column("client_id", sa.String, nullable=False),
    sa.Column("redirect_uri", sa.Text, nullable=False),
    sa.Column("redirect_uri_provided_explicitly", sa.Boolean, nullable=False),
    sa.Column("scopes", sa.Text, nullable=False),
    sa.Column("code_challenge", sa.String, nullable=False),
    sa.Column("expires_at", sa.Float, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
)

oauth_access_token_table = sa.Table(
    "oauth_access_token",
    oauth_tables_metadata,
    sa.Column("token", sa.String, primary_key=True),
    sa.Column("client_id", sa.String, nullable=False),
    sa.Column("scopes", sa.Text, nullable=False),
    sa.Column("expires_at", sa.Integer, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
)

oauth_refresh_token_table = sa.Table(
    "oauth_refresh_token",
    oauth_tables_metadata,
    sa.Column("token", sa.String, primary_key=True),
    sa.Column("client_id", sa.String, nullable=False),
    sa.Column("scopes", sa.Text, nullable=False),
    sa.Column("expires_at", sa.Integer, nullable=True),
    sa.Column("access_token", sa.String, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
)


class PostgresOAuthProvider(OAuthProvider):
    """OAuth 2.1 provider backed by PostgreSQL tables.

    The ``engine`` can be provided at init time or set later via
    ``set_engine()`` — this allows the provider to be constructed before
    the database URL is available (e.g. at module-import time in tests).
    """

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        owner_password_hash: str,
        base_url: str,
        client_registration_options: ClientRegistrationOptions | None = None,
        revocation_options: RevocationOptions | None = None,
    ):
        super().__init__(
            base_url=base_url,
            client_registration_options=client_registration_options
            or ClientRegistrationOptions(enabled=True),
            revocation_options=revocation_options or RevocationOptions(enabled=True),
        )
        self._engine = engine
        self._owner_password_hash = owner_password_hash

    def set_engine(self, engine: Engine) -> None:
        """Set the SQLAlchemy engine (called during lifespan init)."""
        self._engine = engine

    @property
    def _db(self) -> Engine:
        """Return the engine, raising if not yet initialized."""
        if self._engine is None:
            raise RuntimeError("OAuth provider engine not initialized — call set_engine() first")
        return self._engine

    # ── Client management ────────────────────────────────────────────

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        with self._db.connect() as conn:
            row = conn.execute(
                sa.select(oauth_client_table.c.client_info_json).where(
                    oauth_client_table.c.client_id == client_id
                )
            ).first()
        if row is None:
            return None
        return OAuthClientInformationFull.model_validate_json(row[0])

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if client_info.client_id is None:
            raise ValueError("client_id is required for client registration")

        json_str = client_info.model_dump_json()
        with self._db.begin() as conn:
            # Upsert: delete existing then insert (simple, portable)
            conn.execute(
                oauth_client_table.delete().where(
                    oauth_client_table.c.client_id == client_info.client_id
                )
            )
            conn.execute(
                oauth_client_table.insert().values(
                    client_id=client_info.client_id,
                    client_info_json=json_str,
                    created_at=time.time(),
                )
            )

    # ── Authorization ────────────────────────────────────────────────

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Redirect to the login page instead of auto-approving."""
        if client.client_id is None:
            raise AuthorizeError(error="invalid_client", error_description="Client ID is required")

        query = urlencode(
            {
                "client_id": client.client_id,
                "redirect_uri": str(params.redirect_uri),
                "redirect_uri_provided_explicitly": str(params.redirect_uri_provided_explicitly),
                "state": params.state or "",
                "code_challenge": params.code_challenge,
                "scopes": " ".join(params.scopes) if params.scopes else "",
            }
        )

        # Build login URL relative to the MCP base URL
        base = str(self.base_url).rstrip("/")
        return f"{base}/login?{query}"

    # ── Authorization code management ────────────────────────────────

    async def create_authorization_code(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        redirect_uri_provided_explicitly: bool,
        scopes: list[str],
        code_challenge: str,
        expires_at: float | None = None,
    ) -> str:
        """Create and persist an authorization code. Called by the login handler."""
        code_value = secrets.token_urlsafe(32)
        if expires_at is None:
            expires_at = time.time() + AUTH_CODE_EXPIRY_SECONDS

        with self._db.begin() as conn:
            conn.execute(
                oauth_authorization_code_table.insert().values(
                    code=code_value,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    redirect_uri_provided_explicitly=redirect_uri_provided_explicitly,
                    scopes=" ".join(scopes),
                    code_challenge=code_challenge,
                    expires_at=expires_at,
                    created_at=time.time(),
                )
            )
        return code_value

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        with self._db.connect() as conn:
            row = conn.execute(
                sa.select(oauth_authorization_code_table).where(
                    oauth_authorization_code_table.c.code == authorization_code
                )
            ).first()

        if row is None:
            return None

        # Check client_id match
        if row.client_id != client.client_id:
            return None

        # Check expiry
        if row.expires_at < time.time():
            # Clean up expired code
            with self._db.begin() as conn:
                conn.execute(
                    oauth_authorization_code_table.delete().where(
                        oauth_authorization_code_table.c.code == authorization_code
                    )
                )
            return None

        scopes = row.scopes.split() if row.scopes else []
        return AuthorizationCode(
            code=row.code,
            client_id=row.client_id,
            redirect_uri=row.redirect_uri,
            redirect_uri_provided_explicitly=row.redirect_uri_provided_explicitly,
            scopes=scopes,
            expires_at=row.expires_at,
            code_challenge=row.code_challenge,
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        # Consume the authorization code
        with self._db.begin() as conn:
            result = conn.execute(
                oauth_authorization_code_table.delete().where(
                    oauth_authorization_code_table.c.code == authorization_code.code
                )
            )
            if result.rowcount == 0:
                raise TokenError("invalid_grant", "Authorization code not found or already used.")

        if client.client_id is None:
            raise TokenError("invalid_client", "Client ID is required")

        # Generate tokens
        access_token_value = secrets.token_urlsafe(32)
        refresh_token_value = secrets.token_urlsafe(32)
        access_expires_at = int(time.time() + ACCESS_TOKEN_EXPIRY_SECONDS)
        scopes_str = " ".join(authorization_code.scopes)
        now = time.time()

        with self._db.begin() as conn:
            conn.execute(
                oauth_access_token_table.insert().values(
                    token=access_token_value,
                    client_id=client.client_id,
                    scopes=scopes_str,
                    expires_at=access_expires_at,
                    created_at=now,
                )
            )
            conn.execute(
                oauth_refresh_token_table.insert().values(
                    token=refresh_token_value,
                    client_id=client.client_id,
                    scopes=scopes_str,
                    expires_at=None,
                    access_token=access_token_value,
                    created_at=now,
                )
            )

        return OAuthToken(
            access_token=access_token_value,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRY_SECONDS,
            refresh_token=refresh_token_value,
            scope=scopes_str,
        )

    # ── Token loading ────────────────────────────────────────────────

    async def load_access_token(self, token: str) -> AccessToken | None:  # type: ignore[override]
        if self._engine is None:
            return None
        with self._db.connect() as conn:
            row = conn.execute(
                sa.select(oauth_access_token_table).where(oauth_access_token_table.c.token == token)
            ).first()

        if row is None:
            return None

        # Check expiry
        if row.expires_at < time.time():
            await self._revoke_by_access_token(token)
            return None

        scopes = row.scopes.split() if row.scopes else []
        return AccessToken(
            token=row.token,
            client_id=row.client_id,
            scopes=scopes,
            expires_at=row.expires_at,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        with self._db.connect() as conn:
            row = conn.execute(
                sa.select(oauth_refresh_token_table).where(
                    oauth_refresh_token_table.c.token == refresh_token
                )
            ).first()

        if row is None:
            return None

        if row.client_id != client.client_id:
            return None

        if row.expires_at is not None and row.expires_at < time.time():
            await self._revoke_by_refresh_token(refresh_token)
            return None

        scopes = row.scopes.split() if row.scopes else []
        return RefreshToken(
            token=row.token,
            client_id=row.client_id,
            scopes=scopes,
            expires_at=row.expires_at,
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Validate scopes
        original_scopes = set(refresh_token.scopes)
        requested_scopes = set(scopes)
        if not requested_scopes.issubset(original_scopes):
            raise TokenError(
                "invalid_scope",
                "Requested scopes exceed those authorized by the refresh token.",
            )

        if client.client_id is None:
            raise TokenError("invalid_client", "Client ID is required")

        # Revoke old token pair
        await self._revoke_by_refresh_token(refresh_token.token)

        # Issue new tokens
        new_access = secrets.token_urlsafe(32)
        new_refresh = secrets.token_urlsafe(32)
        access_expires_at = int(time.time() + ACCESS_TOKEN_EXPIRY_SECONDS)
        scopes_str = " ".join(scopes)
        now = time.time()

        with self._db.begin() as conn:
            conn.execute(
                oauth_access_token_table.insert().values(
                    token=new_access,
                    client_id=client.client_id,
                    scopes=scopes_str,
                    expires_at=access_expires_at,
                    created_at=now,
                )
            )
            conn.execute(
                oauth_refresh_token_table.insert().values(
                    token=new_refresh,
                    client_id=client.client_id,
                    scopes=scopes_str,
                    expires_at=None,
                    access_token=new_access,
                    created_at=now,
                )
            )

        return OAuthToken(
            access_token=new_access,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRY_SECONDS,
            refresh_token=new_refresh,
            scope=scopes_str,
        )

    # ── Token verification (TokenVerifier protocol) ──────────────────

    async def verify_token(self, token: str) -> AccessToken | None:  # type: ignore[override]
        return await self.load_access_token(token)

    # ── Token revocation ─────────────────────────────────────────────

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        if isinstance(token, AccessToken):
            await self._revoke_by_access_token(token.token)
        elif isinstance(token, RefreshToken):
            await self._revoke_by_refresh_token(token.token)

    async def _revoke_by_access_token(self, access_token: str) -> None:
        """Remove an access token and its paired refresh token."""
        with self._db.begin() as conn:
            # Find paired refresh token
            conn.execute(
                oauth_refresh_token_table.delete().where(
                    oauth_refresh_token_table.c.access_token == access_token
                )
            )
            conn.execute(
                oauth_access_token_table.delete().where(
                    oauth_access_token_table.c.token == access_token
                )
            )

    async def _revoke_by_refresh_token(self, refresh_token: str) -> None:
        """Remove a refresh token and its paired access token."""
        with self._db.begin() as conn:
            # Find the associated access token first
            row = conn.execute(
                sa.select(oauth_refresh_token_table.c.access_token).where(
                    oauth_refresh_token_table.c.token == refresh_token
                )
            ).first()
            if row:
                conn.execute(
                    oauth_access_token_table.delete().where(
                        oauth_access_token_table.c.token == row[0]
                    )
                )
            conn.execute(
                oauth_refresh_token_table.delete().where(
                    oauth_refresh_token_table.c.token == refresh_token
                )
            )
