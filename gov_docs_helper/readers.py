"""Module containing code for reading information out of our input CSV files."""

from csv import reader as csv_reader
from csv import writer as csv_writer
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from gov_docs_helper.utils import simplify_sudoc_number
from gov_docs_helper.weeding_set import WeedingSet


@dataclass
class FDLPReferenceDoc:
    """A data representation for the information we want to track about FDLP docs."""

    file_path: Path
    file_num: int
    skip_rows: int
    sudoc_number_column_index: int
    classification_type: Optional[str]
    classification_type_column_index: int
    headers: Optional[List[str]] = None
    rows_of_interest: Dict[int, List[str]] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.file_path)


class FDLPReader:
    """Class to read through an FDLP file and extract the needed information."""

    def __init__(self, scu_weeding_set: WeedingSet):
        """Initialize an FDLPReader.

        Args:
            scu_weeding_set: an SCUWeedingSet instance.
        """
        # The SCUWeedingSet off which on which to match.
        self.scu_weeding_set: WeedingSet = scu_weeding_set

        self.reference_docs: List[FDLPReferenceDoc] = []
        self.scu_sudoc_row_nums_for_matches: Set[int] = set()
        self.scu_rows_not_matched: List[List[str]] = []
        self.scu_rows_matched: List[List[str]] = []

    def reset(self) -> None:
        """Empty the contents of this SCUWeedingSet."""
        self.reference_docs = []
        self.scu_sudoc_row_nums_for_matches = set()
        self.scu_rows_not_matched = []
        self.scu_rows_matched = []

    @property
    def num_docs(self) -> int:
        """Get the number of reference documents that we currently have."""
        return len(self.reference_docs)

    def read_from_file(
        self,
        fdlp_reference_set_file: Path,
        skip_rows: int = 1,
        sudoc_number_column_index: int = 2,
        classification_type: Optional[str] = "SuDoc",
        classification_type_column_index: int = 1,
        header_row_index: Optional[int] = 0,
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
            header_row_index: The index for the row that contains the column headers,
                where the first row in the file has index 0. If None, then we assume no
                header row. Default = 0.
        Returns:
            None
        """
        # Create a new reference document and add it to our collection of them.
        reference_doc = FDLPReferenceDoc(
            file_path=fdlp_reference_set_file,
            file_num=self.num_docs,
            skip_rows=skip_rows,
            sudoc_number_column_index=sudoc_number_column_index,
            classification_type=classification_type,
            classification_type_column_index=classification_type_column_index,
        )
        self.reference_docs.append(reference_doc)

        with fdlp_reference_set_file.open("r") as file_pointer:
            reader = csv_reader(file_pointer)
            # Iterate over the rest, looking for matches.
            for fdlp_row_index, row in enumerate(reader):
                # If we have a header row and have reached it, save it in our
                # reference doc.
                if header_row_index is not None and fdlp_row_index == header_row_index:
                    reference_doc.headers = row
                    continue
                # If we're within the rows that need to be skipped, we'll skip it.
                if fdlp_row_index < skip_rows:
                    continue
                # Skip the row if it has an invalid classification type:
                if classification_type:
                    if row[classification_type_column_index] != classification_type:
                        continue
                # Get the sudoc number from the specified column
                fdlp_sudoc_number: str = row[sudoc_number_column_index]
                simplified_sudoc_number = simplify_sudoc_number(fdlp_sudoc_number)
                if simplified_sudoc_number in self.scu_weeding_set.sudoc_numbers:
                    # Record the FDLP row as of interest.
                    reference_doc.rows_of_interest[fdlp_row_index] = row
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

    def write_matches_to_file(self, output_dir: Path) -> None:
        # Create the directory into which to write the output.
        output_dir.mkdir(parents=True, exist_ok=True)
        # Create the results that we want to write out.
        for doc_index, reference_doc in enumerate(self.reference_docs):
            rows: List[List[Any]] = []
            # If this document has headers, then add them first.
            if reference_doc.headers:
                rows.append(reference_doc.headers + ["FDLP Row", "SCU Row(s)"])
            # Now add the rest of the rows.
            for row_number, doc_row in reference_doc.rows_of_interest.items():
                sudoc_num = simplify_sudoc_number(
                    doc_row[reference_doc.sudoc_number_column_index]
                )
                added_columns = [
                    row_number,
                    self.scu_weeding_set.sudoc_number_to_row_nums[sudoc_num],
                ]
                out_row = doc_row + added_columns
                rows.append(out_row)

            # Write to file.
            output_file = output_dir / f"matched_{reference_doc.file_path.name}"
            with output_file.open("w") as file_pointer:
                writer = csv_writer(file_pointer)
                writer.writerows(rows)
