"""A script to search for gov-docs of interest."""
from csv import reader as csv_reader
from pathlib import Path
from typing import List, Dict


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
        A dictionary mapping row numbers to the rows (list of strings with the first
            value being the sudoc number)
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
    rows_of_interest: Dict[int, List[str]] = {}
    with fdlp_reference_set_file.open("r") as file_pointer:
        reader = csv_reader(file_pointer)
        # Strip the first two rows. They don't have useful information.
        next(reader)
        next(reader)
        # Iterate over the rest, looking for matches.
        for row_number, row in enumerate(reader, 3):
            # Get the sudoc number from the first column
            fdlp_sudoc_number: str = row[0]
            if simplify_sudoc_number(fdlp_sudoc_number) in scu_sudoc_numbers:
                rows_of_interest[row_number] = row

    return rows_of_interest


if __name__ == "__main__":
    rows_of_interest = perform_sudoc_match(
        fdlp_reference_set_file=Path(
            "./spreadsheets/PreviousFDLPDisposalListOffers-2023-12-2.csv"
        ),
        scu_weeding_set_file=Path(
            "./spreadsheets/SantaClara20240124.csv"
        )
    )
    print(len(rows_of_interest))
