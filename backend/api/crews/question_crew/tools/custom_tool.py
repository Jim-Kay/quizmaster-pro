from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import PyPDF2
import os

# Define a custom tool for reading text from a PDF file
class PDFReaderInput(BaseModel):
    """Input schema for PDFReaderTool."""
    file_path: str = Field(..., description="The absolute or relative path to the PDF file to read.")

# Define the PDFReaderTool class
class PDFReaderTool(BaseTool):
    """
    Tool for reading and extracting text from PDF documents.
    """
    name: str = "PDF Reader"
    description: str = (
        "Use this tool to read and extract content from a PDF file. "
        "Provide the file path as input, and the tool will return the extracted text."
    )
    args_schema: Type[BaseModel] = PDFReaderInput

    def _run(self, file_path: str) -> str:
        """
        Reads and extracts text from the provided PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            str: Extracted text from the PDF file.
        """
        try:
            # Open the PDF file
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                # Extract all text from the PDF
                extracted_text = ''
                for page in reader.pages:
                    extracted_text += page.extract_text()
            return extracted_text
        except Exception as e:
            return f"An error occurred while reading the PDF file: {e}"

