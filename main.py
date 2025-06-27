"""A script to search for gov-docs of interest."""
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Optional

from gov_docs_helper.fdlp_reference import FDLPReferenceDoc, FDLPSearcher
from gov_docs_helper.weeding_set import WeedingSet
from gov_docs_helper.writers import (
    write_weeding_set_file_rows_matched,
    write_weeding_set_file_rows_not_matched,
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
parser.add_argument(
    "--max-rows",
    type=int,
    default=250,
    help="The maximum number of rows that the output sheets can have."
)


def perform_sudoc_match(
    fdlp_reference_set_file_pre_exchange: Path,
    fdlp_reference_set_file_post_exchange: Path,
    weeding_set_file: Path,
    output_dir: Optional[Path] = None,
    max_rows: int = 250,
) -> FDLPSearcher:
    """Search for entries in the reference set from the weeding set .

    Args:
        fdlp_reference_set_file_pre_exchange: a path to the reference set CSV file from
            before the exchange.
        fdlp_reference_set_file_post_exchange: a path to the reference set CSV file
            from after the exchange.
        weeding_set_file: a path to the CSV file containing the weeding set.
        output_dir: where the results from the search should be saved. If not
            provided, the results will only be returned.
        max_rows: what is the maximum number of rows that may appear in each CSV file.
            This will be used to determine how to split up the information that is
            being written out. Default = 250. (Note: this code includes the header row
            in the count of the number of rows.)

    Returns:
        A dictionary mapping row numbers to the rows (list of strings with the first
            value being the sudoc number)
    """
    # ------ Step 1 - Build our set of interest -----
    # Create the set of sudoc numbers from our weeding set that we want to locate in
    # the FDLP set.
    weeding_set = WeedingSet(weeding_set_file)

    # ------ Step 2 - Search the FDLP reference -----
    fdlp_reference_docs: List[FDLPReferenceDoc] = [
        FDLPReferenceDoc(
            fdlp_reference_set_file_pre_exchange,
            skip_rows=1,
            sudoc_number_column_index=2,
            classification_type="SuDoc",
            classification_type_column_index=1,
            header_row_index=0,
        ),
        FDLPReferenceDoc(
            fdlp_reference_set_file_post_exchange,
            skip_rows=0,
            sudoc_number_column_index=6,
            classification_type="SuDoc",
            classification_type_column_index=0,
            header_row_index=None,
        ),
    ]
    fdlp_searcher = FDLPSearcher(weeding_set)
    fdlp_searcher.search_fdlp_references(fdlp_reference_docs)

    # ------ Step 3 - Optionally write the results to file. -----
    if output_dir:
        # Write out the FDLP file rows for which matches were found.
        fdlp_searcher.write_matches_to_file(output_dir=output_dir)
        write_weeding_set_file_rows_matched(
            weeding_set_rows_matched=fdlp_searcher.weeding_set_rows_matched,
            headers_row=weeding_set.headers,
            output_dir=output_dir,
            file_name="scu_rows_matched.csv",
        )
        write_weeding_set_file_rows_not_matched(
            weeding_set_rows_not_matched=fdlp_searcher.weeding_set_rows_not_matched,
            headers_row=weeding_set.headers,
            output_dir=output_dir,
            not_matches_dir_name="scu_rows_not_matched",
            max_rows=max_rows
        )

    # ------ Step 4 - Return -----
    return fdlp_searcher


if __name__ == "__main__":
    args = parser.parse_args()
    fdlp_searcher = perform_sudoc_match(
        fdlp_reference_set_file_pre_exchange=Path(args.fdlp_pre),
        fdlp_reference_set_file_post_exchange=Path(args.fdlp_post),
        weeding_set_file=Path(args.scu),
        output_dir=Path(args.out) if args.out else None,
        max_rows=args.max_rows
    )
    num_rows_of_interest = sum(
        len(reference_doc.rows_of_interest)
        for reference_doc in fdlp_searcher.reference_docs
    )
    print(f"Found {num_rows_of_interest} matches.")
