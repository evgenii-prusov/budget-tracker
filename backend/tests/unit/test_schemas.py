import pytest
from pydantic import ValidationError

from app.api.schemas import AccountCreate, AccountUpdate


class TestAccountNameValidation:
    """Account names should allow Unicode characters (Cyrillic, CJK, etc.)."""

    def test_create_account_with_cyrillic_name(self):
        acc = AccountCreate(name="Revolute Женя", currency="EUR")
        assert acc.name == "Revolute Женя"

    def test_update_account_with_cyrillic_name(self):
        update = AccountUpdate(name="Revolute Женя")
        assert update.name == "Revolute Женя"

    def test_create_account_with_ascii_name_still_works(self):
        acc = AccountCreate(name="My Account", currency="USD")
        assert acc.name == "My Account"

    def test_create_account_with_digits_and_hyphens(self):
        acc = AccountCreate(name="Account-123 Test", currency="USD")
        assert acc.name == "Account-123 Test"

    def test_create_account_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="", currency="USD")

    def test_create_account_rejects_too_short_name(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Ab", currency="USD")

    def test_create_account_rejects_special_chars(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Account@#$", currency="USD")

    def test_create_account_with_chinese_name(self):
        acc = AccountCreate(name="我的账户", currency="CNY")
        assert acc.name == "我的账户"

    def test_create_account_with_mixed_scripts(self):
        acc = AccountCreate(name="Счёт EUR-123", currency="EUR")
        assert acc.name == "Счёт EUR-123"

    def test_create_account_rejects_leading_underscore(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="_Account", currency="USD")

    def test_create_account_rejects_underscore_in_word(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="My__Account", currency="USD")

    def test_create_account_allows_underscore_as_separator(self):
        acc = AccountCreate(name="My_Account", currency="USD")
        assert acc.name == "My_Account"
