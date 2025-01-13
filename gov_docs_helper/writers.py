"""This file contains code for writing the results of our GovDocs search to file."""
from csv import writer as csv_writer
from pathlib import Path
from typing import List


def write_seeding_set_file_rows_matched(
    weeding_set_rows_matched: List[List[str]],
    headers_row: List[str],
    output_dir: Path,
    file_name: str = "weeding_set_rows_matched.csv",
) -> None:
    """Write out rows from the weeding set with matches in the FDLP references.

    Args:
        weeding_set_rows_matched: The rows to write out into the CSV file.
        headers_row: The header row for the file.
        output_dir: a Path to the directory into which to write the file.
        file_name: the name for the CSV file into which to write the matches.
    """
    # Create the directory into which to write the output.
    output_dir.mkdir(parents=True, exist_ok=True)
    scu_rows_matched_output_file = output_dir / file_name
    # Create the results that we want to write out.
    rows = [headers_row] + weeding_set_rows_matched

    # Write to file.
    with scu_rows_matched_output_file.open("w") as file_pointer:
        writer = csv_writer(file_pointer)
        writer.writerows(rows)


def write_weeding_set_file_rows_not_matched(
    weeding_set_rows_not_matched: List[List[str]],
    headers_row: List[str],
    output_dir: Path,
    not_matches_dir_name: str = "weeding_set_rows_not_matched",
    file_name_start: str = "rows_not_matched",
    start_index: int = 1,
    max_rows: int = 250,
) -> None:
    """Write out rows from the weeding set without matches in the FDLP references.

    Args:
        weeding_set_rows_not_matched: The rows to write out into the CSV files.
        headers_row: The header row for the files.
        output_dir: a Path to the directory into which to create the
            directory for the non-matches, if necessary.
        not_matches_dir_name: a name for the directory into which to write the files.
        file_name_start: the starting name for the CSV file into which to write the
            matches. Indices numbers will be appended to the different files created to
            differentiate them.
        start_index: what number to append to the first file written. Default = 1.
        max_rows: what is the maximum number of rows that may appear in each CSV file.
            This will be used to determine how to split up the information that is
            being written out. Default = 250. (Note: this code includes the header row
            in the count of the number of rows.)
    """
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
    for row in weeding_set_rows_not_matched:
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
