from langchain.tools import BaseTool
import os

class MarkdownReaderTool(BaseTool):
    name = "markdown_reader"
    description = "A tool for reading markdown files"

    def _run(self, file_path: str) -> str:
        """Read content from a markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            return f"Error reading markdown file: {str(e)}"

    def _arun(self, file_path: str) -> str:
        """Async implementation of run - just calls run since this is a simple operation."""
        return self._run(file_path)
