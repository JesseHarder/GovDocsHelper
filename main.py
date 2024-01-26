"""A script to search for gov-docs of interest."""
from argparse import ArgumentParser
from csv import reader as csv_reader
from csv import writer as csv_writer
from pathlib import Path
from typing import Dict, List, Optional

# Build the argument parser for main.
parser = ArgumentParser(prog="GovDocsHelper", description="Searches for sudoc matches.")
parser.add_argument(
    "--fdlp",
    type=str,
    default="./spreadsheets/PreviousFDLPDisposalListOffers-2023-12-2.csv",
)
parser.add_argument("--scu", type=str, default="./spreadsheets/SantaClara20240124.csv")
parser.add_argument("--out", type=str, default="")


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
    scu_weeding_set_file: Path,
    output_file: Optional[Path] = None,
):
    """Search for entries in the reference set from the weeding set .

    Args:
        fdlp_reference_set_file: a path to the reference set CSV file.
        scu_weeding_set_file: a path to the CSV file containing the weeding set.
        output_file: where the results from the search should be saved. If not
            provided, the results will only be returned.

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

    # ------ Step 3 - Optionally write the results to file. -----
    if output_file:
        # Create the results that we want to write out.
        rows = [row + [row_number] for row_number, row in rows_of_interest.items()]

        # Create header row.
        headers = ["" for _ in rows[0]]
        headers[0] = "Document Number"
        headers[1] = "Year(s)"
        headers[2] = "Title"
        headers[3] = "Reviewed Date"
        headers[-1] = "Original Row Number"
        # Insert it at the front of the rows to write out.
        rows.insert(0, headers)

        # Write to file.
        with output_file.open("w") as file_pointer:
            writer = csv_writer(file_pointer)
            writer.writerows(rows)

    # ------ Step 4 - Return -----
    return rows_of_interest


if __name__ == "__main__":
    args = parser.parse_args()
    rows_of_interest = perform_sudoc_match(
        fdlp_reference_set_file=Path(args.fdlp),
        scu_weeding_set_file=Path(args.scu),
        output_file=Path(args.out) if args.out else None,
    )
    print(f"Found {len(rows_of_interest)} matches.")
