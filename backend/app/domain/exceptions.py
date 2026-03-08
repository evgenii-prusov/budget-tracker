class InsufficientFundsError(Exception):
    """Raised when an operation would result in a negative account balance."""

    pass


class DuplicateAccountNameError(Exception):
    """Raised when attempting to create an account with a duplicate name."""

    pass


class InvalidInitialBalanceError(Exception):
    """Raised when attempting to create an account with a negative initial balance."""

    pass


class InvalidCurrencyError(Exception):
    """Raised when attempting to create an account with an invalid currency code."""

    pass


class AccountNotFoundError(Exception):
    """Raised when an account with the given ID does not exist."""

    pass


class AccountHasTransfersError(Exception):
    """Raised when attempting to delete an account that has transfers."""

    pass


class AccountHasPostingsError(Exception):
    """Raised when attempting to delete an account that has postings."""

    pass


class DuplicateCategoryNameError(Exception):
    """Raised when attempting to create a category with a duplicate name."""

    pass


class CategoryNotFoundError(Exception):
    """Raised when a category with the given ID does not exist."""

    pass


class CategoryInUseError(Exception):
    """Raised when attempting to delete a category that is in use (has transactions)."""

    pass


class CategoryHierarchyError(Exception):
    """Raised when category hierarchy constraints are violated."""

    pass


class ParentCategoryPostingError(Exception):
    """Raised when attempting to create a posting with a parent category (must use subcategory)."""

    pass


class CategoryHasChildrenError(Exception):
    """Raised when attempting to delete a parent category that has children."""

    pass


class PostingNotFoundError(Exception):
    """Raised when a posting with the given ID does not exist."""

    pass


class TransferNotFoundError(Exception):
    """Raised when a transfer with the given ID does not exist."""

    pass
