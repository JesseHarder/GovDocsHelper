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


def write_scu_file_rows_matched(
    scu_rows_matched: List[List[str]],
    headers_row: List[str],
    output_dir: Path,
    file_name: str = "scu_rows_matched.csv",
) -> None:
    # Create the directory into which to write the output.
    output_dir.mkdir(parents=True, exist_ok=True)
    scu_rows_matched_output_file = output_dir / file_name
    # Create the results that we want to write out.
    rows = [headers_row] + scu_rows_matched

    # Write to file.
    with scu_rows_matched_output_file.open("w") as file_pointer:
        writer = csv_writer(file_pointer)
        writer.writerows(rows)


def write_scu_file_rows_not_matched(
    scu_rows_not_matched: List[List[str]],
    headers_row: List[str],
    output_dir: Path,
    not_matches_dir_name: str = "scu_rows_not_matched",
    file_name_start: str = "rows_not_matched",
    start_index: int = 1,
    max_rows: int = 250
) -> None:
    # Create the directory into which to write the output.
    not_matches_dir: Path = output_dir / not_matches_dir_name
    not_matches_dir.mkdir(parents=True, exist_ok=True)

    # Help-er function to write less code twice.
    def write_out(rows_to_write: List[List[str]], file_index: int) -> None:
        # Write out to file.
        not_matches_file = not_matches_dir / f"{file_name_start}_{file_index}.csv"
        with not_matches_file.open("w") as file_pointer:
            writer = csv_writer(file_pointer)
            # Write the headers.
            writer.writerow(headers_row)
            # Write the rows.
            writer.writerows(rows_to_write)

    file_index: int = start_index
    rows_to_write: List[List[str]] = []
    for row in scu_rows_not_matched:
        # If we haven't reached our limit, add another row.
        if len(rows_to_write) < max_rows - 1:
            rows_to_write.append(row)
        else:
            # Write out to file.
            write_out(rows_to_write=rows_to_write, file_index=file_index)
            # Reset the rows to write
            rows_to_write = []
            # Increment the output file index.
            file_index += 1

    # If we have any rows left unwritten, write them out as well.
    if len(rows_to_write) > 0:
        # Write out to file.
        write_out(rows_to_write=rows_to_write, file_index=file_index)
        # Reset the rows to write
        rows_to_write = []
        # Increment the output file index.
        file_index += 1
