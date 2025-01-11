"""A script to search for gov-docs of interest."""
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from gov_docs_helper.readers import FDLPReader, SCUWeedingSet
from gov_docs_helper.writers import (
    write_scu_file_rows_matched,
    write_scu_file_rows_not_matched,
)

# Build the argument parser for main.
parser = ArgumentParser(prog="GovDocsHelper", description="Searches for sudoc matches.")
parser.add_argument(
    "--fdlp-pre",
    type=str,
    default="./spreadsheets/PreviousFDLPDisposalListOffersThroughAugust2021.csv",
)
parser.add_argument(
    "--fdlp-post",
    type=str,
    default="./spreadsheets/FDLP-eXchange-offers-2022-01-to-2024-02.csv",
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
    fdlp_reference_set_file_pre_exchange: Path,
    fdlp_reference_set_file_post_exchange: Path,
    scu_weeding_set_file: Path,
    output_dir: Optional[Path] = None,
) -> FDLPReader:
    """Search for entries in the reference set from the weeding set .

    Args:
        fdlp_reference_set_file_pre_exchange: a path to the reference set CSV file from
            before the exchange.
        fdlp_reference_set_file_post_exchange: a path to the reference set CSV file
            from after the exchange.
        scu_weeding_set_file: a path to the CSV file containing the weeding set.
        output_dir: where the results from the search should be saved. If not
            provided, the results will only be returned.
        fdlp_sudoc_number_column_index: The index for the column that contains the sudoc
            numbers in the FDLP file, where the first column in the file has index 0.
            Default = 2.

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
    fdlp_reader.read_from_file(
        fdlp_reference_set_file_pre_exchange,
        skip_rows=1,
        sudoc_number_column_index=2,
        classification_type="SuDoc",
        classification_type_column_index=1,
        header_row_index=0,
    )
    fdlp_reader.read_from_file(
        fdlp_reference_set_file_post_exchange,
        skip_rows=0,
        sudoc_number_column_index=6,
        classification_type="SuDoc",
        classification_type_column_index=0,
        header_row_index=None,
    )
    fdlp_reader.separate_rows()

    # ------ Step 3 - Optionally write the results to file. -----
    if output_dir:
        # Write out the FDLP file rows for which matches were found.
        fdlp_reader.write_matches_to_file(output_dir=output_dir)
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
    return fdlp_reader


if __name__ == "__main__":
    args = parser.parse_args()
    fdlp_reader = perform_sudoc_match(
        fdlp_reference_set_file_pre_exchange=Path(args.fdlp_pre),
        fdlp_reference_set_file_post_exchange=Path(args.fdlp_post),
        scu_weeding_set_file=Path(args.scu),
        output_dir=Path(args.out) if args.out else None,
    )
    num_rows_of_interest = sum(
        len(reference_doc.rows_of_interest)
        for reference_doc in fdlp_reader.reference_docs
    )
    print(f"Found {num_rows_of_interest} matches.")
