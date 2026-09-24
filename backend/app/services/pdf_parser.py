"""
PDF parser service.

Extracts text content from uploaded PDF files.
"""


class PDFParser:
    """Extracts structured text from PDF documents."""

    @staticmethod
    async def extract_text(file_bytes: bytes) -> str:
        """
        Parse a PDF file and return its full text content.

        TODO: Implement using PyMuPDF (fitz) or pdfplumber.
        """
        raise NotImplementedError("PDF parsing not yet implemented.")

    @staticmethod
    async def extract_pages(file_bytes: bytes) -> list[str]:
        """
        Parse a PDF file and return text content per page.

        TODO: Implement page-level extraction.
        """
        raise NotImplementedError("PDF page extraction not yet implemented.")
