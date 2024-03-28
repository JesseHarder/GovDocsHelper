"""A script to search for gov-docs of interest."""
from argparse import ArgumentParser
from csv import reader as csv_reader
from pathlib import Path
from typing import Dict, List, Optional, Set

from gov_docs_helper.utils import simplify_sudoc_number
from gov_docs_helper.writers import write_fdlp_matches_to_file, \
    write_scu_file_rows_matched

# Build the argument parser for main.
parser = ArgumentParser(prog="GovDocsHelper", description="Searches for sudoc matches.")
parser.add_argument(
    "--fdlp",
    type=str,
    default="./spreadsheets/PreviousFDLPDisposalListOffers-2023-12-2.csv",
)
parser.add_argument("--scu", type=str, default="./spreadsheets/SantaClaraTDDocs.csv")
parser.add_argument(
    "--out",
    type=str,
    default="./spreadsheets/output/",
    help="The path to the directory into which the results files will be written. If "
    "this directory does not exist, it will be created. Provide an empty string "
    "if you wish to skip writing out to file.",
)


def perform_sudoc_match(
    fdlp_reference_set_file: Path,
    scu_weeding_set_file: Path,
    output_dir: Optional[Path] = None,
):
    """Search for entries in the reference set from the weeding set .

    Args:
        fdlp_reference_set_file: a path to the reference set CSV file.
        scu_weeding_set_file: a path to the CSV file containing the weeding set.
        output_dir: where the results from the search should be saved. If not
            provided, the results will only be returned.

    Returns:
        A dictionary mapping row numbers to the rows (list of strings with the first
            value being the sudoc number)
    """
    # ------ Step 1 - Build our set of interest -----
    # Create the set of sudoc numbers from our weeding set that we want to locate in
    # the FDLP set.
    scu_sudoc_numbers: set = set()
    scu_sudoc_number_to_row_nums: Dict[str, str] = {}
    scu_sudoc_row_num_to_row: Dict[int, List[str]] = {}
    with scu_weeding_set_file.open("r") as file_pointer:
        reader = csv_reader(file_pointer)
        # Grab the first row which has the headers.
        scu_sudoc_headers: List[str] = next(reader)
        # Build a set from the rest of the rows.
        for row_number, row in enumerate(reader, 2):
            scu_sudoc_row_num_to_row[row_number] = row
            scu_sudoc_number: str = row[scu_sudoc_headers.index("Document Number")]
            simplified_scu_sudoc_number = simplify_sudoc_number(scu_sudoc_number)
            scu_sudoc_numbers.add(simplified_scu_sudoc_number)
            # Record the row the sudoc number was found on.
            existing_rows = scu_sudoc_number_to_row_nums.get(
                simplified_scu_sudoc_number, None
            )
            if existing_rows is None:
                scu_sudoc_number_to_row_nums[
                    simplified_scu_sudoc_number
                ] = f"{row_number}"
            else:
                scu_sudoc_number_to_row_nums[
                    simplified_scu_sudoc_number
                ] += f",{row_number}"

    # ------ Step 2 - Search the FDLP reference -----
    fdlp_rows_of_interest: Dict[int, List[str]] = {}
    scu_sudoc_row_nums_for_matches: Set[int] = set()
    with fdlp_reference_set_file.open("r") as file_pointer:
        reader = csv_reader(file_pointer)
        # Strip the first two rows. They don't have useful information.
        next(reader)
        next(reader)
        # Iterate over the rest, looking for matches.
        for fdlp_row_number, row in enumerate(reader, 3):
            # Get the sudoc number from the first column
            fdlp_sudoc_number: str = row[0]
            simplified_sudoc_number = simplify_sudoc_number(fdlp_sudoc_number)
            if simplified_sudoc_number in scu_sudoc_numbers:
                # Record the FDLP row as of interest.
                fdlp_rows_of_interest[fdlp_row_number] = row
                rows_nums = scu_sudoc_number_to_row_nums[simplified_sudoc_number].split(
                    ","
                )
                for row_num in rows_nums:
                    scu_sudoc_row_nums_for_matches.add(int(row_num))

    # Split the rows that need removing from the ones that don't.
    scu_rows_not_matched: List[List[str]] = []
    scu_rows_matched: List[List[str]] = []
    for scu_row_num, row in scu_sudoc_row_num_to_row.items():
        if scu_row_num in scu_sudoc_row_nums_for_matches:
            scu_rows_matched.append(row)
        else:
            scu_rows_not_matched.append(row)

    # ------ Step 3 - Optionally write the results to file. -----
    if output_dir:
        # Write out the FDLP file rows for which matches were found.
        write_fdlp_matches_to_file(
            fdlp_rows_of_interest=fdlp_rows_of_interest,
            scu_sudoc_number_to_row_nums=scu_sudoc_number_to_row_nums,
            output_dir=output_dir,
        )
        write_scu_file_rows_matched(
            scu_rows_matched=scu_rows_matched,
            headers_row=scu_sudoc_headers,
            output_dir=output_dir,
        )

    # ------ Step 4 - Return -----
    return fdlp_rows_of_interest


if __name__ == "__main__":
    args = parser.parse_args()
    fdlp_rows_of_interest = perform_sudoc_match(
        fdlp_reference_set_file=Path(args.fdlp),
        scu_weeding_set_file=Path(args.scu),
        output_dir=Path(args.out) if args.out else None,
    )
    print(f"Found {len(fdlp_rows_of_interest)} matches.")
