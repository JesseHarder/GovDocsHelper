"""Module containing code for reading information out of our input CSV files."""

from __future__ import annotations

from csv import reader as csv_reader
from csv import writer as csv_writer
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from gov_docs_helper.utils import simplify_sudoc_number
from gov_docs_helper.weeding_set import WeedingSet

# --------------------------------------------------------------------------------------
#                      FDLP Reference Document Data Representation
# --------------------------------------------------------------------------------------


@dataclass
class FDLPReferenceDoc:
    """A data representation for the information we want to track about FDLP docs.

    Attributes:
        file_path: the csv file from which to read.
        skip_rows: the number of rows to skip at the top of the file before reading
            for actual content. Typically, these are empty rows or a header row.
            Default = 1.
        sudoc_number_column_index: The index for the column that contains the sudoc
            numbers, where the first column in the file has index 0. Default = 2.
        classification_type: a string to match for the correct classification type.
            Any row with a different classification type will be ignored. If None,
            then all classification types will be accepted. Default = "SuDoc".
        classification_type_column_index: The index for the column that
            contains the classification_types, where the first column in the file
            has index 0. Default = 1.
        header_row_index: The index for the row that contains the column headers,
            where the first row in the file has index 0. If None, then we assume no
            header row. Default = 0.
    """

    file_path: Path
    skip_rows: int
    sudoc_number_column_index: int
    classification_type: Optional[str]
    classification_type_column_index: int
    header_row_index: Optional[int]


class _SearcherReferenceDoc:
    """And extension of the FDLPReferenceDoc.

    We use this class to track information about each reference doc as we search it.
    These additional fields do not need to be exposed outside of this module and the
    user does not need to know about them in order to provide the needed information
    in the form of the public FDLPReferenceDoc class.
    """

    def __init__(self, reference_doc: FDLPReferenceDoc) -> None:
        """Initialize a _SearcherReferenceDoc.

        Args:
            reference_doc: An FDLPReferenceDoc that we are extending.
        """
        self._fdlp_reference_doc: FDLPReferenceDoc = reference_doc

        self.file_num: int
        self.headers: Optional[List[str]] = None
        self.rows_of_interest: Dict[int, List[str]] = {}

    @property
    def file_path(self) -> Path:
        return self._fdlp_reference_doc.file_path

    @property
    def skip_rows(self) -> int:
        return self._fdlp_reference_doc.skip_rows

    @property
    def sudoc_number_column_index(self) -> int:
        return self._fdlp_reference_doc.sudoc_number_column_index

    @property
    def classification_type(self) -> Optional[str]:
        return self._fdlp_reference_doc.classification_type

    @property
    def classification_type_column_index(self) -> int:
        return self._fdlp_reference_doc.classification_type_column_index

    @property
    def header_row_index(self) -> Optional[int]:
        return self._fdlp_reference_doc.header_row_index


class FDLPSearcher:
    """Class to read through an FDLP file and extract the needed information."""

    def __init__(self, scu_weeding_set: WeedingSet) -> None:
        """Initialize an FDLPReader.

        Args:
            scu_weeding_set: the WeedingSet instance that the FDLPSearcher will compare
                against when it scans through the FLDP file(s).
        """
        # The SCUWeedingSet off which on which to match.
        self.weeding_set: WeedingSet = scu_weeding_set

        self.reference_docs: List[_SearcherReferenceDoc] = []
        self.scu_sudoc_row_nums_for_matches: Set[int] = set()
        self.scu_rows_not_matched: List[List[str]] = []
        self.scu_rows_matched: List[List[str]] = []

    @property
    def num_docs(self) -> int:
        """Get the number of reference documents that we currently have."""
        return len(self.reference_docs)

    # ----------------------------------------------------------------------------------
    #                                  Searching Steps
    # ----------------------------------------------------------------------------------

    def _reset(self) -> None:
        """Empty the contents of this SCUWeedingSet."""
        self.reference_docs = []
        self.scu_sudoc_row_nums_for_matches = set()
        self.scu_rows_not_matched = []
        self.scu_rows_matched = []

    def _read_from_file(self, fdlp_reference_doc: FDLPReferenceDoc) -> None:
        """Read through an FDLP reference file and find matching information.

        Args:
            fdlp_reference_doc: an FDLPReferenceDoc instance.
        Returns:
            None
        """
        reference_doc = _SearcherReferenceDoc(fdlp_reference_doc)
        # Create a new reference document and add it to our collection of them.
        self.reference_docs.append(reference_doc)

        with reference_doc.file_path.open("r") as file_pointer:
            reader = csv_reader(file_pointer)
            # Iterate over the rest, looking for matches.
            for fdlp_row_index, row in enumerate(reader):
                # If we have a header row and have reached it, save it in our
                # reference doc.
                if (
                    reference_doc.header_row_index is not None
                    and fdlp_row_index == reference_doc.header_row_index
                ):
                    reference_doc.headers = row
                    continue
                # If we're within the rows that need to be skipped, we'll skip it.
                if fdlp_row_index < reference_doc.skip_rows:
                    continue
                # Skip the row if it has an invalid classification type:
                if reference_doc.classification_type:
                    if (
                        row[reference_doc.classification_type_column_index]
                        != reference_doc.classification_type
                    ):
                        continue
                # Get the sudoc number from the specified column
                fdlp_sudoc_number: str = row[reference_doc.sudoc_number_column_index]
                simplified_sudoc_number = simplify_sudoc_number(fdlp_sudoc_number)
                if simplified_sudoc_number in self.weeding_set.sudoc_numbers:
                    # Record the FDLP row as of interest.
                    reference_doc.rows_of_interest[fdlp_row_index] = row
                    rows_nums = self.weeding_set.sudoc_number_to_row_nums[
                        simplified_sudoc_number
                    ].split(",")
                    for row_num in rows_nums:
                        self.scu_sudoc_row_nums_for_matches.add(int(row_num))

    def _separate_rows(self) -> None:
        """Separate the matched SCU rows from the unmatched.

        This function should be run after read_from_file() has been used to read in
        information from one or more FDLP reference files.
        """
        # Split the rows that need removing from the ones that don't.
        for scu_row_num, row in self.weeding_set.sudoc_row_num_to_row.items():
            if scu_row_num in self.scu_sudoc_row_nums_for_matches:
                self.scu_rows_matched.append(row)
            else:
                self.scu_rows_not_matched.append(row)

    # ----------------------------------------------------------------------------------
    #                         Single-Function Search Interface
    # ----------------------------------------------------------------------------------

    def search_fdlp_references(
        self, fdlp_reference_docs: Iterable[FDLPReferenceDoc]
    ) -> None:
        """Search the given FDLP Reference documents for matches in our weeding set.

        Args:
            fdlp_reference_docs: An iterable collection of FDLPReferenceDocument
                instances.

        Return:
            None. The search collects the data inside of this class so that it can
                then be written out to file using write_matches_to_file.
        """
        # Reset this class so that it can start a fresh search.
        self._reset()
        # Read in the FDLp reference information from each document.
        for reference_doc in fdlp_reference_docs:
            self._read_from_file(reference_doc)
        # Then separate out the results into matches and non-matches.
        self._separate_rows()

    # ----------------------------------------------------------------------------------
    #                             Results Writing Functions
    # ----------------------------------------------------------------------------------

    def write_matches_to_file(self, output_dir: Path) -> None:
        """Write out FDLP file rows with matches in the weeding set.

        This function writes out copies of the FDLP reference documents containing only
        those rows for which matches were found in the weeding set. Each output
        document will have the same filename as the original document in which the
        matching row was found, with "matched_" appened to the front of the name.
        Further, two additional columns will be added to the end of each row. The
        first will contain the number of the row in the original FDLP document. The
        second will contain one or row numbers for the row or rows in the weeding set
        that matched to that FDLP reference document row.

        Args:
            output_dir: a Path to the directory into which to write the files.
        """
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
                    self.weeding_set.sudoc_number_to_row_nums[sudoc_num],
                ]
                out_row = doc_row + added_columns
                rows.append(out_row)

            # Write to file.
            output_file = output_dir / f"matched_{reference_doc.file_path.name}"
            with output_file.open("w") as file_pointer:
                writer = csv_writer(file_pointer)
                writer.writerows(rows)
