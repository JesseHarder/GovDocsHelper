"""Module containing code for reading information out of our input CSV files."""

from csv import reader as csv_reader
from pathlib import Path
from typing import Dict, List, Optional, Set

from gov_docs_helper.utils import simplify_sudoc_number


class SCUWeedingSet:
    """The sudoc numbers that we want to locate in the FDLP set."""

    def __init__(self, scu_weeding_set_file: Optional[Path] = None) -> None:
        """Initialize an SCUWeedingSet.

        If a file is provided to read from, the initialization will read from it and
        be set based on the file's contents. If no file is provided, then the set will
        start as an empty file.

        Args:
              scu_weeding_set_file: an optional file from which to read in the weeding
                set information.
        """
        self.sudoc_numbers: set = set()
        self.sudoc_number_to_row_nums: Dict[str, str] = {}
        self.sudoc_row_num_to_row: Dict[int, List[str]] = {}
        self.scu_sudoc_headers: List[str] = []

        # If an input file was provided, read in its contents.
        if scu_weeding_set_file:
            self.read_from_file(scu_weeding_set_file)

    def reset(self) -> None:
        """Empty the contents of this SCUWeedingSet."""
        self.sudoc_numbers = set()
        self.sudoc_number_to_row_nums = {}
        self.sudoc_row_num_to_row = {}
        self.scu_sudoc_headers = []

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


class FDLPReader:
    """Class to read through an FDLP file and extract the needed information."""

    def __init__(self, scu_weeding_set: SCUWeedingSet):
        """Initialize an FDLPReader.

        Args:
            scu_weeding_set: an SCUWeedingSet instance.
        """
        # The SCUWeedingSet off which on which to match.
        self.scu_weeding_set: SCUWeedingSet = scu_weeding_set

        self.fdlp_rows_of_interest: Dict[int, List[str]] = {}
        self.scu_sudoc_row_nums_for_matches: Set[int] = set()
        self.scu_rows_not_matched: List[List[str]] = []
        self.scu_rows_matched: List[List[str]] = []

    def reset(self) -> None:
        """Empty the contents of this SCUWeedingSet."""
        self.fdlp_rows_of_interest = {}
        self.scu_sudoc_row_nums_for_matches = set()
        self.scu_rows_not_matched = []
        self.scu_rows_matched = []

    def read_from_file(
        self,
        fdlp_reference_set_file: Path,
        skip_rows: int = 1,
        sudoc_number_column_index: int = 2,
        classification_type: Optional[str] = "SuDoc",
        classification_type_column_index: int = 1,
    ) -> None:
        """Read through an FDLP reference file and find matching information.

        Args:
            fdlp_reference_set_file: the csv file from which to read.
            skip_rows: the number of rows to skip at the top of the file before reading
                for actual content. Typically, these are empty rows or a header row.
                Default = 1.
            sudoc_number_column_index: The index for the column that contains the sudoc
                numbers, where the first column in the file has index 0. Default = 2.
            classification_type: a string to match for the correct classification type.
                Any row with a different classifiction type will be ignored. If None,
                then all classification types will be accepted. Default = "SuDoc".
            classification_type_column_index: The index for the column that
                contains the classification_types, where the first column in the file
                has index 0. Default = 1.

        Returns:
            None
        """

        with fdlp_reference_set_file.open("r") as file_pointer:
            reader = csv_reader(file_pointer)
            # Iterate over the rest, looking for matches.
            for fdlp_row_number, row in enumerate(reader, skip_rows):
                # Skip the row if it has an invalid classification type:
                if classification_type:
                    if row[classification_type_column_index] != classification_type:
                        continue
                # Get the sudoc number from the specified column
                fdlp_sudoc_number: str = row[sudoc_number_column_index]
                simplified_sudoc_number = simplify_sudoc_number(fdlp_sudoc_number)
                if simplified_sudoc_number in self.scu_weeding_set.sudoc_numbers:
                    # Record the FDLP row as of interest.
                    self.fdlp_rows_of_interest[fdlp_row_number] = row
                    rows_nums = self.scu_weeding_set.sudoc_number_to_row_nums[
                        simplified_sudoc_number
                    ].split(",")
                    for row_num in rows_nums:
                        self.scu_sudoc_row_nums_for_matches.add(int(row_num))

    def separate_rows(self) -> None:
        """Separate the matched SCU rows from the unmatched.

        This function should be run after read_from_file() has been used to read in
        information from one or more FDLP reference files.
        """
        # Split the rows that need removing from the ones that don't.
        for scu_row_num, row in self.scu_weeding_set.sudoc_row_num_to_row.items():
            if scu_row_num in self.scu_sudoc_row_nums_for_matches:
                self.scu_rows_matched.append(row)
            else:
                self.scu_rows_not_matched.append(row)
