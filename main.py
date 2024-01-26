"""A script to search for gov-docs of interest."""
from csv import reader as csv_reader
from pathlib import Path
from typing import List


def simplify_sudoc_number(sudoc_number: str) -> str:
    """Remove spaces from a sudoc number.

    Args:
        sudoc_number: a standard sudoc number string.

    Returns:
        A modified string with no spaces in it.
    """
    return sudoc_number.replace(" ", "")


def perform_sudoc_match(
    fdlp_reference_set_file: Path,
    scu_weeding_set_file: Path
):
    """Search for entries in the reference set from the weeding set .

    Args:
        fdlp_reference_set_file: a path to the reference set CSV file.
        scu_weeding_set_file: a path to the CSV file containing the weeding set.

    Returns:
        None.
    """
    # ------ Step 1 - Build our set of interest -----
    # Create the set of sudoc numbers from our weeding set that we want to locate in
    # the FDLP set.
    scu_sudoc_numbers: set = set()
    with scu_weeding_set_file.open("r") as file_pointer:
        reader = csv_reader(file_pointer)
        # Grab the first row which has the headers.
        headers: List[str] = next(reader)
        # Build a set from the rest of the rows.
        for row in reader:
            scu_sudoc_number: str = row[headers.index("Document Number")]
            scu_sudoc_number = simplify_sudoc_number(scu_sudoc_number)
            scu_sudoc_numbers.add(scu_sudoc_number)

    # ------ Step 2 - Search the FDLP reference -----


if __name__ == "__main__":
    perform_sudoc_match(
        fdlp_reference_set_file=Path(
            "./spreadsheets/PreviousFDLPDisposalListOffers-2023-12-2.csv"
        ),
        scu_weeding_set_file=Path(
            "./spreadsheets/SantaClara20240124.csv"
        )
    )
