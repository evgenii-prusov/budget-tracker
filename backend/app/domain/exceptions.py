class InsufficientFundsError(Exception):
    """Raised when an operation would result in a negative account balance."""

    pass


class DuplicateAccountNameError(Exception):
    """Raised when attempting to create an account with a duplicate name."""

    pass


class InvalidInitialBalanceError(Exception):
    """Raised when attempting to create an account with a negative initial balance."""

    pass
