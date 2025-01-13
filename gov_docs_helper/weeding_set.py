from _csv import reader as csv_reader
from pathlib import Path
from typing import Optional, Dict, List

from gov_docs_helper.utils import simplify_sudoc_number


class WeedingSet:
    """The sudoc numbers that we want to locate in the FDLP set."""

    def __init__(self, weeding_set_file: Optional[Path] = None) -> None:
        """Initialize an SCUWeedingSet.

        If a file is provided to read from, the initialization will read from it and
        be set based on the file's contents. If no file is provided, then the set will
        start as an empty file.

        Args:
              weeding_set_file: an optional file from which to read in the weeding
                set information.
        """
        self.headers: List[str] = []
        self.sudoc_numbers: set = set()
        self.sudoc_number_to_row_nums: Dict[str, str] = {}
        self.sudoc_row_num_to_row: Dict[int, List[str]] = {}

        # If an input file was provided, read in its contents.
        if weeding_set_file:
            self.read_from_file(weeding_set_file)

    def read_from_file(self, scu_weeding_set_file: Path) -> None:
        """Read in the contents of the given CSV file and add it to the weeding set.

        Args:
            scu_weeding_set_file: the csv file from which to read in the weeding
                set information.
        """
        # Open the provided file and read in from it.
        with scu_weeding_set_file.open("r") as file_pointer:
            reader = csv_reader(file_pointer)
            # Grab the first row which has the headers.
            scu_sudoc_headers: List[str] = next(reader)
            # Build a set from the rest of the rows.
            for row_number, row in enumerate(reader, 2):
                self.sudoc_row_num_to_row[row_number] = row
                scu_sudoc_number: str = row[scu_sudoc_headers.index("Document Number")]
                simplified_scu_sudoc_number = simplify_sudoc_number(scu_sudoc_number)
                self.sudoc_numbers.add(simplified_scu_sudoc_number)
                # Record the row the sudoc number was found on.
                existing_rows = self.sudoc_number_to_row_nums.get(
                    simplified_scu_sudoc_number, None
                )
                if existing_rows is None:
                    self.sudoc_number_to_row_nums[
                        simplified_scu_sudoc_number
                    ] = f"{row_number}"
                else:
                    self.sudoc_number_to_row_nums[
                        simplified_scu_sudoc_number
                    ] += f",{row_number}"

    def reset(self) -> None:
        """Empty the contents of this SCUWeedingSet."""
        self.sudoc_numbers = set()
        self.sudoc_number_to_row_nums = {}
        self.sudoc_row_num_to_row = {}
        self.headers = []
