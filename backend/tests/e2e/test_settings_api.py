"""E2E tests for settings API endpoints."""


class TestGetSettingsDefaults:
    def test_get_settings_returns_defaults(self, client):
        """GET /settings → 200, primary_currency="EUR"."""
        response = client.get("/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["primary_currency"] == "EUR"


class TestUpdateSettings:
    def test_update_settings(self, client):
        """PATCH /settings {"primary_currency": "USD"} → 200, verify GET returns USD."""
        response = client.patch("/settings", json={"primary_currency": "USD"})
        assert response.status_code == 200
        assert response.json()["primary_currency"] == "USD"

        # Verify GET returns updated value
        get_response = client.get("/settings")
        assert get_response.status_code == 200
        assert get_response.json()["primary_currency"] == "USD"


class TestUpdateSettingsInvalidCurrency:
    def test_update_settings_invalid_currency_returns_422(self, client):
        """PATCH with "INVALID" → 422."""
        response = client.patch("/settings", json={"primary_currency": "INVALID"})
        assert response.status_code == 422


class TestSettingsUnauthorized:
    def test_unauthorized_returns_401(self, client_no_auth):
        """client_no_auth GET /settings → 401."""
        response = client_no_auth.get("/settings")
        assert response.status_code == 401
