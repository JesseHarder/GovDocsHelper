"""This file contains code for writing the results of our GovDocs search to file."""
from csv import writer as csv_writer
from pathlib import Path
from typing import Dict, List

from gov_docs_helper.utils import simplify_sudoc_number


def write_fdlp_matches_to_file(
    fdlp_rows_of_interest: Dict[int, List[str]],
    scu_sudoc_number_to_row_nums: Dict[str, str],
    output_dir: Path,
    file_name: str = "FDLP_rows.csv",
) -> None:
    # Create the directory into which to write the output.
    output_dir.mkdir(parents=True, exist_ok=True)
    # ----- Step 3A - Write our the matched FDLP rows -----
    fdlp_matches_output_file = output_dir / file_name
    # Create the results that we want to write out.
    rows = [
        row + [row_number, scu_sudoc_number_to_row_nums[simplify_sudoc_number(row[0])]]
        for row_number, row in fdlp_rows_of_interest.items()
    ]

    # Create header row.
    headers = ["" for _ in rows[0]]
    headers[0] = "Document Number"
    headers[1] = "Year(s)"
    headers[2] = "Title"
    headers[3] = "Reviewed Date"
    headers[-2] = "Original Row in FDLP"
    headers[-1] = "Row(s) in SCU file"
    # Insert it at the front of the rows to write out.
    rows.insert(0, headers)

    # Write to file.
    with fdlp_matches_output_file.open("w") as file_pointer:
        writer = csv_writer(file_pointer)
        writer.writerows(rows)
