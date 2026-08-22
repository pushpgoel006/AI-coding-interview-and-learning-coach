"""Focused tests for the upload-to-indexing backend boundary."""

import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.documents import Document

from rag.indexer import index_documents


class IndexDocumentsTests(unittest.TestCase):
    def test_combines_chunks_from_each_uploaded_file(self):
        first_path = Path("resume.pdf")
        second_path = Path("job-description.pdf")
        first_document = Document(page_content="Python", metadata={})
        second_document = Document(page_content="AWS", metadata={})
        chunks = [
            Document(page_content="Python", metadata={}),
            Document(page_content="AWS", metadata={}),
        ]

        with (
            patch("rag.indexer.Path.is_file", return_value=True),
            patch("rag.indexer.load_pdf", side_effect=[[first_document], [second_document]]),
            patch("rag.indexer.split_documents", side_effect=[[chunks[0]], [chunks[1]]]),
            patch("rag.indexer.clear_index") as clear_index,
            patch("rag.indexer.create_vector_store") as create_vector_store,
        ):
            chunk_count = index_documents([first_path, second_path])

        self.assertEqual(chunk_count, 2)
        clear_index.assert_called_once_with()
        self.assertEqual(create_vector_store.call_args.args[0], chunks)

    def test_raises_a_clear_error_when_no_chunks_are_created(self):
        with (
            patch("rag.indexer.Path.is_file", return_value=True),
            patch("rag.indexer.load_pdf", return_value=[]),
            patch("rag.indexer.split_documents", return_value=[]),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "No text could be extracted from the uploaded documents.",
            ):
                index_documents(["empty.pdf"])


if __name__ == "__main__":
    unittest.main()
