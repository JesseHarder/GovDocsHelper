"""Utility code for working with Gov Docs information."""


def simplify_sudoc_number(sudoc_number: str) -> str:
    """Remove spaces from a sudoc number.

    Args:
        sudoc_number: a standard sudoc number string.

    Returns:
        A modified string with no spaces in it.
    """
    return sudoc_number.replace(" ", "")
