"""A script to search for gov-docs of interest."""
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from gov_docs_helper.readers import FDLPReader, SCUWeedingSet
from gov_docs_helper.writers import (
    write_fdlp_matches_to_file,
    write_scu_file_rows_matched,
    write_scu_file_rows_not_matched,
)

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
    scu_weeding_set = SCUWeedingSet(scu_weeding_set_file)

    # ------ Step 2 - Search the FDLP reference -----
    fdlp_reader = FDLPReader(scu_weeding_set)
    fdlp_reader.read_from_file(fdlp_reference_set_file)
    fdlp_reader.separate_rows()

    # ------ Step 3 - Optionally write the results to file. -----
    if output_dir:
        # Write out the FDLP file rows for which matches were found.
        write_fdlp_matches_to_file(
            fdlp_rows_of_interest=fdlp_reader.fdlp_rows_of_interest,
            scu_sudoc_number_to_row_nums=scu_weeding_set.sudoc_number_to_row_nums,
            output_dir=output_dir,
        )
        write_scu_file_rows_matched(
            scu_rows_matched=fdlp_reader.scu_rows_matched,
            headers_row=scu_weeding_set.scu_sudoc_headers,
            output_dir=output_dir,
        )
        write_scu_file_rows_not_matched(
            scu_rows_not_matched=fdlp_reader.scu_rows_not_matched,
            headers_row=scu_weeding_set.scu_sudoc_headers,
            output_dir=output_dir,
        )

    # ------ Step 4 - Return -----
    return fdlp_reader.fdlp_rows_of_interest


if __name__ == "__main__":
    args = parser.parse_args()
    fdlp_rows_of_interest = perform_sudoc_match(
        fdlp_reference_set_file=Path(args.fdlp),
        scu_weeding_set_file=Path(args.scu),
        output_dir=Path(args.out) if args.out else None,
    )
    print(f"Found {len(fdlp_rows_of_interest)} matches.")
