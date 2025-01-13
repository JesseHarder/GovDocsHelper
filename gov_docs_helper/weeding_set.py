"""A module for loading the information about your weeding dataset.

The weeding dataset is the list of documents in your collection that you wish to compare
against the FDLP Reference documents. This document should be a csv file
"""


from pathlib import Path
from typing import Dict, List

from _csv import reader as csv_reader

from gov_docs_helper.utils import simplify_sudoc_number


class WeedingSet:
    """The sudoc numbers that we want to locate in the FDLP set."""

    def __init__(
        self, weeding_set_file: Path, sudoc_number_header: str = "Document Number"
    ) -> None:
        """Initialize an SCUWeedingSet.

        Args:
            weeding_set_file: the path to the CSV file from which to read in the
                weeding set information.
            sudoc_number_header: the string that will be in the header row of the
                column in which the sudoc numbers can be found. This will be used to
                select the correct row from which to read the sudoc number.
                Default = "Document Number"
        """
        self._sudoc_number_header: str = sudoc_number_header
        self.headers: List[str] = []
        self.sudoc_numbers: set = set()
        self.sudoc_number_to_row_nums: Dict[str, str] = {}
        self.sudoc_row_num_to_row: Dict[int, List[str]] = {}

        # Read in the contents of the weeding set csv file that
        self._read_from_file(weeding_set_file)

    def _read_from_file(self, weeding_set_file: Path) -> None:
        """Read in the contents of the given CSV file and add it to the weeding set.

        Args:
            weeding_set_file: the csv file from which to read in the weeding
                set information.
        """
        # Open the provided file and read in from it.
        with weeding_set_file.open("r") as file_pointer:
            reader = csv_reader(file_pointer)
            # Grab the first row which has the headers.
            weeding_set_headers: List[str] = next(reader)
            # Build a set from the rest of the rows.
            for row_number, row in enumerate(reader, 2):
                self.sudoc_row_num_to_row[row_number] = row
                sudoc_number: str = row[
                    weeding_set_headers.index(self._sudoc_number_header)
                ]
                simplified_sudoc_number = simplify_sudoc_number(sudoc_number)
                self.sudoc_numbers.add(simplified_sudoc_number)
                # Record the row the sudoc number was found on.
                existing_rows = self.sudoc_number_to_row_nums.get(
                    simplified_sudoc_number, None
                )
                if existing_rows is None:
                    self.sudoc_number_to_row_nums[
                        simplified_sudoc_number
                    ] = f"{row_number}"
                else:
                    self.sudoc_number_to_row_nums[
                        simplified_sudoc_number
                    ] += f",{row_number}"
