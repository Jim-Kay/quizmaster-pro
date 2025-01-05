from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Define a custom tool for reading text from a Markdown file
class MarkdownReaderInput(BaseModel):
    """Input schema for MarkdownReaderTool."""
    file_path: str = Field(..., description="The absolute or relative path to the Markdown file to read.")

# Define the MarkdownReaderTool class
class MarkdownReaderTool(BaseTool):
    """ 
    Tool for reading and extracting text from Markdown documents.
    """ 
    name: str = "Markdown Reader"
    description: str = (    
        "Use this tool to read and extract content from a Markdown file. "
        "Provide the file path as input, and the tool will return the extracted text."
    )
    args_schema: Type[BaseModel] = MarkdownReaderInput

    def _run(self, file_path: str) -> str:
        """
        Reads and extracts text from the provided Markdown file.

        Args:
            file_path (str): Path to the Markdown file. 

        Returns:    
            str: Extracted text from the Markdown file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            return f"An error occurred while reading the Markdown file: {e}"
